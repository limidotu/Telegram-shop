import datetime
from urllib.parse import urlparse

from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery, ChatType
from aiogram.utils.exceptions import ChatNotFound

from bot.database.methods import select_max_role_id, create_user, check_role, check_user, select_user_operations, \
    select_user_items, check_user_referrals
from bot.handlers.other import get_bot_user_ids, check_sub_channel, get_bot_info
from bot.handlers.user.balance_and_payment import register_balance_handlers
from bot.handlers.user.shop_and_goods import register_shop_handlers
from bot.keyboards import check_sub, main_menu, rules, profile, back
from bot.misc import TgConfig, EnvKeys


async def start(message: Message):
    bot, user_id = await get_bot_user_ids(message)

    if message.chat.type != ChatType.PRIVATE:
        return

    TgConfig.STATE[user_id] = None

    owner = select_max_role_id()
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    referral_id = message.text[7:] if message.text[7:] != str(user_id) else None
    user_role = owner if str(user_id) == EnvKeys.OWNER_ID else 1
    create_user(telegram_id=user_id, registration_date=formatted_time, referral_id=referral_id, role=user_role)
    chat = TgConfig.CHANNEL_URL[13:]
    role_data = check_role(user_id)

    try:
        if chat is not None:
            chat_member = await bot.get_chat_member(chat_id=f'@{chat}', user_id=user_id)
            if not await check_sub_channel(chat_member):
                markup = check_sub(chat)
                await bot.send_message(user_id,
                                       'Для начала подпишитесь на новостной канал',
                                       reply_markup=markup)
                await bot.delete_message(chat_id=message.chat.id,
                                         message_id=message.message_id)
                return

    except ChatNotFound:
        pass

    markup = main_menu(role_data, chat, TgConfig.HELPER_URL)
    await bot.send_message(user_id,
                           '🧬 Добро пожаловать в DNA shop Calgary!',
                           reply_markup=markup)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


async def back_to_menu_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    user = check_user(call.from_user.id)
    markup = main_menu(user.role_id, TgConfig.CHANNEL_URL, TgConfig.HELPER_URL)
    await bot.edit_message_text('🧬 Добро пожаловать в DNA shop Calgary!',
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                reply_markup=markup)


async def rules_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    rules_data = TgConfig.RULES

    if rules_data:
        await bot.edit_message_text(rules_data, chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=rules())
        return

    await call.answer(text='❌ Правила не были добавлены')


async def profile_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    user = call.from_user
    TgConfig.STATE[user_id] = None
    user_info = check_user(user_id)
    balance = user_info.balance
    operations = select_user_operations(user_id)
    overall_balance = 0

    if operations:

        for i in operations:
            overall_balance += i

    items = select_user_items(user_id)
    referral = TgConfig.REFERRAL_PERCENT
    markup = profile(referral, items)
    await bot.edit_message_text(text=f"👤 <b>Профиль</b> — {user.first_name}\n🆔"
                                     f" <b>ID</b> — <code>{user_id}</code>\n"
                                     f"💳 <b>Баланс</b> — <code>{balance}</code> ₽\n"
                                     f"💵 <b>Всего пополнено</b> — <code>{overall_balance}</code> ₽\n"
                                     f" 🎁 <b>Куплено товаров</b> — {items} шт",
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id, reply_markup=markup,
                                parse_mode='HTML')


async def referral_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    referrals = check_user_referrals(user_id)
    referral_percent = TgConfig.REFERRAL_PERCENT
    await bot.edit_message_text(f'💚 Реферальная система\n'
                                f'🔗 Ссылка: https://t.me/{await get_bot_info(call)}?start={user_id}\n'
                                f'Количество рефералов: {referrals}\n'
                                f'📔 Реферальная система позволит Вам заработать деньги без всяких вложений. '
                                f'Необходимо всего лишь распространять свою реферальную ссылку и Вы будете получать'
                                f' {referral_percent}% от суммы пополнений Ваших рефералов на Ваш баланс бота.',
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                reply_markup=back('profile'))


async def check_sub_to_channel(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    chat = TgConfig.CHANNEL_URL
    parsed_url = urlparse(chat)
    channel_username = parsed_url.path.lstrip('/')
    helper = TgConfig.HELPER_URL
    chat_member = await bot.get_chat_member(chat_id='@' + channel_username, user_id=call.from_user.id)

    if await check_sub_channel(chat_member):
        user = check_user(call.from_user.id)
        role = user.role_id
        markup = main_menu(role, chat, helper)
        await bot.edit_message_text('🧬 Добро пожаловать в DNA shop Calgary!', chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=markup)
    else:
        await call.answer(text='Вы не подписались')


def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(start,
                                commands=['start'])
    dp.register_callback_query_handler(back_to_menu_callback_handler,
                                       lambda c: c.data == 'back_to_menu')
    dp.register_callback_query_handler(rules_callback_handler,
                                       lambda c: c.data == 'rules')
    dp.register_callback_query_handler(profile_callback_handler,
                                       lambda c: c.data == 'profile')
    dp.register_callback_query_handler(referral_callback_handler,
                                       lambda c: c.data == 'referral_system')
    dp.register_callback_query_handler(check_sub_to_channel,
                                       lambda c: c.data == 'sub_channel_done')

    register_shop_handlers(dp)
    register_balance_handlers(dp)
