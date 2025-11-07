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