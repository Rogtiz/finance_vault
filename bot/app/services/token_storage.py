# In-memory token store: map telegram_user_id -> jwt token
# TOKENS = {}

# def get_token(user_id: int) -> str | None:
#     return TOKENS.get(user_id)

# def set_token(user_id: int, token: str):
#     TOKENS[user_id] = token

# def del_token(user_id: int):
#     TOKENS.pop(user_id, None)
# In-memory token store: map telegram_user_id -> {'token': jwt, 'master_key': str}
from aiogram import types

TOKENS = {}

def get_token(user_id: int) -> str | None:
    return TOKENS.get(user_id, {}).get('token')

def get_master_key(user_id: int) -> str | None:
    return TOKENS.get(user_id, {}).get('master_key') 

def set_credentials(user_id: int, token: str, master_key: str):
    TOKENS[user_id] = {'token': token, 'master_key': master_key} # <-- Сохраняем оба значения

def del_token(user_id: int):
    TOKENS.pop(user_id, None)
# ...

# /bot/app/services/token_storage.py

# ... (функции get_token, get_master_key, set_credentials, del_token) ...

async def check_auth(target: types.Message | types.CallbackQuery):
    # ПРАВИЛЬНОЕ ИЗВЛЕЧЕНИЕ ID ПОЛЬЗОВАТЕЛЯ ИЗ ЛЮБОГО ТИПА ОБЪЕКТА
    if isinstance(target, types.CallbackQuery):
        user_id = target.from_user.id
        message = target.message
    else:
        user_id = target.from_user.id
        message = target
        
    token = get_token(user_id)
    
    if not token:
        # Используем reply для обычных команд и edit_text для callback'ов
        if isinstance(target, types.CallbackQuery):
            await target.answer(text="Авторизация истекла.", show_alert=True)
            await message.edit_text("❌ Не авторизован. Используйте /login.")
        else:
            await message.reply('Not authenticated. Use /login')
        return None
        
    return token