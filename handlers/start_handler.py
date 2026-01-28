# ДОБАВЬ ЭТО В КОНЕЦ handlers/start_handler.py:

@router.message(Command("inventory"))
async def cmd_inventory(message: Message):
    """Инвентарь пользователя"""
    user_id = message.from_user.id
    
    # Получаем все из инвентаря
    precursors = await get_inventory(user_id, 'precursor')
    products = await get_inventory(user_id, 'product')
    equipment = await get_inventory(user_id, 'equipment')
    
    text = "<b>📦 ИНВЕНТАРЬ</b>\n\n"
    
    # Прекурсоры
    if precursors:
        text += "<b>💊 ПРЕКУРСОРЫ:</b>\n"
        for item in precursors:
            text += f"├ {item['item_id'].title()}: {item['quantity']} шт\n"
        text += "\n"
    
    # Готовый товар
    if products:
        text += "<b>⚗️ ГОТОВЫЙ ТОВАР:</b>\n"
        for item in products:
            purity = item.get('metadata', {}).get('purity', 75)
            sub_data = GAME_CONFIG['SUBSTANCES'].get(item['item_id'], {})
            text += f"├ {sub_data.get('name', item['item_id'])}\n"
            text += f"│  ├ Количество: {item['quantity']}г\n"
            text += f"│  └ Чистота: {purity:.1f}%\n"
        text += "\n"
    
    # Оборудование в инвентаре
    if equipment:
        text += "<b>⚙️ ОБОРУДОВАНИЕ:</b>\n"
        for item in equipment:
            text += f"├ {item['item_id']}: {item['quantity']} шт\n"
        text += "\n"
    
    if not precursors and not products and not equipment:
        text += "❌ Инвентарь пуст\n\n"
        text += "💡 Купи прекурсоры в /market\n"
        text += "💡 Свари товар через /cook_menu"
    else:
        text += "💰 Продай товар через /market"
    
    await message.answer(text)
