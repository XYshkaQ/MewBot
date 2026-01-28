# -*- coding: utf-8 -*-
"""
Стартовый хендлер - команды /start, /help, /stats, /inventory
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_manager import get_user, update_user, get_inventory
from config.settings import GAME_CONFIG, TELEGRAPH_BASE

router = Router()

@router.message(Command("start"))
@router.callback_query(F.data == "back_to_start")
async def cmd_start(event):
    """Главное меню бота"""
    message = event.message if isinstance(event, CallbackQuery) else event
    user_id = event.from_user.id
    
    user = await get_user(user_id)
    
    if not user:
        # Регистрация нового пользователя
        from database.db_manager import register_user
        await register_user(user_id)
        user = await get_user(user_id)
        
        welcome_text = """
🔥 <b>Добро пожаловать в MewBot Cartel!</b>

Ты теперь в Берломоскве — городе, где смешались Берлин и Москва, а законы пишут картели.

💰 <b>СТАРТОВЫЙ КАПИТАЛ:</b>
├ Грязные деньги: $5,000
├ Чистые деньги: $1,000
└ Гараж в Кремлёвских Гетто

📚 <b>С ЧЕГО НАЧАТЬ?</b>
1. Купи прекурсоры в /market
2. Начни первую варку через /cook_menu
3. Продай товар и отмой деньги
4. Прокачивай завод и картель!

⚠️ Следи за Heat (розыск) — при 100 сядешь на сутки!

Удачи! 💎
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Гайд для новичков", url=TELEGRAPH_BASE)],
            [InlineKeyboardButton(text="🚀 Начать игру", callback_data="back_to_start")]
        ])
        
        await message.answer(welcome_text, reply_markup=keyboard)
        return
    
    # Статус игрока
    total_money = user['money_clean'] + user['money_dirty']
    heat_status = "🟢" if user['heat'] < 30 else "🟡" if user['heat'] < 70 else "🔴"
    
    status_text = f"""
🏠 <b>ГЛАВНОЕ МЕНЮ</b>

👤 <b>{user['cartel_name']}</b>
🎯 Уровень: {user['level']} | ⭐ Респект: {user['respect']:,}

💰 <b>ДЕНЬГИ:</b>
├ Грязные: ${user['money_dirty']:,}
├ Чистые: ${user['money_clean']:,}
└ Всего: ${total_money:,}

{heat_status} Heat: {user['heat']}/100
{'⚠️ Высокий розыск! Менты на хвосте!' if user['heat'] > 80 else ''}

📊 <b>СТАТИСТИКА:</b>
├ Сварено: {user['total_cooked']:,}г
├ Продано: ${user['total_sold']:,}
└ Отмыто: ${user['total_laundered']:,}

<i>Выбери действие:</i>
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚗️ Варка", callback_data="cook_menu"),
            InlineKeyboardButton(text="🏭 Завод", callback_data="factory_main")
        ],
        [
            InlineKeyboardButton(text="🛒 Рынок", callback_data="market_main"),
            InlineKeyboardButton(text="📦 Инвентарь", callback_data="inventory_menu")
        ],
        [
            InlineKeyboardButton(text="💸 Отмыв", callback_data="laundry_main"),
            InlineKeyboardButton(text="🏠 Недвижимость", callback_data="property_main")
        ],
        [
            InlineKeyboardButton(text="🏰 Картель", callback_data="cartel_main"),
            InlineKeyboardButton(text="⚔️ PVP", callback_data="pvp_main")
        ],
        [
            InlineKeyboardButton(text="👮 Безопасность", callback_data="security_main"),
            InlineKeyboardButton(text="🏆 Топ", callback_data="leaderboard")
        ],
        [
            InlineKeyboardButton(text="📖 Гайд", url=TELEGRAPH_BASE),
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help_menu")
        ]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(status_text, reply_markup=keyboard)
        await event.answer()
    else:
        await message.answer(status_text, reply_markup=keyboard)


@router.message(Command("help"))
@router.callback_query(F.data == "help_menu")
async def cmd_help(event):
    """Справка по командам"""
    message = event.message if isinstance(event, CallbackQuery) else event
    
    help_text = """
📚 <b>СПРАВКА ПО КОМАНДАМ</b>

<b>🎮 ОСНОВНЫЕ:</b>
/start - Главное меню
/help - Эта справка
/stats - Твоя статистика

<b>⚗️ ПРОИЗВОДСТВО:</b>
/cook_menu - Выбрать вещество и начать варку
/control_panel - Управление активной варкой
/factory - Информация о заводе

<b>💰 ЭКОНОМИКА:</b>
/market - Купить/продать товар и оборудование
/inventory - Твой инвентарь
/laundry - Отмыв грязных денег
/properties - Недвижимость

<b>🏰 СОЦИАЛЬНОЕ:</b>
/cartel - Управление картелем
/pvp - PVP арена
/leaderboard - Топ игроков

