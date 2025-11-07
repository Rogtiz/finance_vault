# In-memory token store: map telegram_user_id -> jwt token
# TOKENS = {}

# def get_token(user_id: int) -> str | None:
#     return TOKENS.get(user_id)

# def set_token(user_id: int, token: str):
#     TOKENS[user_id] = token

# def del_token(user_id: int):
#     TOKENS.pop(user_id, None)
# In-memory token store: map telegram_user_id -> {'token': jwt, 'master_key': str}
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

async def check_auth(message):
    token = get_token(message.from_user.id)
    if not token:
        await message.reply('Not authenticated. Use /login')
        return None
    return token