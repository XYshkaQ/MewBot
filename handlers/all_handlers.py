# -*- coding: utf-8 -*-
"""
Все остальные хендлеры в одном файле
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_manager import get_user, get_inventory, add_to_inventory, remove_from_inventory, update_user, get_leaderboard
from config.settings import GAME_CONFIG, DONATE_PRICES
import random

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
👥 Персонал — наймы работников
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
├ Псевдоэфедрин: $2,000
├ Красный фосфор: $2,500
└ Катализатор: $1,000
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить x10 Стартовый набор ($5,000)", callback_data="buy_starter_pack")],
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
    
    # Списываем деньги
    await update_user(callback.from_user.id, money_clean=user['money_clean'] - price)
    
    # Выдаем прекурсоры
    precursors = {
        'бензол': 10,
        'метиламин': 10,
        'ацетон': 10,
        'катализатор': 5
    }
    
    for prec, amount in precursors.items():
        await add_to_inventory(callback.from_user.id, 'precursor', prec, amount)
    
    await callback.answer("✅ Стартовый набор куплен!")
    await market_precursors(callback)


@market_router.callback_query(F.data == "market_sell")
async def market_sell(callback: CallbackQuery):
    user_id = callback.from_user.id
    products = await get_inventory(user_id, 'product')
    
    if not products:
        await callback.answer("❌ У тебя нет товара для продажи!", show_alert=True)
        return
    
    text = "<b>💰 ПРОДАТЬ ТОВАР</b>\n\nВыбери что продать:\n"
    buttons = []
    
    for product in products:
        substance = product['item_id']
        quantity = product['quantity']
        purity = product.get('metadata', {}).get('purity', 75)
        
        sub_data = GAME_CONFIG['SUBSTANCES'][substance]
        base_price = sub_data['base_price']
        
        # Цена зависит от чистоты
        price = int(base_price * (purity / 100) * quantity)
        
        text += f"\n{sub_data['name']}\n├ Количество: {quantity}г\n├ Чистота: {purity:.1f}%\n└ Цена: ${price:,}\n"
        
        buttons.append([InlineKeyboardButton(
            text=f"Продать {sub_data['name']} (${price:,})",
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
    
    # Удаляем товар
    await remove_from_inventory(user_id, 'product', substance, quantity)
    
    # Выдаем грязные деньги
    user = await get_user(user_id)
    new_money = user['money_dirty'] + total_price
    new_sold = user['total_sold'] + total_price
    
    await update_user(user_id, money_dirty=new_money, total_sold=new_sold)
    
    await callback.answer(f"✅ Продано за ${total_price:,}!", show_alert=True)
    await market_sell(callback)


# ========== CARTEL HANDLER ==========
cartel_router = Router()

@cartel_router.message(Command("cartel"))
@cartel_router.callback_query(F.data == "cartel_main")
async def cartel_main(event):
    text = """
🏰 <b>КАРТЕЛЬ</b>

Создай свою организацию или вступи в существующую!

<b>ВОЗМОЖНОСТИ:</b>
├ Контроль регионов
├ Общий бюджет
├ Совместные варки
└ PVP битвы

<i>В разработке...</i>
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать Картель", callback_data="cartel_create")],
        [InlineKeyboardButton(text="🔍 Найти Картель", callback_data="cartel_search")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


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
        text += f"\n{region['name']}\n├ Tier: {region['tier']}\n├ Опасность: {region['danger']}%\n└ Статус: Свободен\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Атаковать район", callback_data="pvp_attack")],
        [InlineKeyboardButton(text="🛡 Защита", callback_data="pvp_defense")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


# ========== PROPERTY HANDLER ==========
property_router = Router()

@property_router.message(Command("properties"))
@property_router.callback_query(F.data == "property_main")
async def property_main(event):
    text = """
🏠 <b>НЕДВИЖИМОСТЬ</b>

Покупай недвижимость для:
├ Дополнительных слотов производства
├ Отмыва денег
└ Пассивного дохода

<b>ДОСТУПНО:</b>
"""
    
    for prop_id, prop_data in GAME_CONFIG['PROPERTIES'].items():
        if 'bar' in prop_id or 'casino' in prop_id:
            continue
        
        text += f"\n{prop_data['name']}\n├ Цена: ${prop_data['price']:,}\n├ Слоты: {prop_data['slots']}\n└ Доход: ${prop_data['income']:,}/день\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Мои объекты", callback_data="my_properties")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


# ========== LAUNDRY HANDLER ==========
laundry_router = Router()

@laundry_router.message(Command("laundry"))
@laundry_router.callback_query(F.data == "laundry_main")
async def laundry_main(event):
    user_id = event.from_user.id
    user = await get_user(user_id)
    
    text = f"""
💸 <b>ОТМЫВ ДЕНЕГ</b>

💰 Грязные деньги: <b>${user['money_dirty']:,}</b>
💎 Чистые деньги: <b>${user['money_clean']:,}</b>

<b>СПОСОБЫ ОТМЫВА:</b>

🍺 <b>Бар "Кристалл"</b>
├ Комиссия: 15%
├ Лимит: $50,000
└ Цена: $300,000

🎰 <b>Казино</b>
├ Комиссия: 25%
├ Лимит: $500,000
└ Цена: $2,000,000

<i>Купи недвижимость для отмыва через /properties</i>
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Отмыть через улицу (50%)", callback_data="laundry_street")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
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
    
    # Отмываем 50%
    amount = min(user['money_dirty'], 10000)  # Макс 10k за раз
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


# ========== SECURITY HANDLER ==========
security_router = Router()

@security_router.message(Command("security"))
@security_router.callback_query(F.data == "security_main")
async def security_main(event):
    user_id = event.from_user.id
    user = await get_user(user_id)
    
    heat_status = "🟢 Низкий" if user['heat'] < 30 else "🟡 Средний" if user['heat'] < 70 else "🔴 ВЫСОКИЙ"
    
    text = f"""
👮 <b>БЕЗОПАСНОСТЬ</b>

⚠️ Розыск: <b>{user['heat']}/100</b> {heat_status}

<b>ДЕЙСТВИЯ:</b>

💰 <b>Взятка копам</b> — $10,000
└ -20 Heat

🎥 <b>Камеры наблюдения</b> — $2,000
└ Снижают Heat от варки

🚪 <b>Бронированная дверь</b> — $25,000
└ Защита от рейдов

<i>При Heat 100 — арест на 24 часа!</i>
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Дать взятку ($10k)", callback_data="security_bribe")],
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
