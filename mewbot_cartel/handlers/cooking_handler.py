# -*- coding: utf-8 -*-
"""
Хендлер варки веществ
"""

import random
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_manager import (
    get_user, get_factory, get_active_cooking, start_cooking,
    update_cooking, add_to_inventory, remove_from_inventory,
    get_inventory, update_user
)
from config.settings import GAME_CONFIG

router = Router()


@router.message(Command("cook_menu"))
@router.callback_query(F.data == "cook_menu")
async def cook_menu(event):
    """Меню выбора вещества для варки"""
    message = event.message if isinstance(event, CallbackQuery) else event
    user_id = event.from_user.id
    
    user = await get_user(user_id)
    if not user:
        await message.answer("❌ Сначала используй /start")
        return
    
    if user['in_jail']:
        await message.answer(f"🔒 Ты в тюрьме до {user['jail_until'].strftime('%H:%M %d.%m')}")
        return
    
    # Проверяем активную варку
    active = await get_active_cooking(user_id)
    if active:
        await message.answer("⚗️ У тебя уже идет варка! Используй /control_panel")
        return
    
    text = """
⚗️ <b>ВЫБОР ВЕЩЕСТВА</b>

Выбери что варить. Чем круче вещество — тем выше прибыль, но и риск взрыва.

<b>ДОСТУПНЫЕ ВЕЩЕСТВА:</b>
    """
    
    buttons = []
    
    for sub_id, sub_data in GAME_CONFIG['SUBSTANCES'].items():
        tier_emoji = "⭐" * sub_data['tier']
        cook_time_min = sub_data['cook_time'] // 60
        
        # Проверяем доступность по уровню
        required_level = sub_data['tier'] * 2
        is_locked = user['level'] < required_level
        
        if is_locked:
            button_text = f"🔒 {sub_data['name']} (LVL {required_level})"
            callback_data = "substance_locked"
        else:
            button_text = f"{sub_data['name']} {tier_emoji}"
            callback_data = f"cook_select_{sub_id}"
        
        info_text = f"""
{sub_data['name']} {tier_emoji}
├ Время варки: {cook_time_min} мин
├ Базовая цена: ${sub_data['base_price']}/г
├ Риск взрыва: {sub_data['explosion_risk']}%
└ Требует: LVL {required_level}
        """
        
        text += info_text
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="factory_main")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
        await event.answer()
    else:
        await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("cook_select_"))
async def cook_select(callback: CallbackQuery):
    """Выбрано вещество"""
    substance = callback.data.replace("cook_select_", "")
    user_id = callback.from_user.id
    
    sub_data = GAME_CONFIG['SUBSTANCES'][substance]
    
    # Получаем инвентарь прекурсоров
    inventory = await get_inventory(user_id, 'precursor')
    
    text = f"""
⚗️ <b>{sub_data['name']}</b>

⏱ Время варки: <b>{sub_data['cook_time'] // 60}</b> минут
🌡 Оптимальная температура: <b>{sub_data['optimal_temp']}°C</b>
💨 Макс. давление: <b>{sub_data['pressure_max']} PSI</b>
💣 Риск взрыва: <b>{sub_data['explosion_risk']}%</b>

<b>ТРЕБУЕМЫЕ ПРЕКУРСОРЫ:</b>
    """
    
    missing = []
    for prec, amount in sub_data['precursors'].items():
        has = next((i['quantity'] for i in inventory if i['item_id'] == prec), 0)
        status = "✅" if has >= amount else "❌"
        text += f"{status} {prec.title()}: {has}/{amount}\n"
        
        if has < amount:
            missing.append(prec)
    
    if missing:
        text += f"\n⚠️ <b>Не хватает:</b> {', '.join(missing)}"
        text += "\n\n💡 Купи прекурсоры в /market"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 В Магазин", callback_data="market_precursors")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="cook_menu")]
        ])
    else:
        text += "\n\n✅ Все прекурсоры в наличии!"
        text += "\n\n<b>Сколько грамм варить?</b>"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="10г", callback_data=f"cook_amount_{substance}_10"),
                InlineKeyboardButton(text="50г", callback_data=f"cook_amount_{substance}_50")
            ],
            [
                InlineKeyboardButton(text="100г", callback_data=f"cook_amount_{substance}_100"),
                InlineKeyboardButton(text="500г", callback_data=f"cook_amount_{substance}_500")
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="cook_menu")]
        ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("cook_amount_"))
