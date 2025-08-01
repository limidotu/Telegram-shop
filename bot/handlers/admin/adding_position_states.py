from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.utils.exceptions import ChatNotFound

from bot.database.methods import check_role, check_category, check_item, create_item, add_values_to_item, \
    update_item, delete_item, check_value, delete_only_items
from bot.database.models import Permission
from bot.handlers.other import get_bot_user_ids
from bot.keyboards import goods_management, back, item_management, question_buttons, goods_adding
from bot.logger_mesh import logger
from bot.misc import TgConfig


async def add_item_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[f'{user_id}_message_id'] = call.message.message_id
    TgConfig.STATE[user_id] = 'create_item_name'
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('Введите название позиции',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=back("item-management"))
        return
    await call.answer('Недостаточно прав')


async def check_item_name_for_add(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    item_name = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    item = check_item(item_name)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    if item:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='❌ Позиция не может быть создана (Такая позиция уже существует)',
                                    reply_markup=back('item-management'))
        return
    TgConfig.STATE[user_id] = 'create_item_description'
    TgConfig.STATE[f'{user_id}_name'] = message.text
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Введите описание для позиции:',
                                reply_markup=back('item-management'))


async def add_item_description(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    TgConfig.STATE[f'{user_id}_description'] = message.text
    TgConfig.STATE[user_id] = 'create_item_price'
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Введите цену для позиции:',
                                reply_markup=back('item-management'))


async def add_item_price(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    if not message.text.isdigit():
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='⚠️ некорректное значение цены.',
                                    reply_markup=back('item-management'))
        return
    TgConfig.STATE[user_id] = 'check_item_category'
    TgConfig.STATE[f'{user_id}_price'] = message.text
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Введите категорию, к которой будет относится позиция:',
                                reply_markup=back('item-management'))


async def check_category_for_add_item(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    category_name = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    category = check_category(category_name)
    if not category:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='❌ Позиция не может быть создана (Категория для привязки введена неверно)',
                                    reply_markup=back('item-management'))
        return
    TgConfig.STATE[user_id] = None
    TgConfig.STATE[f'{user_id}_category'] = category_name
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='У этой позиции будут бесконечные товары? '
                                     '(всем будет высылаться одна копия товара)',
                                reply_markup=question_buttons('infinity', 'item-management'))


async def adding_value_to_position(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    answer = call.data.split('_')[1]
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    TgConfig.STATE[f'{user_id}_answer'] = answer
    TgConfig.STATE[f'{user_id}_message'] = message_id

    if answer == 'no':
        TgConfig.STATE[user_id] = 'add_item_values'
        TgConfig.STATE[f'{user_id}_values'] = []
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=message_id,
            text=(
                'Введите товары для позиции по одному сообщению.\n'
                'Когда закончите ввод — нажмите «Добавить указанные товары». (появится после первого добавленного товара)'
            ),
            reply_markup=back("item-management")
        )
    else:
        TgConfig.STATE[user_id] = 'finish_adding_item'
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=message_id,
            text='Введите товар для позиции:',
            reply_markup=back('item-management')
        )


async def collect_item_value(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    values = TgConfig.STATE.setdefault(f'{user_id}_values', [])
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    values.append(message.text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text=f'✅ Товар «{message.text}» добавлен в список ({len(values)} шт.)',
        reply_markup=goods_adding("finish_adding_items", "item-management")
    )



async def finish_adding_items_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    item_name = TgConfig.STATE.get(f'{user_id}_name')
    item_description = TgConfig.STATE.get(f'{user_id}_description')
    item_price = TgConfig.STATE.get(f'{user_id}_price')
    category_name = TgConfig.STATE.get(f'{user_id}_category')
    values = TgConfig.STATE.pop(f'{user_id}_values', [])
    TgConfig.STATE[user_id] = None

    create_item(item_name, item_description, item_price, category_name)

    for val in values:
        add_values_to_item(item_name, val, False)

    group_id = TgConfig.GROUP_ID if TgConfig.GROUP_ID != -988765433 else None
    if group_id:
        try:
            await bot.send_message(
                chat_id=group_id,
                text=(
                    f'🎁 Залив\n'
                    f'🏷️ Товар: <b>{item_name}</b>\n'
                    f'📦 Количество: <b>{len(values)}</b>'
                ),
                parse_mode='HTML'
            )
        except ChatNotFound:
            pass

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=message_id,
        text='✅ Позиция создана, товары добавлены',
        reply_markup=back('item-management')
    )
    admin_info = await bot.get_chat(user_id)
    logger.info(f"Пользователь {user_id} ({admin_info.first_name}) "
                f'создал новую позицию "{item_name}"')


async def finish_adding_item_callback_handler(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    item_name = TgConfig.STATE.get(f'{user_id}_name')
    item_description = TgConfig.STATE.get(f'{user_id}_description')
    item_price = TgConfig.STATE.get(f'{user_id}_price')
    category_name = TgConfig.STATE.get(f'{user_id}_category')
    value = message.text
    TgConfig.STATE[user_id] = None

    create_item(item_name, item_description, item_price, category_name)
    add_values_to_item(item_name, value, True)

    group_id = TgConfig.GROUP_ID if TgConfig.GROUP_ID != -988765433 else None
    if group_id:
        try:
            await bot.send_message(
                chat_id=group_id,
                text=(
                    f'🎁 Залив\n'
                    f'🏷️ Товар: <b>{item_name}</b>\n'
                    f'📦 Количество: <b>Информация в группе</b>'
                ),
                parse_mode='HTML'
            )
        except ChatNotFound:
            pass

    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text='✅ Позиция создана, товар добавлен',
        reply_markup=back('item-management')
    )
    admin_info = await bot.get_chat(user_id)
    logger.info(f"Пользователь {user_id} ({admin_info.first_name}) "
                f'создал новую позицию "{item_name}"')


def register_add_management(dp: Dispatcher) -> None:
    dp.register_callback_query_handler(add_item_callback_handler,
                                       lambda c: c.data == 'add_item')
    dp.register_callback_query_handler(finish_adding_items_callback_handler,
                                       lambda c: c.data == 'finish_adding_items')

    dp.register_message_handler(finish_adding_item_callback_handler,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'finish_adding_item')
    dp.register_message_handler(check_item_name_for_add,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'create_item_name')
    dp.register_message_handler(add_item_description,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'create_item_description')
    dp.register_message_handler(add_item_price,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'create_item_price')
    dp.register_message_handler(check_category_for_add_item,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'check_item_category')
    dp.register_message_handler(collect_item_value,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'add_item_values')

    dp.register_callback_query_handler(adding_value_to_position,
                                       lambda c: c.data.startswith('infinity_'))