<b>🛡 БЕЗОПАСНОСТЬ:</b>
/security - Снизить Heat (розыск)

<b>💎 ДОНАТ:</b>
/donate - Премиум преимущества

📖 <b>Полный гайд:</b>
{TELEGRAPH_BASE}

💡 <b>Совет:</b> Начни с покупки прекурсоров в /market, затем запусти варку через /cook_menu
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(help_text, reply_markup=keyboard)
        await event.answer()
    else:
        await message.answer(help_text, reply_markup=keyboard)


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Подробная статистика игрока"""
    user = await get_user(message.from_user.id)
    
    # Расчет прогресса до следующего уровня
    next_level_exp = user['level'] * 1000
    current_exp = user['experience']
    progress = min(100, int((current_exp / next_level_exp) * 100))
    progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
    
    # Статистика по взрывам/арестам
    explosions = user.get('explosions', 0)
    busts = user.get('busts', 0)
    deaths = user.get('deaths_caused', 0)
    
    total_money = user['money_clean'] + user['money_dirty']
    
    stats_text = f"""
📊 <b>СТАТИСТИКА</b>

👤 <b>{user['cartel_name']}</b>

<b>🎯 ПРОГРЕСС:</b>
├ Уровень: {user['level']}
├ Опыт: {current_exp:,}/{next_level_exp:,}
└ {progress_bar} {progress}%

<b>💰 ФИНАНСЫ:</b>
├ Грязные деньги: ${user['money_dirty']:,}
├ Чистые деньги: ${user['money_clean']:,}
├ Всего капитал: ${total_money:,}
└ Респект: ⭐ {user['respect']:,}

<b>⚗️ ПРОИЗВОДСТВО:</b>
├ Всего сварено: {user['total_cooked']:,}г
├ Всего продано: ${user['total_sold']:,}
└ Всего отмыто: ${user['total_laundered']:,}

<b>⚠️ ИНЦИДЕНТЫ:</b>
├ Взрывы: 💥 {explosions}
├ Аресты: 👮 {busts}
└ Смерти клиентов: ☠️ {deaths}

<b>🎖 ДОСТИЖЕНИЯ:</b>
{'🏆 Легенда криминала' if user['respect'] > 10000 else '💎 Опытный торговец' if user['respect'] > 5000 else '⭐ Начинающий босс' if user['respect'] > 1000 else '🌱 Новичок'}

<b>👮 РОЗЫСК:</b>
Heat: {user['heat']}/100 {'🔴 КРИТИЧНО!' if user['heat'] > 80 else '🟡 Средний' if user['heat'] > 40 else '🟢 Низкий'}
    """
    
    await message.answer(stats_text)


@router.message(Command("inventory"))
@router.callback_query(F.data == "inventory_menu")
async def cmd_inventory(event):
    """Инвентарь пользователя"""
    message = event.message if isinstance(event, CallbackQuery) else event
    user_id = event.from_user.id
    
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
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 В магазин", callback_data="market_main")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
        await event.answer()
    else:
        await message.answer(text, reply_markup=keyboard)


@router.message(Command("tutorial"))
async def cmd_tutorial(message: Message):
    """Ссылка на полный гайд"""
    text = f"""
📖 <b>ПОЛНЫЙ ГАЙД ПО ИГРЕ</b>

Изучи подробное руководство по всем механикам:
• Производство и варка
• Вещества и оборудование
• Экономика и отмыв денег
• Картели и PVP
• Советы для новичков и профи

👉 <a href="{TELEGRAPH_BASE}">Открыть гайд</a>
    """
    
    await message.answer(text, disable_web_page_preview=True)


@router.message(Command("donate"))
async def cmd_donate(message: Message):
    """Информация о донате"""
    text = """
💎 <b>ПРЕМИУМ ПРЕИМУЩЕСТВА</b>

<b>🎭 Золотая Маска (100 ⭐)</b>
├ Премиум статус на 30 дней
├ +20% скорость варки
├ Автосброс давления
├ Эксклюзивная иконка
└ Приоритетная поддержка

<b>⚖️ РАЗОВЫЕ БУСТЫ:</b>

👔 Звонок адвокату (50 ⭐)
└ Мгновенный выход из тюрьмы

📦 Экспресс-доставка (20 ⭐)
└ Мгновенная доставка прекурсоров

💨 Ускорение (25 ⭐)
└ +100% скорость варки на 1 час

🔄 Воскрешение (150 ⭐)
└ Восстановление после взрыва

🚨 Сброс Heat (60 ⭐)
└ Обнуление розыска

<b>🎨 СКИНЫ (30-50 ⭐):</b>
├ Breaking Bad
├ Narcos
└ Cyberpunk

<i>Покупка через Telegram Stars</i>
<i>Функция в разработке</i>
    """
    
    await message.answer(text)
    
