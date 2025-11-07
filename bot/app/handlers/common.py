from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from ..bot import dp
from ..services import token_storage, api_client
from ..keyboards import main_menu_keyboard

@dp.message_handler(commands=['start', 'menu'])
async def cmd_start(message: types.Message):
    if token_storage.check_auth(message.from_user.id):
        await message.reply("Главное меню:", reply_markup=main_menu_keyboard())
    else:
        await message.reply(
            "👋 Добро пожаловать в Карточное Хранилище!\n"
            "Пожалуйста, авторизуйтесь, чтобы начать.",
            reply_markup=main_menu_keyboard()
        )

# --- Обработка инлайн-кнопок ---

@dp.callback_query_handler(lambda c: c.data == 'menu')
async def process_menu_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    if token_storage.check_auth(callback_query.from_user.id):
        await callback_query.message.edit_text("Главное меню:", reply_markup=main_menu_keyboard())
    else:
        await callback_query.message.edit_text("👋 Добро пожаловать!\nПожалуйста, авторизуйтесь, чтобы начать.", reply_markup=main_menu_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'logout')
async def process_logout_callback(callback_query: types.CallbackQuery):
    token_storage.del_token(callback_query.from_user.id)
    await callback_query.answer(text="Вы вышли из системы.", show_alert=False)
    await callback_query.message.edit_text("Выход выполнен. Используйте /login для входа.")

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
    await message.reply('Cancelled. Возврат в /menu')

@dp.message_handler(lambda m: m.text and ' ' in m.text and not m.text.startswith('/'), state='*')
async def handle_credentials(message: types.Message):
    parts = message.text.strip().split(None, 1)
    if len(parts) != 2: return
    
    username, password = parts
    status, data = await api_client.api_login(username, password)
    
    if status == 200:
        token_storage.set_credentials(message.from_user.id, data.get('access_token'), password) 
        await message.reply('Logged in successfully. Переход в /menu', reply_markup=main_menu_keyboard())
    else:
        await message.reply(f'Login failed: {status} {data}')