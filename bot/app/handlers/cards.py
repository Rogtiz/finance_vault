import json
import base64
import os
from aiogram import types
from aiogram.dispatcher import FSMContext

# --- КРИПТОГРАФИЧЕСКИЕ ЗАВИСИМОСТИ ---
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

# Константы
KDF_ITERS = 200_000
NONCE_LEN = 12
SHARED_SALT = b'client_unified_vault_salt' # <--- ЕДИНАЯ ОБЩАЯ СОЛЬ!

# Функции, скопированные из cards_client.py
def derive_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SHARED_SALT,
        iterations=KDF_ITERS,
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))

def encrypt_payload(key: bytes, payload: dict):
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_LEN)
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    ct = aesgcm.encrypt(nonce, data, None)
    return nonce, ct

def decrypt_payload(key: bytes, nonce: bytes, ct: bytes):
    aesgcm = AESGCM(key)
    data = aesgcm.decrypt(nonce, ct, None)
    return json.loads(data.decode('utf-8'))
# --- КОНЕЦ КРИПТОГРАФИИ ---

from ..bot import dp
from ..states import AddCardStates
from ..services import token_storage, api_client
# ...

# @dp.message_handler(commands=['list'])
# async def cmd_list(message: types.Message):
#     token = await token_storage.check_auth(message)
#     if not token: return
    
#     status, data = await api_client.api_get_cards(token)
#     if status == 200:
#         if not data:
#             await message.reply('No cards.')
#             return
#         lines = ["💳 <b>Your Cards:</b>"]
#         for c in data:
#             lines.append(f"ID: {c['id']} | {c.get('label') or ''} | {c.get('masked')} | {c.get('holder') or ''} | {c.get('exp') or ''}")
#         await message.reply('\n'.join(lines))
#     else:
#         await message.reply(f'Error: {status} {data}')

# ...
from ..keyboards import main_menu_keyboard # <-- ИМПОРТ

@dp.message_handler(commands=['list']) # Оставляем для совместимости
@dp.callback_query_handler(lambda c: c.data == 'cards_list') # <-- НОВЫЙ ХЕНДЛЕР
async def cmd_list(target: types.Message | types.CallbackQuery):
    # Универсализация для обработки и Message, и CallbackQuery
    message = target.message if isinstance(target, types.CallbackQuery) else target
    user_id = target.from_user.id

    token = await token_storage.check_auth(message)
    master_key = token_storage.get_master_key(user_id) 
    if not token or not master_key: 
        if isinstance(target, types.CallbackQuery): await target.answer()
        return
    
    if isinstance(target, types.CallbackQuery):
        await target.answer()
        
    # ... (логика получения ключа и RAW данных)
    key = derive_key(master_key) 
    status, data_raw = await api_client.api_get_cards(token)
    
    if status == 200:
        if not data_raw:
            await message.edit_text('💳 У вас пока нет сохраненных карт.', reply_markup=main_menu_keyboard())
            return
            
        lines = ["💳 <b>СОХРАНЕННЫЕ КАРТЫ:</b>\n"]
        for c_raw in data_raw:
            try:
                nonce = base64.b64decode(c_raw['nonce_b64'])
                ct = base64.b64decode(c_raw['enc_data_b64'])
                payload = decrypt_payload(key, nonce, ct)
                
                card_num = payload.get('card_number', '')
                masked = '<code>' + ('*' * (len(card_num)-4) + card_num[-4:]) + '</code>' if len(card_num) > 4 else '<code>N/A</code>'
                holder = payload.get('holder') or 'Нет данных'
                exp = payload.get('exp') or 'N/A'
                
                lines.append(
                    f"🔸 ID: <b>{c_raw['id']}</b> | {c_raw.get('label') or 'Без метки'}\n"
                    f"   Счет: {masked} | Владелец: {holder} | Срок: {exp}\n"
                )
            except Exception:
                lines.append(f"❌ ID: {c_raw['id']} | {c_raw.get('label') or 'Без метки'} | Ошибка дешифровки.")

        await message.edit_text('\n'.join(lines), reply_markup=main_menu_keyboard())
    else:
        await message.edit_text(f'❌ Ошибка API: {status}', reply_markup=main_menu_keyboard())

