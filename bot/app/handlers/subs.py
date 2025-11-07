from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from ..bot import dp
from ..states import AddSubStates
from ..services import token_storage, api_client

# @dp.message_handler(commands=['list_subs'])
# async def cmd_list_subs(message: types.Message):
#     token = await token_storage.check_auth(message)
#     if not token: return
    
#     status, data = await api_client.api_get_subs(token)
#     if status == 200:
#         if not data:
#             await message.reply('No subscriptions.')
#             return
#         lines = ["🔄 <b>Your Subscriptions:</b>"]
#         for s in data:
#             cost_str = f"{s['cost']} {s['currency']}"
#             cycle_str = s['billing_cycle']
#             date_str = s.get('next_billing_date') or s.get('start_date') or ''
#             lines.append(f"ID: {s['id']} | <b>{s['service_name']}</b> | {cost_str} ({cycle_str}) | Next: {date_str}")
#         await message.reply('\n'.join(lines))
#     else:
#         await message.reply(f'Error: {status} {data}')

# ...
from ..keyboards import main_menu_keyboard
from .cards import check_and_get_auth # <--- ИМПОРТИРУЕМ ИЗ КАРТ, ЕСЛИ ОНА ТАМ БЫЛА

# ...
# @dp.message_handler(commands=['list_subs']) # Оставляем для совместимости
# @dp.callback_query_handler(lambda c: c.data == 'subs_list') # <-- НОВЫЙ ХЕНДЛЕР
# async def cmd_list_subs(target: types.Message | types.CallbackQuery):
#     message = target.message if isinstance(target, types.CallbackQuery) else target
#     user_id = target.from_user.id
    
#     token = await token_storage.check_auth(message)
#     if not token: 
#         if isinstance(target, types.CallbackQuery): await target.answer()
#         return

@dp.message_handler(commands=['list_subs']) # Оставляем для совместимости
@dp.callback_query_handler(lambda c: c.data == 'subs_list') # <-- НОВЫЙ ХЕНДЛЕР
async def cmd_list_subs(target: types.Message | types.CallbackQuery):
    
    token, _ = await check_and_get_auth(target)
    if not token: return
    
    message = target.message if isinstance(target, types.CallbackQuery) else target
    if isinstance(target, types.CallbackQuery):
        await target.answer()
        
    status, data = await api_client.api_get_subs(token)
    
    if status == 200:
        if not data:
            await message.edit_text('🔄 У вас пока нет активных подписок.', reply_markup=main_menu_keyboard())
            return
            
        lines = ["🔄 <b>ВАШИ ПОДПИСКИ:</b>\n"]
        total_cost = 0
        
        for s in data:
            cost = s['cost']
            currency = s['currency']
            cycle = s['billing_cycle']
            next_date = s.get('next_billing_date') or 'N/A'
            
            lines.append(
                f"🌟 ID: <b>{s['id']}</b> | <b>{s['service_name']}</b>\n"
                f"   Стоимость: <code>{cost:.2f} {currency}</code> ({cycle})\n"
                f"   След. списание: <code>{next_date}</code>\n"
            )
            if currency == 'USD' and cycle.lower() == 'monthly':
                total_cost += cost # Простой подсчет только для USD/monthly

        lines.append(f"\n💵 Общий (USD/мес. ~): <b>{total_cost:.2f} USD</b>")
        
        # await message.edit_text('\n'.join(lines), reply_markup=main_menu_keyboard())

        if isinstance(target, types.CallbackQuery):
            await message.edit_text('\n'.join(lines), reply_markup=main_menu_keyboard())
        else:
            await message.reply('\n'.join(lines), reply_markup=main_menu_keyboard())
    else:
        await message.edit_text(f'❌ Ошибка API: {status}', reply_markup=main_menu_keyboard())


# --- Хендлер для начала добавления подписки ---
@dp.callback_query_handler(lambda c: c.data == 'subs_add')
async def start_add_sub_callback(callback_query: types.CallbackQuery):
    if not await token_storage.check_auth(callback_query.message): 
        await callback_query.answer()
        return
        
    await callback_query.answer()
    await callback_query.message.reply('📝 Добавление подписки. Введите название сервиса (или /cancel)')
    await AddSubStates.service_name.set()

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