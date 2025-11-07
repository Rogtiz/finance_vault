from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from ..bot import dp
from ..states import AddSubStates
from ..services import token_storage, api_client

@dp.message_handler(commands=['list_subs'])
async def cmd_list_subs(message: types.Message):
    token = await token_storage.check_auth(message)
    if not token: return
    
    status, data = await api_client.api_get_subs(token)
    if status == 200:
        if not data:
            await message.reply('No subscriptions.')
            return
        lines = ["🔄 <b>Your Subscriptions:</b>"]
        for s in data:
            cost_str = f"{s['cost']} {s['currency']}"
            cycle_str = s['billing_cycle']
            date_str = s.get('next_billing_date') or s.get('start_date') or ''
            lines.append(f"ID: {s['id']} | <b>{s['service_name']}</b> | {cost_str} ({cycle_str}) | Next: {date_str}")
        await message.reply('\n'.join(lines))
    else:
        await message.reply(f'Error: {status} {data}')

@dp.message_handler(Command('del_sub'))
async def cmd_del_sub(message: types.Message):
    token = await token_storage.check_auth(message)
    if not token: return
    try:
        sub_id = int(message.get_args())
    except (ValueError, TypeError):
        await message.reply("Please provide an ID, e.g., <code>/del_sub 123</code>")
        return

    status, data = await api_client.api_del_sub(token, sub_id)
    if status == 200:
        await message.reply(f'Subscription {sub_id} deleted.')
    elif status == 404:
        await message.reply(f'Subscription {sub_id} not found.')
    else:
        await message.reply(f'Error: {status} {data}')

@dp.message_handler(commands=['add_sub'])
async def cmd_add_sub(message: types.Message):
    if not await token_storage.check_auth(message): return
    await message.reply('Adding subscription. What is the service name? (e.g., Netflix) (or /cancel)')
    await AddSubStates.service_name.set()

@dp.message_handler(state=AddSubStates.service_name)
async def sub_state_service_name(message: types.Message, state: FSMContext):
    await state.update_data(service_name=message.text)
    await message.reply('Cost (e.g., 10.99):')
    await AddSubStates.next()

@dp.message_handler(state=AddSubStates.cost)
async def sub_state_cost(message: types.Message, state: FSMContext):
    try:
        cost = float(message.text)
        await state.update_data(cost=cost)
        await message.reply('Currency (e.g., USD, RUB):')
        await AddSubStates.next()
    except ValueError:
        await message.reply('Invalid number. Please send cost (e.g., 10.99):')

@dp.message_handler(state=AddSubStates.currency)
async def sub_state_currency(message: types.Message, state: FSMContext):
    await state.update_data(currency=message.text)
    await message.reply('Billing cycle (e.g., monthly, yearly):')
    await AddSubStates.next()

@dp.message_handler(state=AddSubStates.billing_cycle)
async def sub_state_billing_cycle(message: types.Message, state: FSMContext):
    await state.update_data(billing_cycle=message.text)
    await message.reply('Next billing date (YYYY-MM-DD or send "skip"):')
    await AddSubStates.next()

@dp.message_handler(state=AddSubStates.next_billing_date)
async def sub_state_next_billing_date(message: types.Message, state: FSMContext):
    if message.text.lower() != 'skip':
        await state.update_data(next_billing_date=message.text)
    await message.reply('Start date (YYYY-MM-DD or send "skip"):')
    await AddSubStates.next()

@dp.message_handler(state=AddSubStates.start_date)
async def sub_state_start_date(message: types.Message, state: FSMContext):
    if message.text.lower() != 'skip':
        await state.update_data(start_date=message.text)
    await message.reply('Notes (optional, or send "skip"):')
    await AddSubStates.next()

@dp.message_handler(state=AddSubStates.notes)
async def sub_state_notes(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text.lower() != 'skip':
        data['notes'] = message.text

    token = token_storage.get_token(message.from_user.id)
    if not token:
        await message.reply('Auth lost. Please /login again')
        await state.finish()
        return
        
    payload = {
        'service_name': data.get('service_name'),
        'cost': data.get('cost'),
        'currency': data.get('currency'),
        'billing_cycle': data.get('billing_cycle'),
        'next_billing_date': data.get('next_billing_date'),
        'start_date': data.get('start_date'),
        'notes': data.get('notes')
    }
    
    status, data = await api_client.api_add_sub(token, payload)
    if status in (200, 201):
        await message.reply('Subscription added.')
    else:
        await message.reply(f'Failed to add: {status} {data}')
    await state.finish()