# --- Хендлер для начала добавления карты ---
@dp.callback_query_handler(lambda c: c.data == 'cards_add')
async def start_add_card_callback(callback_query: types.CallbackQuery):
    if not await token_storage.check_auth(callback_query.message): 
        await callback_query.answer()
        return
        
    await callback_query.answer()
    await callback_query.message.reply('📝 Добавление карты. Введите метку/название (или /cancel)')
    await AddCardStates.label.set()

@dp.message_handler(commands=['add'])
async def cmd_add(message: types.Message):
    if not await token_storage.check_auth(message): return
    await message.reply('Adding card. Send label (or /cancel)')
    await AddCardStates.label.set()

@dp.message_handler(state=AddCardStates.label)
async def state_label(message: types.Message, state: FSMContext):
    await state.update_data(label=message.text)
    await message.reply('Card number (digits only):')
    await AddCardStates.next()

@dp.message_handler(state=AddCardStates.card_number)
async def state_card_number(message: types.Message, state: FSMContext):
    await state.update_data(card_number=message.text)
    await message.reply('Holder name:')
    await AddCardStates.next()

@dp.message_handler(state=AddCardStates.holder)
async def state_holder(message: types.Message, state: FSMContext):
    await state.update_data(holder=message.text)
    await message.reply('Expiry (MM/YY):')
    await AddCardStates.next()

@dp.message_handler(state=AddCardStates.exp)
async def state_exp(message: types.Message, state: FSMContext):
    await state.update_data(exp=message.text)
    await message.reply('CVV (send privately):')
    await AddCardStates.next()

@dp.message_handler(state=AddCardStates.cvv)
async def state_cvv(message: types.Message, state: FSMContext):
    await state.update_data(cvv=message.text)
    await message.reply('Notes (optional):')
    await AddCardStates.next()

# @dp.message_handler(state=AddCardStates.notes)
# async def state_notes(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     data['notes'] = message.text
#     token = token_storage.get_token(message.from_user.id)
#     if not token:
#         await message.reply('Auth lost. Please /login again')
#         await state.finish()
#         return

#     payload = {
#         'label': data.get('label'),
#         'card_number': data.get('card_number'),
#         'holder': data.get('holder'),
#         'exp': data.get('exp'),
#         'cvv': data.get('cvv'),
#         'notes': data.get('notes')
#     }
    
#     status, data = await api_client.api_add_card(token, payload)
#     if status in (200, 201):
#         await message.reply('Card added.')
#     else:
#         await message.reply(f'Failed to add: {status} {data}')
#     await state.finish()

# ...
@dp.message_handler(state=AddCardStates.notes)
async def state_notes(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data['notes'] = message.text
    token = token_storage.get_token(message.from_user.id)
    master_key = token_storage.get_master_key(message.from_user.id)
    
    if not token or not master_key:
        await message.reply('Auth/Key lost. Please /login again')
        await state.finish()
        return

    # 1. Шифрование на стороне клиента (бота)
    key = derive_key(master_key)
    
    payload_to_encrypt = {
        'card_number': data.get('card_number'),
        'holder': data.get('holder'),
        'exp': data.get('exp'),
        'cvv': data.get('cvv'),
        'notes': data.get('notes')
    }
    nonce, ct = encrypt_payload(key, payload_to_encrypt)
    
    # 2. Формируем RAW POST-запрос
    raw_payload = {
        'label': data.get('label'),
        'enc_data_b64': base64.b64encode(ct).decode('ascii'),
        'nonce_b64': base64.b64encode(nonce).decode('ascii'),
    }

    # API_add_card теперь отправляет RAW данные в /cards
    status, data_response = await api_client.api_add_card(token, raw_payload) 
    
    if status in (200, 201):
        await message.reply('Card added (encrypted).')
    else:
        await message.reply(f'Failed to add: {status} {data_response}')
    await state.finish()