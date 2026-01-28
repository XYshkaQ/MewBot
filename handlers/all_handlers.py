# -*- coding: utf-8 -*-
"""
ВСЕ ХЕНДЛЕРЫ - ПОЛНАЯ ВЕРСИЯ
Рынок, Картели, PVP, Недвижимость, Отмыв, Безопасность
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_manager import (
    get_user, get_inventory, add_to_inventory, remove_from_inventory,
    update_user, get_leaderboard, get_factory, pool
)
from config.settings import GAME_CONFIG, DONATE_PRICES
import random
import json

# ========== MARKET HANDLER ==========
market_router = Router()

@market_router.message(Command("market"))
@market_router.callback_query(F.data == "market_main")
async def market_main(event):
    text = """
🛒 <b>ЧЕРНЫЙ РЫНОК</b>

Что хочешь купить?

💊 Прекурсоры — сырье для варки
⚙️ Оборудование — улучшай завод
👥 Персонал — нанимай работников
💰 Продать товар — конвертируй в деньги
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💊 Прекурсоры", callback_data="market_precursors")],
        [InlineKeyboardButton(text="⚙️ Оборудование", callback_data="market_equipment")],
        [InlineKeyboardButton(text="👥 Персонал", callback_data="market_staff")],
        [InlineKeyboardButton(text="💰 Продать товар", callback_data="market_sell")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


@market_router.callback_query(F.data == "market_precursors")
async def market_precursors(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    
    text = f"""
💊 <b>ПРЕКУРСОРЫ</b>

💰 Твои чистые: ${user['money_clean']:,}

<b>В НАЛИЧИИ:</b>
├ Бензол: $500
├ Метиламин: $800
├ Ацетон: $300
├ Сафрол: $1,200
├ Ртуть: $1,500
├ Йод: $600
└ Катализатор: $1,000

💡 <b>Стартовый набор x10</b> — $5,000
   Включает: бензол, метиламин, ацетон, катализаторы
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Стартовый набор ($5k)", callback_data="buy_starter_pack")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="market_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@market_router.callback_query(F.data == "buy_starter_pack")
async def buy_starter_pack(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    price = 5000
    
    if user['money_clean'] < price:
        await callback.answer("❌ Недостаточно чистых денег!", show_alert=True)
        return
    
    await update_user(callback.from_user.id, money_clean=user['money_clean'] - price)
    
    precursors = {
        'бензол': 10,
        'метиламин': 10,
        'ацетон': 10,
        'катализатор': 5
    }
    
    for prec, amount in precursors.items():
        await add_to_inventory(callback.from_user.id, 'precursor', prec, amount)
    
    await callback.answer("✅ Стартовый набор куплен!", show_alert=True)
    await market_precursors(callback)


@market_router.callback_query(F.data == "market_equipment")
async def market_equipment(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    
    text = f"""
⚙️ <b>ОБОРУДОВАНИЕ</b>

💰 Твои чистые: ${user['money_clean']:,}

<b>РЕАКТОРЫ:</b>
├ Mk-I: $10,000 (+5% чистота)
├ Mk-II: $50,000 (+15% чистота)
├ Mk-III: $200,000 (+30% чистота)
└ Квантовый: $1,000,000 (+50% чистота)

<b>ВЕНТИЛЯЦИЯ:</b>
├ Базовая: $3,000 (-20% токсичность)
├ Промышленная: $15,000 (-50% токсичность)
└ Система очистки: $80,000 (-90% токсичность)

<b>БЕЗОПАСНОСТЬ:</b>
├ Камеры: $2,000 (-5 Heat)
├ Сигнализация: $8,000 (-10 Heat)
└ Бронедверь: $25,000 (-20 Heat)
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Реактор Mk-I ($10k)", callback_data="buy_equipment_reactor_1")],
        [InlineKeyboardButton(text="Вентиляция ($3k)", callback_data="buy_equipment_ventilation_1")],
        [InlineKeyboardButton(text="Камеры ($2k)", callback_data="buy_equipment_security_cam")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="market_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@market_router.callback_query(F.data.startswith("buy_equipment_"))
async def buy_equipment(callback: CallbackQuery):
    equipment_id = callback.data.replace("buy_equipment_", "")
    user = await get_user(callback.from_user.id)
    factory = await get_factory(callback.from_user.id)
    
    eq_info = GAME_CONFIG['EQUIPMENT'].get(equipment_id)
    if not eq_info:
        await callback.answer("❌ Оборудование не найдено!")
        return
    
    price = eq_info['price']
    
    if user['money_clean'] < price:
        await callback.answer(f"❌ Нужно ${price:,} чистых!", show_alert=True)
        return
    
    # Списываем деньги
    await update_user(callback.from_user.id, money_clean=user['money_clean'] - price)
    
    # Добавляем оборудование в завод
    equipment = factory.get('equipment', {})
    equipment[equipment_id] = {'durability': 100, 'installed': True}
    
    async with pool.acquire() as conn:
        await conn.execute('''
            UPDATE factories 
            SET equipment = $2
            WHERE user_id = $1
        ''', callback.from_user.id, json.dumps(equipment))
    
    await callback.answer(f"✅ {eq_info['name']} куплен и установлен!", show_alert=True)
    await market_equipment(callback)


@market_router.callback_query(F.data == "market_staff")
async def market_staff(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    
    text = f"""
👥 <b>ПЕРСОНАЛ</b>

💰 Твои чистые: ${user['money_clean']:,}

<b>ХИМИКИ:</b>
├ Новичок: $5,000 (+5% чистота, $500/день)
├ Опытный: $25,000 (+15% чистота, $2k/день)
└ Профессор: $100,000 (+30% чистота, $10k/день)

<b>ДИЛЕРЫ:</b>
├ Барыга: $2,000 (риск Heat 30%)
├ Кладмен: $10,000 (риск Heat 15%)
└ Призрак: $50,000 (риск Heat 5%)

<b>ОХРАНА:</b>
├ Гопник: $3,000 (+10 защиты)
├ ЧОП: $15,000 (+25 защиты)
└ Спецназ: $100,000 (+50 защиты)

<b>ПРОЧЕЕ:</b>
└ Адвокат: $50,000 (-20% Heat постоянно)
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Химик-Новичок ($5k)", callback_data="buy_staff_chemist_1")],
        [InlineKeyboardButton(text="Охранник ($3k)", callback_data="buy_staff_guard_1")],
        [InlineKeyboardButton(text="Адвокат ($50k)", callback_data="buy_staff_lawyer")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="market_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@market_router.callback_query(F.data.startswith("buy_staff_"))
async def buy_staff(callback: CallbackQuery):
    staff_id = callback.data.replace("buy_staff_", "")
    user = await get_user(callback.from_user.id)
    factory = await get_factory(callback.from_user.id)
    
    staff_info = GAME_CONFIG['STAFF'].get(staff_id)
    if not staff_info:
        await callback.answer("❌ Персонал не найден!")
        return
    
    price = staff_info['price']
    
    if user['money_clean'] < price:
        await callback.answer(f"❌ Нужно ${price:,} чистых!", show_alert=True)
        return
    
    # Списываем деньги
    await update_user(callback.from_user.id, money_clean=user['money_clean'] - price)
    
    # Добавляем персонал
    staff = factory.get('staff', {})
    staff[staff_id] = {'hired': True, 'salary': staff_info.get('salary', 0)}
    
    async with pool.acquire() as conn:
        await conn.execute('''
            UPDATE factories 
            SET staff = $2
            WHERE user_id = $1
        ''', callback.from_user.id, json.dumps(staff))
    
    await callback.answer(f"✅ {staff_info['name']} нанят!", show_alert=True)
    await market_staff(callback)


@market_router.callback_query(F.data == "market_sell")
async def market_sell(callback: CallbackQuery):
    user_id = callback.from_user.id
    products = await get_inventory(user_id, 'product')
    
    if not products:
        await callback.answer("❌ У тебя нет товара для продажи!", show_alert=True)
        return
    
    text = "<b>💰 ПРОДАТЬ ТОВАР</b>\n\nВыбери что продать:\n\n"
    buttons = []
    
    for product in products:
        substance = product['item_id']
        quantity = product['quantity']
        purity = product.get('metadata', {}).get('purity', 75)
        
        sub_data = GAME_CONFIG['SUBSTANCES'][substance]
        base_price = sub_data['base_price']
        
        price = int(base_price * (purity / 100) * quantity)
        
        text += f"{sub_data['name']}\n├ Количество: {quantity}г\n├ Чистота: {purity:.1f}%\n└ Цена: ${price:,}\n\n"
        
        buttons.append([InlineKeyboardButton(
            text=f"Продать {quantity}г (${price:,})",
            callback_data=f"sell_{substance}"
        )])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="market_main")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)


@market_router.callback_query(F.data.startswith("sell_"))
async def sell_product(callback: CallbackQuery):
    substance = callback.data.replace("sell_", "")
    user_id = callback.from_user.id
    
    products = await get_inventory(user_id, 'product')
    product = next((p for p in products if p['item_id'] == substance), None)
    
    if not product:
        await callback.answer("❌ Товар не найден!")
        return
    
    quantity = product['quantity']
    purity = product.get('metadata', {}).get('purity', 75)
    
    sub_data = GAME_CONFIG['SUBSTANCES'][substance]
    base_price = sub_data['base_price']
    total_price = int(base_price * (purity / 100) * quantity)
    
    await remove_from_inventory(user_id, 'product', substance, quantity)
    
    user = await get_user(user_id)
    new_money = user['money_dirty'] + total_price
    new_sold = user['total_sold'] + total_price
    
    await update_user(user_id, money_dirty=new_money, total_sold=new_sold)
    
    await callback.answer(f"✅ Продано за ${total_price:,}!", show_alert=True)
    await market_sell(callback)


# ========== PROPERTY HANDLER ==========
property_router = Router()

@property_router.message(Command("properties"))
@property_router.callback_query(F.data == "property_main")
async def property_main(event):
    user_id = event.from_user.id if isinstance(event, CallbackQuery) else event.from_user.id
    user = await get_user(user_id)
    
    # Получаем недвижимость пользователя
    async with pool.acquire() as conn:
        properties = await conn.fetch('''
            SELECT * FROM properties WHERE user_id = $1
        ''', user_id)
    
    text = f"""
🏠 <b>НЕДВИЖИМОСТЬ</b>

💰 Твои чистые: ${user['money_clean']:,}

<b>ТВОЯ НЕДВИЖИМОСТЬ:</b>
"""
    
    if properties:
        total_value = 0
        total_income = 0
        for prop in properties:
            prop_data = GAME_CONFIG['PROPERTIES'].get(prop['property_type'], {})
            text += f"\n{prop_data.get('name', prop['property_type'])}\n"
            text += f"├ Стоимость: ${prop['current_value']:,}\n"
            text += f"└ Доход: ${prop['income_daily']:,}/день\n"
            total_value += prop['current_value']
            total_income += prop['income_daily']
        
        text += f"\n<b>Всего:</b> ${total_value:,}\n<b>Доход/день:</b> ${total_income:,}"
    else:
        text += "\n❌ У тебя нет недвижимости\n\n<b>ДОСТУПНО ДЛЯ ПОКУПКИ:</b>\n"
        
        for prop_id, prop_data in GAME_CONFIG['PROPERTIES'].items():
            if 'bar' in prop_id or 'casino' in prop_id or 'nightclub' in prop_id or 'bank' in prop_id:
                text += f"\n{prop_data['name']}\n├ Цена: ${prop_data['price']:,}\n"
                if prop_data.get('type') == 'laundry':
                    text += f"├ Отмыв: до ${prop_data['capacity']:,}\n└ Комиссия: {int((1-prop_data['rate'])*100)}%\n"
                continue
            
            text += f"\n{prop_data['name']}\n├ Цена: ${prop_data['price']:,}\n├ Слоты: +{prop_data['slots']}\n└ Доход: ${prop_data['income']:,}/день\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍺 Бар ($300k)", callback_data="buy_property_bar")],
        [InlineKeyboardButton(text="🏭 Склад ($200k)", callback_data="buy_property_warehouse")],
        [InlineKeyboardButton(text="🎰 Казино ($2M)", callback_data="buy_property_casino")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


@property_router.callback_query(F.data.startswith("buy_property_"))
async def buy_property(callback: CallbackQuery):
    property_type = callback.data.replace("buy_property_", "")
    user = await get_user(callback.from_user.id)
    
    prop_data = GAME_CONFIG['PROPERTIES'].get(property_type)
    if not prop_data:
        await callback.answer("❌ Недвижимость не найдена!")
        return
    
    price = prop_data['price']
    
    if user['money_clean'] < price:
        await callback.answer(f"❌ Нужно ${price:,} чистых!", show_alert=True)
        return
    
    # Списываем деньги
    await update_user(callback.from_user.id, money_clean=user['money_clean'] - price)
    
    # Добавляем недвижимость
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO properties (user_id, property_type, region_id, purchase_price, current_value, income_daily)
            VALUES ($1, $2, 1, $3, $3, $4)
        ''', callback.from_user.id, property_type, price, prop_data.get('income', 0))
    
    await callback.answer(f"✅ {prop_data['name']} куплен!", show_alert=True)
    await property_main(callback)


# ========== LAUNDRY HANDLER ==========
laundry_router = Router()

@laundry_router.message(Command("laundry"))
@laundry_router.callback_query(F.data == "laundry_main")
async def laundry_main(event):
    user_id = event.from_user.id if isinstance(event, CallbackQuery) else event.from_user.id
    user = await get_user(user_id)
    
    # Получаем недвижимость для отмыва
    async with pool.acquire() as conn:
        laundry_props = await conn.fetch('''
            SELECT * FROM properties 
            WHERE user_id = $1 AND property_type IN ('bar', 'casino', 'nightclub', 'bank')
        ''', user_id)
    
    text = f"""
💸 <b>ОТМЫВ ДЕНЕГ</b>

💰 Грязные деньги: <b>${user['money_dirty']:,}</b>
💎 Чистые деньги: <b>${user['money_clean']:,}</b>

<b>ДОСТУПНЫЕ СПОСОБЫ:</b>

🚶 Улица (комиссия 50%)
└ Макс: $10,000 за раз
"""
    
    buttons = [[InlineKeyboardButton(text="💸 Отмыть на улице", callback_data="laundry_street")]]
    
    if laundry_props:
        text += "\n<b>ТВОИ ЗАВЕДЕНИЯ:</b>\n"
        for prop in laundry_props:
            prop_data = GAME_CONFIG['PROPERTIES'].get(prop['property_type'], {})
            commission = int((1 - prop_data.get('rate', 0.5)) * 100)
            text += f"\n{prop_data['name']}\n├ Комиссия: {commission}%\n└ Лимит: ${prop_data.get('capacity', 0):,}\n"
            
            buttons.append([InlineKeyboardButton(
                text=f"Отмыть через {prop_data['name']}",
                callback_data=f"laundry_use_{prop['property_type']}"
            )])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


@laundry_router.callback_query(F.data == "laundry_street")
async def laundry_street(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    
    if user['money_dirty'] < 1000:
        await callback.answer("❌ Минимум $1,000 для отмыва!")
        return
    
    amount = min(user['money_dirty'], 10000)
    clean_amount = int(amount * 0.5)
    
    new_dirty = user['money_dirty'] - amount
    new_clean = user['money_clean'] + clean_amount
    new_laundered = user['total_laundered'] + clean_amount
    
    await update_user(
        callback.from_user.id,
        money_dirty=new_dirty,
        money_clean=new_clean,
        total_laundered=new_laundered
    )
    
    await callback.answer(f"✅ Отмыто ${clean_amount:,} (комиссия 50%)", show_alert=True)
    await laundry_main(callback)


@laundry_router.callback_query(F.data.startswith("laundry_use_"))
async def laundry_use_property(callback: CallbackQuery):
    property_type = callback.data.replace("laundry_use_", "")
    user = await get_user(callback.from_user.id)
    
    prop_data = GAME_CONFIG['PROPERTIES'].get(property_type)
    if not prop_data:
        await callback.answer("❌ Заведение не найдено!")
        return
    
    rate = prop_data.get('rate', 0.5)
    capacity = prop_data.get('capacity', 50000)
    
    if user['money_dirty'] < 1000:
        await callback.answer("❌ Минимум $1,000 для отмыва!")
        return
    
    amount = min(user['money_dirty'], capacity)
    clean_amount = int(amount * rate)
    
    new_dirty = user['money_dirty'] - amount
    new_clean = user['money_clean'] + clean_amount
    new_laundered = user['total_laundered'] + clean_amount
    
    await update_user(
        callback.from_user.id,
        money_dirty=new_dirty,
        money_clean=new_clean,
        total_laundered=new_laundered
    )
    
    commission = int((1 - rate) * 100)
    await callback.answer(f"✅ Отмыто ${clean_amount:,} (комиссия {commission}%)", show_alert=True)
    await laundry_main(callback)


# ========== CARTEL HANDLER ==========
cartel_router = Router()

@cartel_router.message(Command("cartel"))
@cartel_router.callback_query(F.data == "cartel_main")
async def cartel_main(event):
    user_id = event.from_user.id if isinstance(event, CallbackQuery) else event.from_user.id
    
    # Проверяем членство в картеле
    async with pool.acquire() as conn:
        membership = await conn.fetchrow('''
            SELECT c.*, cm.rank
            FROM cartel_members cm
            JOIN cartels c ON cm.cartel_id = c.id
            WHERE cm.user_id = $1
        ''', user_id)
    
    if membership:
        text = f"""
🏰 <b>{membership['name']}</b>

👑 Лидер: ID {membership['leader_id']}
👥 Участников: {membership['member_count']}
🏆 Респект: {membership['respect']:,}
🎯 Уровень: {membership['level']}

💰 <b>КАЗНА:</b>
├ Грязные: ${membership['treasury_dirty']:,}
└ Чистые: ${membership['treasury_clean']:,}

👤 <b>Твой ранг:</b> {membership['rank']}

📝 {membership['description'] or 'Нет описания'}
        """
        
        buttons = [
            [InlineKeyboardButton(text="💰 Пополнить казну", callback_data="cartel_donate")],
            [InlineKeyboardButton(text="👥 Участники", callback_data="cartel_members")],
            [InlineKeyboardButton(text="🗺 Территории", callback_data="cartel_territories")]
        ]
        
        if membership['rank'] == 'leader':
            buttons.append([InlineKeyboardButton(text="⚙️ Управление", callback_data="cartel_manage")])
        
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")])
        
    else:
        text = """
🏰 <b>КАРТЕЛИ</b>

У тебя нет картеля!

<b>ВОЗМОЖНОСТИ КАРТЕЛЯ:</b>
├ Общая казна
├ Контроль территорий
├ Совместные варки
├ PVP войны
└ Бонусы к доходу

💰 Создание картеля: $100,000 чистых
        """
        
        buttons = [
            [InlineKeyboardButton(text="➕ Создать картель", callback_data="cartel_create")],
            [InlineKeyboardButton(text="🔍 Найти картель", callback_data="cartel_search")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
        ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


@cartel_router.callback_query(F.data == "cartel_create")
async def cartel_create(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    
    if user['money_clean'] < 100000:
        await callback.answer("❌ Нужно $100,000 чистых для создания картеля!", show_alert=True)
        return
    
    text = """
➕ <b>СОЗДАТЬ КАРТЕЛЬ</b>

Придумай название для своего картеля.

Используй команду:
/create_cartel Название

Например:
/create_cartel Берломосковский Синдикат

💰 Стоимость: $100,000
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="cartel_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@cartel_router.message(Command("create_cartel"))
async def create_cartel_command(message: Message):
    user = await get_user(message.from_user.id)
    
    if user['money_clean'] < 100000:
        await message.answer("❌ Нужно $100,000 чистых!")
        return
    
    # Получаем название
    cartel_name = message.text.replace("/create_cartel", "").strip()
    
    if not cartel_name or len(cartel_name) < 3:
        await message.answer("❌ Название должно быть минимум 3 символа!")
        return
    
    if len(cartel_name) > 50:
        await message.answer("❌ Название слишком длинное (макс 50 символов)!")
        return
    
    # Проверяем что не в картеле
    async with pool.acquire() as conn:
        existing = await conn.fetchrow('''
            SELECT 1 FROM cartel_members WHERE user_id = $1
        ''', message.from_user.id)
        
        if existing:
            await message.answer("❌ Ты уже в картеле! Сначала выйди из него.")
            return
        
        # Проверяем уникальность названия
        name_taken = await conn.fetchrow('''
            SELECT 1 FROM cartels WHERE name = $1
        ''', cartel_name)
        
        if name_taken:
            await message.answer("❌ Это название уже занято!")
            return
        
        # Создаем картель
        cartel = await conn.fetchrow('''
            INSERT INTO cartels (name, leader_id, description)
            VALUES ($1, $2, 'Новый картель')
            RETURNING id
        ''', cartel_name, message.from_user.id)
        
        # Добавляем создателя
        await conn.execute('''
            INSERT INTO cartel_members (cartel_id, user_id, rank)
            VALUES ($1, $2, 'leader')
        ''', cartel['id'], message.from_user.id)
        
        # Списываем деньги
        await update_user(message.from_user.id, money_clean=user['money_clean'] - 100000)
    
    await message.answer(f"""
✅ <b>Картель создан!</b>

🏰 <b>{cartel_name}</b>

Ты теперь лидер картеля!
Используй /cartel для управления.
    """)


# ========== PVP HANDLER ==========
pvp_router = Router()

@pvp_router.message(Command("pvp"))
@pvp_router.callback_query(F.data == "pvp_main")
async def pvp_main(event):
    text = """
⚔️ <b>PVP АРЕНА</b>

Сражайся за контроль над районами Берломосквы!

<b>РЕГИОНЫ:</b>
"""
    
    for region in GAME_CONFIG['REGIONS']:
        text += f"\n{region['name']}\n├ Tier: {region['tier']}\n├ Опасность: {region['danger']}%\n└ Статус: 🟢 Свободен\n"
    
    text += "\n💡 Контроль региона дает бонусы к доходу!"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Атаковать район", callback_data="pvp_attack_select")],
        [InlineKeyboardButton(text="🛡 Защита", callback_data="pvp_defense")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


@pvp_router.callback_query(F.data == "pvp_attack_select")
async def pvp_attack_select(callback: CallbackQuery):
    text = """
🎯 <b>ВЫБЕРИ РЕГИОН ДЛЯ АТАКИ</b>

Атакуй районы чтобы установить контроль!

<b>ДОСТУПНО:</b>
"""
    
    buttons = []
    
    for i, region in enumerate(GAME_CONFIG['REGIONS'][:4]):  # Первые 4 региона
        text += f"\n{region['name']}\n├ Сложность: {region['tier']}⭐\n└ Опасность: {region['danger']}%\n"
        
        buttons.append([InlineKeyboardButton(
            text=f"Атаковать {region['name']}",
            callback_data=f"pvp_attack_{i+1}"
        )])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="pvp_main")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)


@pvp_router.callback_query(F.data.startswith("pvp_attack_"))
async def pvp_attack(callback: CallbackQuery):
    region_id = int(callback.data.replace("pvp_attack_", ""))
    region = GAME_CONFIG['REGIONS'][region_id - 1]
    
    user = await get_user(callback.from_user.id)
    factory = await get_factory(callback.from_user.id)
    
    # Расчет силы атаки
    attack_power = user['level'] * 10
    
    # Бонус от персонала
    staff = factory.get('staff', {})
    for staff_id, staff_data in staff.items():
        if 'guard' in staff_id:
            staff_info = GAME_CONFIG['STAFF'].get(staff_id, {})
            attack_power += staff_info.get('pvp_defense', 0)
    
    # Защита региона
    defense_power = region['tier'] * 20 + region['danger']
    
    # Бой
    success_chance = min(90, max(10, (attack_power / defense_power) * 50))
    
    if random.random() * 100 < success_chance:
        # Победа
        loot_money = random.randint(5000, 20000) * region['tier']
        loot_respect = random.randint(10, 50) * region['tier']
        
        await update_user(
            callback.from_user.id,
            money_dirty=user['money_dirty'] + loot_money,
            respect=user['respect'] + loot_respect
        )
        
        text = f"""
🎉 <b>ПОБЕДА!</b>

Ты захватил {region['name']}!

<b>ТРОФЕИ:</b>
├ Деньги: ${loot_money:,}
└ Респект: +{loot_respect}

💪 Сила атаки: {attack_power}
🛡 Защита врага: {defense_power}
        """
    else:
        # Поражение
        lost_money = random.randint(1000, 5000)
        
        await update_user(
            callback.from_user.id,
            money_dirty=max(0, user['money_dirty'] - lost_money)
        )
        
        text = f"""
💥 <b>ПОРАЖЕНИЕ!</b>

Атака на {region['name']} провалилась!

<b>ПОТЕРИ:</b>
└ Деньги: -${lost_money:,}

💪 Твоя сила: {attack_power}
🛡 Защита врага: {defense_power}

Прокачай персонал и попробуй снова!
        """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Атаковать снова", callback_data="pvp_attack_select")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="pvp_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)


# ========== SECURITY HANDLER ==========
security_router = Router()

@security_router.message(Command("security"))
@security_router.callback_query(F.data == "security_main")
async def security_main(event):
    user_id = event.from_user.id if isinstance(event, CallbackQuery) else event.from_user.id
    user = await get_user(user_id)
    
    heat_status = "🟢 Низкий" if user['heat'] < 30 else "🟡 Средний" if user['heat'] < 70 else "🔴 ВЫСОКИЙ"
    
    text = f"""
👮 <b>БЕЗОПАСНОСТЬ</b>

⚠️ Розыск: <b>{user['heat']}/100</b> {heat_status}

<b>ДЕЙСТВИЯ:</b>

💰 <b>Взятка копам</b> — $10,000
└ -20 Heat

<i>При Heat 100 — арест на 24 часа!</i>

💡 Купи камеры и сигнализацию в /market
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Дать взятку ($10k)", callback_data="security_bribe")],
        [InlineKeyboardButton(text="🛒 Купить защиту", callback_data="market_equipment")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


@security_router.callback_query(F.data == "security_bribe")
async def security_bribe(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    price = 10000
    
    if user['money_clean'] < price:
        await callback.answer("❌ Недостаточно чистых денег!", show_alert=True)
        return
    
    new_money = user['money_clean'] - price
    new_heat = max(0, user['heat'] - 20)
    
    await update_user(callback.from_user.id, money_clean=new_money, heat=new_heat)
    
    await callback.answer(f"✅ Взятка дана! Heat: {new_heat}/100", show_alert=True)
    await security_main(callback)


# ========== LEADERBOARD ==========
@market_router.message(Command("leaderboard"))
@market_router.callback_query(F.data == "leaderboard")
async def leaderboard(event):
    leaders = await get_leaderboard('money', 10)
    
    text = "<b>🏆 ТОП-10 БОССОВ</b>\n\n"
    
    medals = ["🥇", "🥈", "🥉"] + ["📍"] * 7
    
    for i, leader in enumerate(leaders):
        total_money = leader['money_clean'] + leader['money_dirty']
        text += f"{medals[i]} <b>{leader['cartel_name']}</b>\n"
        text += f"├ Респект: {leader['respect']:,}\n"
        text += f"├ Капитал: ${total_money:,}\n"
        text += f"└ Сварено: {leader['total_cooked']:,}г\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


# Экспортируем все роутеры
router = market_router
