from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from ..bot import dp
from ..states import AddSubStates
from ..services import token_storage, api_client
from ..keyboards import main_menu_keyboard, item_actions_keyboard
from .cards import check_and_get_auth # Импортируем функцию проверки аутентификации

@dp.message_handler(commands=['list_subs'])
@dp.callback_query_handler(lambda c: c.data == 'subs_list') 
async def cmd_list_subs(target: types.Message | types.CallbackQuery):
    token, _ = await check_and_get_auth(target)
    if not token: return
    
    message = target.message if isinstance(target, types.CallbackQuery) else target
    if isinstance(target, types.CallbackQuery):
        await target.answer()
        await message.delete() 

    status, data = await api_client.api_get_subs(token)
    
    if status == 200:
        if not data:
            await message.answer('🔄 У вас пока нет активных подписок.', reply_markup=main_menu_keyboard())
            return
            
        await message.answer("🔄 <b>СПИСОК ВАШИХ ПОДПИСОК:</b>")
        
        for s in data:
            cost = s['cost']
            currency = s['currency']
            cycle = s['billing_cycle']
            next_date = s.get('next_billing_date') or 'N/A'
            
            sub_text = (
                f"🌟 ID: <b>{s['id']}</b> | <b>{s['service_name']}</b>\n"
                f"   Стоимость: <code>{cost:.2f} {currency}</code> ({cycle})\n"
                f"   След. списание: <code>{next_date}</code>"
            )
            
            await message.answer(
                sub_text,
                reply_markup=item_actions_keyboard('sub', s['id'])
            )

        await message.answer("👆 Выберите действие для просмотра деталей или удаления.", reply_markup=main_menu_keyboard())

    else:
        await message.reply(f'❌ Ошибка API: {status}', reply_markup=main_menu_keyboard())


@dp.callback_query_handler(lambda c: c.data == 'subs_add')
async def start_add_sub_callback(callback_query: types.CallbackQuery):
    token, _ = await check_and_get_auth(callback_query)
    if not token: 
        await callback_query.answer()
        return
        
    await callback_query.answer()
    await callback_query.message.delete()
    
    await callback_query.message.answer(
        '📝 **ДОБАВЛЕНИЕ ПОДПИСКИ**\nВведите название сервиса (или /cancel):', 
        parse_mode="Markdown"
    )
    await AddSubStates.service_name.set()

@dp.message_handler(Command('del_sub'))
@dp.callback_query_handler(lambda c: c.data.startswith('del_sub_id:'))
async def cmd_del_sub(target: types.Message | types.CallbackQuery):
    token, _ = await check_and_get_auth(target)
    if not token: return

    if isinstance(target, types.CallbackQuery):
        await target.answer()
        sub_id = int(target.data.split(':')[1])
        message = target.message
    else:
        try:
            sub_id = int(target.get_args())
            message = target
        except (ValueError, TypeError):
            await target.reply("Please provide an ID, e.g., <code>/del_sub 123</code>")
            return
    
    status, data = await api_client.api_del_sub(token, sub_id)
    
    if status == 200:
        await message.edit_text(f'✅ Подписка ID <b>{sub_id}</b> удалена.', reply_markup=main_menu_keyboard())
    elif status == 404:
        await message.edit_text(f'❌ Подписка ID <b>{sub_id}</b> не найдена.', reply_markup=main_menu_keyboard())
    else:
        await message.edit_text(f'❌ Error: {status} {data}', reply_markup=main_menu_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('view_sub:'))
async def view_sub_callback(callback_query: types.CallbackQuery):
    token, _ = await check_and_get_auth(callback_query)
    if not token: return
    
    await callback_query.answer()
    
    sub_id = int(callback_query.data.split(':')[1])
    message = callback_query.message
    
    status, s = await api_client.api_get_subs_id(token, sub_id)
    
    if status == 200:
        txt = (
            f"📑 <b>ДЕТАЛИ ПОДПИСКИ ID: {sub_id}</b>\n"
            f"----------------------------------------\n"
            f"Сервис: <b>{s.get('service_name')}</b>\n"
            f"Сумма: <code>{s.get('cost'):.2f} {s.get('currency')}</code>\n"
            f"Цикл: {s.get('billing_cycle')}\n"
            f"След. списание: <b>{s.get('next_billing_date') or 'N/A'}</b>\n"
            f"Дата начала: {s.get('start_date') or 'N/A'}\n"
            f"Заметки:\n{s.get('notes') or 'Нет'}"
        )
        
        await message.edit_text(txt, reply_markup=item_actions_keyboard('sub', sub_id))
    
    else:
        await message.edit_text(f"❌ Ошибка: Подписка ID {sub_id} не найдена или ошибка API.", reply_markup=main_menu_keyboard())

@dp.message_handler(commands=['add_sub'])
async def cmd_add_sub(message: types.Message):
    if not await check_and_get_auth(message): return
    await message.reply('Adding subscription. What is the service name? (e.g., Netflix) (or /cancel)')
    await AddSubStates.service_name.set()

# ... (Остальные FSM хендлеры для подписок без изменений)

@dp.message_handler(state=AddSubStates.notes)
async def sub_state_notes(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text.lower() != 'skip':
        data['notes'] = message.text

    token, _ = await check_and_get_auth(message)
    if not token:
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
        await message.reply('Subscription added. Возврат в /menu', reply_markup=main_menu_keyboard())
    else:
        await message.reply(f'Failed to add: {status} {data}', reply_markup=main_menu_keyboard())
    await state.finish()