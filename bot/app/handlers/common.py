from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from ..bot import dp
from ..services import token_storage, api_client
from ..keyboards import main_menu_keyboard # <-- ИМПОРТ

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply(
        "👋 Добро пожаловать в Карточное Хранилище!\n"
        "Пожалуйста, авторизуйтесь, чтобы начать.",
        reply_markup=main_menu_keyboard()
    )

@dp.message_handler(commands=['menu']) # Добавим команду для вызова меню
async def cmd_menu(message: types.Message):
    if not token_storage.get_token(message.from_user.id):
        await message.reply("Вы не авторизованы. Используйте /login.")
        return
    await message.reply("Главное меню:", reply_markup=main_menu_keyboard())

# --- Обработка инлайн-кнопок ---
@dp.callback_query_handler(lambda c: c.data == 'logout')
async def process_logout_callback(callback_query: types.CallbackQuery):
    token_storage.del_token(callback_query.from_user.id)
    await callback_query.answer(text="Вы вышли из системы.", show_alert=False)
    await callback_query.message.edit_text("Выход выполнен. Используйте /login для входа.")

# ... (остальные команды login, cancel, handle_credentials без изменений)

# @dp.message_handler(commands=['start'])
# async def cmd_start(message: types.Message):
#     await message.reply(
#         "Hello! 👋\n"
#         "<b>Cards:</b>\n"
#         "  /login - Log in (username password)\n"
#         "  /list - List masked cards\n"
#         "  /add - Add a new card\n"
#         "<b>Subscriptions:</b>\n"
#         "  /list_subs - List subscriptions\n"
#         "  /add_sub - Add a subscription\n"
#         "  /del_sub [ID] - Delete a subscription (e.g., /del_sub 5)\n"
#         "<b>General:</b>\n"
#         "  /logout - Log out\n"
#         "  /cancel - Cancel current operation"
#     )

@dp.message_handler(commands=['login'])
async def cmd_login(message: types.Message):
    await message.reply("Send username and password in one message separated by space, e.g.:\n<code>username mypass</code>")

@dp.message_handler(commands=['logout'])
async def cmd_logout(message: types.Message):
    token_storage.del_token(message.from_user.id)
    await message.reply('Logged out.')

@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply('Cancelled.')

# @dp.message_handler(lambda m: m.text and ' ' in m.text and not m.text.startswith('/'), state='*')
# async def handle_credentials(message: types.Message):
#     parts = message.text.strip().split(None, 1)
#     if len(parts) != 2: return
    
#     username, password = parts
#     status, data = await api_client.api_login(username, password)
    
#     if status == 200:
#         token_storage.set_token(message.from_user.id, data.get('access_token'))
#         await message.reply('Logged in successfully.')
@dp.message_handler(lambda m: m.text and ' ' in m.text and not m.text.startswith('/'), state='*')
async def handle_credentials(message: types.Message):
    parts = message.text.strip().split(None, 1)
    if len(parts) != 2: return
    
    username, password = parts
    status, data = await api_client.api_login(username, password)
    
    if status == 200:
        # Сохраняем и токен, и пароль (как мастер-ключ)
        token_storage.set_credentials(message.from_user.id, data.get('access_token'), password) 
        await message.reply('Logged in successfully.')
    # ...
    else:
        await message.reply(f'Login failed: {status} {data}')