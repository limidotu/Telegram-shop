from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from bot.database.methods import get_all_categories, get_all_items, select_bought_items, get_bought_item_info, get_item_info, \
    select_item_values_amount, bought_items_list, check_value
from bot.handlers.other import get_bot_user_ids
from bot.keyboards import categories_list, goods_list, user_items_list, back, item_info
from bot.misc import TgConfig


async def shop_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    categories = get_all_categories()
    max_index = len(categories) // 10
    if len(categories) % 10 == 0:
        max_index -= 1
    markup = categories_list(categories, 0, max_index)
    await bot.edit_message_text('🏪 Категории магазина',
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                reply_markup=markup)


async def navigate_categories(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    categories = get_all_categories()
    current_index = int(call.data.split('_')[1])
    max_index = len(categories) // 10
    if len(categories) % 10 == 0:
        max_index -= 1
    if 0 <= current_index <= max_index:
        markup = categories_list(categories, current_index, max_index)
        await bot.edit_message_text(message_id=call.message.message_id,
                                    chat_id=call.message.chat.id,
                                    text='🏪 Категории магазина',
                                    reply_markup=markup)
    else:
        await bot.answer_callback_query(callback_query_id=call.id,
                                        text="❌ Такой страницы нет")


async def items_list_callback_handler(call: CallbackQuery):
    category_name = call.data[9:]
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    goods = get_all_items(category_name)
    max_index = len(goods) // 10
    if len(goods) % 10 == 0:
        max_index -= 1
    markup = goods_list(goods, category_name, 0, max_index)
    await bot.edit_message_text('🏪 выберите нужный товар', chat_id=call.message.chat.id,
                                message_id=call.message.message_id, reply_markup=markup)


async def navigate_goods(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    category_name = call.data.split('_')[1]
    current_index = int(call.data.split('_')[2])
    goods = get_all_items(category_name)
    max_index = len(goods) // 10
    if len(goods) % 10 == 0:
        max_index -= 1
    if 0 <= current_index <= max_index:
        markup = goods_list(goods, category_name, current_index, max_index)
        await bot.edit_message_text(message_id=call.message.message_id,
                                    chat_id=call.message.chat.id,
                                    text='🏪 выберите нужный товар',
                                    reply_markup=markup)
    else:
        await bot.answer_callback_query(callback_query_id=call.id, text="❌ Такой страницы нет")


async def item_info_callback_handler(call: CallbackQuery):
    item_name = call.data[5:]
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    item_info_list = get_item_info(item_name)
    category = item_info_list['category_name']
    quantity = 'Количество - информация в группе'
    if not check_value(item_name):
        quantity = f'Количество - {select_item_values_amount(item_name)}шт.'
    markup = item_info(item_name, category)
    await bot.edit_message_text(
        f'{item_name}\n'
        f'{item_info_list["description"]}\n'
        f'{quantity}',
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)


async def navigate_bought_items(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    goods = bought_items_list(user_id)
    bought_goods = select_bought_items(user_id)
    current_index = int(call.data.split('_')[1])
    data = call.data.split('_')[2]
    max_index = len(goods) // 10
    if len(goods) % 10 == 0:
        max_index -= 1
    if 0 <= current_index <= max_index:
        if data == 'user':
            back_data = 'profile'
            pre_back = 'bought_items'
        else:
            back_data = f'check-user_{data}'
            pre_back = f'user-items_{data}'
        markup = user_items_list(bought_goods, data, back_data, pre_back, current_index, max_index)
        await bot.edit_message_text(message_id=call.message.message_id,
                                    chat_id=call.message.chat.id,
                                    text='Ваши товары:',
                                    reply_markup=markup)
    else:
        await bot.answer_callback_query(callback_query_id=call.id, text="❌ Такой страницы нет")


async def bought_items_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    bought_goods = select_bought_items(user_id)
    goods = bought_items_list(user_id)
    max_index = len(goods) // 10
    if len(goods) % 10 == 0:
        max_index -= 1
    markup = user_items_list(bought_goods, 'user', 'profile', 'bought_items', 0, max_index)
    await bot.edit_message_text('Ваши товары:', chat_id=call.message.chat.id,
                                message_id=call.message.message_id, reply_markup=markup)


async def bought_item_info_callback_handler(call: CallbackQuery):
    item_id = call.data.split(":")[1]
    back_data = call.data.split(":")[2]
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    item = get_bought_item_info(item_id)
    
    
    await bot.edit_message_text(
        f'<b>Товар</b>: <code>{item["item_name"]}</code>\n'
        f'<b>Цена</b>: <code>{item["price"]}</code>\n'
        f'<b>Дата покупки</b>: <code>{item["bought_datetime"]}</code>\n'
        f'<b>Уникальный ID</b>: <code>{item["unique_id"]}</code>\n'
        f'<b>Значение</b>:\n<code>{item["value"]}</code>',
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=back(back_data))


def register_shop_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(shop_callback_handler,
                                       lambda c: c.data == 'shop')
    dp.register_callback_query_handler(bought_items_callback_handler,
                                       lambda c: c.data == 'bought_items')

    dp.register_callback_query_handler(navigate_categories,
                                       lambda c: c.data.startswith('categories-page_'))
    dp.register_callback_query_handler(navigate_bought_items,
                                       lambda c: c.data.startswith('bought-goods-page_'))
    dp.register_callback_query_handler(navigate_goods,
                                       lambda c: c.data.startswith('goods-page_'))
    dp.register_callback_query_handler(bought_item_info_callback_handler,
                                       lambda c: c.data.startswith('bought-item:'))
    dp.register_callback_query_handler(items_list_callback_handler,
                                       lambda c: c.data.startswith('category_'))
    dp.register_callback_query_handler(item_info_callback_handler,
                                       lambda c: c.data.startswith('item_'))