async def cook_start(callback: CallbackQuery):
    """Начать варку"""
    parts = callback.data.replace("cook_amount_", "").split("_")
    substance = parts[0]
    amount = int(parts[1])
    
    user_id = callback.from_user.id
    user = await get_user(user_id)
    factory = await get_factory(user_id)
    
    sub_data = GAME_CONFIG['SUBSTANCES'][substance]
    
    # Списываем прекурсоры
    for prec, prec_amount in sub_data['precursors'].items():
        success = await remove_from_inventory(user_id, 'precursor', prec, prec_amount * (amount // 10))
        if not success:
            await callback.answer("❌ Не хватает прекурсоров!", show_alert=True)
            return
    
    # Создаем сессию варки
    session_id = await start_cooking(
        user_id, 
        factory['id'], 
        substance, 
        amount,
        sub_data['precursors']
    )
    
    # Добавляем Heat
    heat_increase = 5 + (sub_data['tier'] * 2)
    new_heat = min(100, user['heat'] + heat_increase)
    await update_user(user_id, heat=new_heat)
    
    cook_time_min = sub_data['cook_time'] // 60
    
    text = f"""
🔥 <b>ВАРКА НАЧАТА!</b>

⚗️ Вещество: <b>{sub_data['name']}</b>
⚖️ Количество: <b>{amount}г</b>
⏱ Время: <b>~{cook_time_min} минут</b>

🌡 Целевая температура: <b>{sub_data['optimal_temp']}°C</b>
💨 Макс. давление: <b>{sub_data['pressure_max']} PSI</b>

⚠️ <b>Розыск увеличился до {new_heat}/100</b>

<i>Используй /control_panel для управления процессом!</i>
<i>Не забывай следить за показателями — это не пассивная игра!</i>
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎛 Панель Управления", callback_data="control_panel")],
        [InlineKeyboardButton(text="◀️ В Меню", callback_data="back_to_start")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("🔥 Реактор запущен!")


@router.message(Command("control_panel"))
@router.callback_query(F.data == "control_panel")
async def control_panel(event):
    """Панель управления варкой"""
    message = event.message if isinstance(event, CallbackQuery) else event
    user_id = event.from_user.id
    
    cooking = await get_active_cooking(user_id)
    
    if not cooking:
        await message.answer("❌ Нет активной варки! Начни через /cook_menu")
        return
    
    sub_data = GAME_CONFIG['SUBSTANCES'][cooking['substance']]
    
    # Рассчитываем прогресс
    now = datetime.now()
    elapsed = (now - cooking['start_time']).total_seconds()
    total_time = sub_data['cook_time']
    progress = min(100, int((elapsed / total_time) * 100))
    
    # Определяем стадию
    if progress < 25:
        stage = "Смешивание"
        stage_emoji = "🌀"
    elif progress < 50:
        stage = "Нагрев"
        stage_emoji = "🔥"
    elif progress < 75:
        stage = "Реакция"
        stage_emoji = "⚗️"
    else:
        stage = "Кристаллизация"
        stage_emoji = "💎"
    
    # Оценка чистоты
    temp_diff = abs(cooking['current_temp'] - cooking['target_temp'])
    temp_penalty = min(30, temp_diff * 2)
    
    pressure_penalty = 0
    if cooking['pressure'] > sub_data['pressure_max'] * 0.8:
        pressure_penalty = 10
    
    fume_penalty = min(20, cooking['fumes'] // 5)
    
    estimated_purity = max(0, sub_data['base_purity'] - temp_penalty - pressure_penalty - fume_penalty)
    
    # Статус бары
    temp_bar = "🟩" * int(cooking['current_temp'] / 30) + "⬜" * (10 - int(cooking['current_temp'] / 30))
    pressure_bar = "🟦" * int(cooking['pressure'] / 100) + "⬜" * (10 - int(cooking['pressure'] / 100))
    purity_bar = "🟨" * int(estimated_purity / 10) + "⬜" * (10 - int(estimated_purity / 10))
    progress_bar = "🟩" * (progress // 10) + "⬜" * (10 - progress // 10)
    
    text = f"""
🎛 <b>ПАНЕЛЬ УПРАВЛЕНИЯ</b>

⚗️ <b>{sub_data['name']}</b>
{stage_emoji} Стадия: <b>{stage}</b>

📊 Прогресс: <b>{progress}%</b>
{progress_bar}

🌡 Температура: <b>{cooking['current_temp']:.1f}°C</b> (цель: {cooking['target_temp']}°C)
{temp_bar}

💨 Давление: <b>{cooking['pressure']:.0f} PSI</b> (макс: {sub_data['pressure_max']})
{pressure_bar}

💎 Чистота: <b>~{estimated_purity:.0f}%</b>
{purity_bar}

☠️ Токсичность: <b>{cooking['fumes']}</b>
{'⚠️ ВЫСОКИЙ УРОВЕНЬ! Включи вентиляцию!' if cooking['fumes'] > 50 else '✅ Норма'}

⏱ Осталось: <b>~{(total_time - elapsed) // 60:.0f} мин</b>
    """
    
    # Проверка на критические параметры
    warnings = []
    if cooking['pressure'] > sub_data['pressure_max'] * 0.9:
        warnings.append("🚨 ДАВЛЕНИЕ КРИТИЧЕСКОЕ!")
    if temp_diff > 20:
        warnings.append("⚠️ Температура вне диапазона!")
    if cooking['fumes'] > 70:
        warnings.append("☠️ ОПАСНАЯ ТОКСИЧНОСТЬ!")
    
    if warnings:
        text += "\n\n" + "\n".join(warnings)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔥 +10°C", callback_data="cook_heat_up"),
            InlineKeyboardButton(text="❄️ -10°C", callback_data="cook_heat_down")
        ],
        [
            InlineKeyboardButton(text="💨 Сбросить давление", callback_data="cook_release_pressure"),
        ],
        [
            InlineKeyboardButton(text="🌪 Вентиляция", callback_data="cook_ventilate"),
            InlineKeyboardButton(text="🧪 Катализатор", callback_data="cook_catalyst")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="control_panel"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
        await event.answer()
    else:
        await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "cook_heat_up")
async def cook_heat_up(callback: CallbackQuery):
    """Повысить температуру"""
    cooking = await get_active_cooking(callback.from_user.id)
    
    if not cooking:
        await callback.answer("❌ Нет активной варки!")
        return
    
    new_temp = min(300, cooking['current_temp'] + 10)
    new_pressure = cooking['pressure'] + random.uniform(10, 30)
    
    await update_cooking(cooking['id'], current_temp=new_temp, pressure=new_pressure)
    
    await callback.answer("🔥 Температура повышена!")
    await control_panel(callback)


@router.callback_query(F.data == "cook_heat_down")
async def cook_heat_down(callback: CallbackQuery):
    """Понизить температуру"""
    cooking = await get_active_cooking(callback.from_user.id)
    
    if not cooking:
        await callback.answer("❌ Нет активной варки!")
        return
    
    new_temp = max(20, cooking['current_temp'] - 10)
    new_pressure = max(0, cooking['pressure'] - random.uniform(5, 15))
    
    await update_cooking(cooking['id'], current_temp=new_temp, pressure=new_pressure)
    
    await callback.answer("❄️ Температура понижена!")
    await control_panel(callback)


@router.callback_query(F.data == "cook_release_pressure")
async def cook_release_pressure(callback: CallbackQuery):
    """Сбросить давление"""
    cooking = await get_active_cooking(callback.from_user.id)
    
    if not cooking:
        await callback.answer("❌ Нет активной варки!")
        return
    
    new_pressure = cooking['pressure'] * 0.3
    new_fumes = cooking['fumes'] + random.randint(5, 15)
    
    await update_cooking(cooking['id'], pressure=new_pressure, fumes=new_fumes)
    
    await callback.answer("💨 Давление сброшено! +токсичность")
    await control_panel(callback)


@router.callback_query(F.data == "cook_ventilate")
async def cook_ventilate(callback: CallbackQuery):
    """Включить вентиляцию"""
    cooking = await get_active_cooking(callback.from_user.id)
    factory = await get_factory(callback.from_user.id)
    
    if not cooking:
        await callback.answer("❌ Нет активной варки!")
        return
    
    # Проверяем наличие вентиляции
    equipment = factory.get('equipment', {})
    has_vent = any('ventilation' in k for k in equipment.keys())
    
    if not has_vent:
        await callback.answer("❌ Нет вентиляции! Купи в /market", show_alert=True)
        return
    
    new_fumes = max(0, cooking['fumes'] - 30)
    
    await update_cooking(cooking['id'], fumes=new_fumes)
    
    await callback.answer("🌪 Вентиляция включена!")
    await control_panel(callback)


@router.callback_query(F.data == "cook_catalyst")
async def cook_catalyst(callback: CallbackQuery):
    """Добавить катализатор"""
    cooking = await get_active_cooking(callback.from_user.id)
    user_id = callback.from_user.id
    
    if not cooking:
        await callback.answer("❌ Нет активной варки!")
        return
    
    # Проверяем наличие катализатора в инвентаре
    inventory = await get_inventory(user_id, 'catalyst')
    
    if not inventory or inventory[0]['quantity'] < 1:
        await callback.answer("❌ Нет катализатора! Купи в /market", show_alert=True)
        return
    
    # Списываем катализатор
    await remove_from_inventory(user_id, 'catalyst', 'basic_catalyst', 1)
    
    # Повышаем чистоту
    new_purity = min(99, cooking['purity'] + random.uniform(5, 15))
    
    await update_cooking(cooking['id'], purity=new_purity)
    
    await callback.answer("🧪 Катализатор добавлен! +чистота")
    await control_panel(callback)
