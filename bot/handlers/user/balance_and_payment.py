import asyncio
import datetime

from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from bot.database.methods import get_all_categories
from bot.database.methods import get_item_info, get_item_value, buy_item, add_bought_item, \
    start_operation, \
    select_unfinished_operations, get_user_referral, finish_operation, update_balance, create_operation
from bot.handlers.other import get_bot_user_ids
from bot.keyboards import back, payment_menu, close
from bot.logger_mesh import logger
from bot.misc import TgConfig, EnvKeys
from bot.misc.payment import quick_pay, check_payment_status
from bot.keyboards import categories_list
ADMIN_CHAT_ID = EnvKeys.OWNER_ID

async def replenish_balance_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    message_id = call.message.message_id

    if EnvKeys.ACCESS_TOKEN and EnvKeys.ACCOUNT_NUMBER is not None:
        TgConfig.STATE[f'{user_id}_message_id'] = message_id
        TgConfig.STATE[user_id] = 'process_replenish_balance'
        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=message_id,
                                    text='💰 Введите сумму для пополнения:',
                                    reply_markup=back('profile'))
        return

    await call.answer('Пополнение не было настроено')


async def process_replenish_balance(message: Message):
    bot, user_id = await get_bot_user_ids(message)

    text = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    TgConfig.STATE[user_id] = None
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    if not text.isdigit() or int(text) < 20 or int(text) > 10000:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text="❌ Неверная сумма пополнения. "
                                         "Сумма пополнения должна быть числом не меньше 20₽ и не более 10 000₽",
                                    reply_markup=back('replenish_balance'))
        return

    label, url = quick_pay(message)
    start_operation(user_id, text, label)
    sleep = TgConfig.PAYMENT_TIME
    sleep_time = int(sleep)
    markup = payment_menu(url, label)
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text=f'💵 Сумма пополнения: {text}₽.\n'
                                     f'⌛️ У вас имеется {int(sleep_time / 60)} минут на оплату.\n'
                                     f'<b>❗️ После оплаты нажмите кнопку «Проверить оплату»</b>',
                                reply_markup=markup)
    await asyncio.sleep(sleep_time)
    info = select_unfinished_operations(label)
    if info:
        payment_status = await check_payment_status(label)

        if not payment_status == "success":
            finish_operation(label)


async def checking_payment(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    message_id = call.message.message_id
    label = call.data[6:]
    info = select_unfinished_operations(label)

    if info:
        operation_value = info[0]
        payment_status = await check_payment_status(label)

        if payment_status == "success":
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            referral_id = get_user_referral(user_id)
            finish_operation(label)

            if referral_id and TgConfig.REFERRAL_PERCENT != 0:
                referral_percent = TgConfig.REFERRAL_PERCENT
                referral_operation = round((referral_percent / 100) * operation_value)
                update_balance(referral_id, referral_operation)
                await bot.send_message(referral_id,
                                       f'✅ Вы получили {referral_operation}₽ '
                                       f'от вашего реферал {call.from_user.first_name}',
                                       reply_markup=close())

            create_operation(user_id, operation_value, formatted_time)
            update_balance(user_id, operation_value)
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=message_id,
                                        text=f'✅ Баланс пополнен на {operation_value}₽',
                                        reply_markup=back('profile'))
        else:
            await call.answer(text='❌ Оплата не прошла успешно')
    else:
        await call.answer(text='❌ Счет не найден')


async def buy_item_callback_handler(call: CallbackQuery):
    item_name = call.data[4:]
    bot, user_id = await get_bot_user_ids(call)
    msg = call.message.message_id
    item_info_list = get_item_info(item_name)
    item_price = item_info_list["price"]

    value_data = get_item_value(item_name)

async def buy_item_callback_handler(call: CallbackQuery):
    item_name = call.data[4:]
    bot, user_id = await get_bot_user_ids(call)
    msg = call.message.message_id
    item_info_list = get_item_info(item_name)
    item_price = item_info_list["price"]
    
    # Get category for the item
    item_category = item_info_list.get("category_name", "Неизвестная категория")
    
    value_data = get_item_value(item_name)

    if value_data:
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        buy_item(value_data['id'], value_data['is_infinity'])
        add_bought_item(value_data['item_name'], value_data['value'], item_price, user_id, formatted_time)
        
        # Send confirmation to buyer
        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=msg,
                                    text=f'✅ Ваш заказ получен.\n\n'
                                         f'📂 <b>Товар:</b> {item_category}\n'
                                         f'🛍️ <b>Количество:</b> {value_data["item_name"]}\n'
                                         f'💵 <b>Цена:</b> ${item_price}',
                                    parse_mode='HTML')
        
        # Get user info and send notification to admin
        user_info = await bot.get_chat(user_id)
        
        # Format username display
        username_text = f"@{user_info.username}" if user_info.username else "без username"
        
        # Send you a direct message about the purchase
        notification_text = (
            f"💰 <b>Новая покупка!</b>\n\n"
            f"👤 <b>Покупатель:</b> {user_info.first_name} ({username_text})\n"
            f"🆔 <b>ID:</b> {user_id}\n"
            f"📂 <b>Категория:</b> {item_category}\n"
            f"🛍️ <b>Товар:</b> {value_data['item_name']}\n"
            f"💵 <b>Цена:</b> ${item_price}\n"
            f"🕐 <b>Время:</b> {formatted_time}\n"
            f"📦 <b>Содержимое:</b> {value_data['value']}"
        )
        
        await bot.send_message(chat_id=ADMIN_CHAT_ID, 
                              text=notification_text, 
                              parse_mode='HTML')
        
        logger.info(f"Пользователь {user_id} ({user_info.first_name})"
                    f" купил 1 товар позиции {value_data['item_name']} за {item_price}₽")
        return

    return


def register_balance_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(replenish_balance_callback_handler,
                                       lambda c: c.data == 'replenish_balance')

    dp.register_message_handler(process_replenish_balance,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'process_replenish_balance')

    dp.register_callback_query_handler(checking_payment,
                                       lambda c: c.data.startswith('check_'))
    dp.register_callback_query_handler(buy_item_callback_handler,
                                       lambda c: c.data.startswith('buy_'))
