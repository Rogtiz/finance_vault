from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from ..bot import dp
from ..services import token_storage, api_client

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply(
        "Hello! 👋\n"
        "<b>Cards:</b>\n"
        "  /login - Log in (username password)\n"
        "  /list - List masked cards\n"
        "  /add - Add a new card\n"
        "<b>Subscriptions:</b>\n"
        "  /list_subs - List subscriptions\n"
        "  /add_sub - Add a subscription\n"
        "  /del_sub [ID] - Delete a subscription (e.g., /del_sub 5)\n"
        "<b>General:</b>\n"
        "  /logout - Log out\n"
        "  /cancel - Cancel current operation"
    )

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