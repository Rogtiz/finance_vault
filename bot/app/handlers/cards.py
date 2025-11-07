from aiogram import types
from aiogram.dispatcher import FSMContext

from ..bot import dp
from ..states import AddCardStates
from ..services import token_storage, api_client

@dp.message_handler(commands=['list'])
async def cmd_list(message: types.Message):
    token = await token_storage.check_auth(message)
    if not token: return
    
    status, data = await api_client.api_get_cards(token)
    if status == 200:
        if not data:
            await message.reply('No cards.')
            return
        lines = ["💳 <b>Your Cards:</b>"]
        for c in data:
            lines.append(f"ID: {c['id']} | {c.get('label') or ''} | {c.get('masked')} | {c.get('holder') or ''} | {c.get('exp') or ''}")
        await message.reply('\n'.join(lines))
    else:
        await message.reply(f'Error: {status} {data}')

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

@dp.message_handler(state=AddCardStates.notes)
async def state_notes(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data['notes'] = message.text
    token = token_storage.get_token(message.from_user.id)
    if not token:
        await message.reply('Auth lost. Please /login again')
        await state.finish()
        return

    payload = {
        'label': data.get('label'),
        'card_number': data.get('card_number'),
        'holder': data.get('holder'),
        'exp': data.get('exp'),
        'cvv': data.get('cvv'),
        'notes': data.get('notes')
    }
    
    status, data = await api_client.api_add_card(token, payload)
    if status in (200, 201):
        await message.reply('Card added.')
    else:
        await message.reply(f'Failed to add: {status} {data}')
    await state.finish()