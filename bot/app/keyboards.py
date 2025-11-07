from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Генерирует инлайн-клавиатуру для главного меню."""
    kb = InlineKeyboardMarkup(row_width=2)
    
    # Секция Карты
    kb.add(InlineKeyboardButton("💳 Мои Карты (Список)", callback_data="cards_list"))
    kb.add(InlineKeyboardButton("➕ Добавить Карту", callback_data="cards_add"))
    
    # Секция Подписки
    kb.add(InlineKeyboardButton("🔄 Мои Подписки (Список)", callback_data="subs_list"))
    kb.add(InlineKeyboardButton("➕ Добавить Подписку", callback_data="subs_add"))
    
    # Общие команды
    kb.add(InlineKeyboardButton("🚪 Выход / Logout", callback_data="logout"))
    
    return kb

def item_actions_keyboard(item_type: str, item_id: int) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру действий для конкретного элемента.
    item_type: 'card' или 'sub'
    item_id: ID элемента в БД
    """
    kb = InlineKeyboardMarkup(row_width=2)
    
    if item_type == 'card':
        kb.add(InlineKeyboardButton("👁️ Просмотр полной карты", callback_data=f"view_card:{item_id}"))
        # kb.add(InlineKeyboardButton("✏️ Изменить", callback_data=f"edit_card:{item_id}")) # Можно добавить позже
        kb.add(InlineKeyboardButton("🗑️ Удалить", callback_data=f"del_card:{item_id}"))
    
    elif item_type == 'sub':
        kb.add(InlineKeyboardButton("👁️ Просмотр деталей", callback_data=f"view_sub:{item_id}"))
        # kb.add(InlineKeyboardButton("✏️ Изменить", callback_data=f"edit_sub:{item_id}")) # Можно добавить позже
        kb.add(InlineKeyboardButton("🗑️ Удалить", callback_data=f"del_sub_id:{item_id}")) # Избегаем конфликта с командой /del_sub

    kb.add(InlineKeyboardButton("🔙 Назад в меню", callback_data="menu"))
    
    return kb