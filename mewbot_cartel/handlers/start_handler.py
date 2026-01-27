# -*- coding: utf-8 -*-
"""
Хендлер стартовых команд
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_manager import get_user, create_user
from config.settings import GAME_CONFIG

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    user = await get_user(user_id)
    
    if not user:
        # Новый пользователь
        user = await create_user(user_id, username)
        
        welcome_text = f"""
🔥 <b>ДОБРО ПОЖАЛОВАТЬ В БЕРЛОМОСКВУ</b> 🔥

Ты входишь в игру. Твоя цель — построить империю производства и стать легендой подпольного мира.

💰 Стартовый капитал:
├ Грязные: ${user['money_dirty']:,}
└ Чистые: ${user['money_clean']:,}

🏭 Тебе выдан стартовый <b>Гараж в Гетто</b>
📍 Локация: <b>{GAME_CONFIG['REGIONS'][0]['name']}</b>

<b>Что делать дальше?</b>
1. Изучи /tutorial — гайд для новичков
2. Построй первую варку через /cook_menu
3. Нанимай персонал в /market
4. Развивай картель через /cartel

<i>Помни: каждое решение может стоить тебе всего. Или принести миллионы.</i>

⚠️ Уровень розыска: <b>{user['heat']}/100</b>
🎯 Уровень: <b>{user['level']}</b>
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Обучение", callback_data="tutorial")],
            [InlineKeyboardButton(text="🏭 Мой Завод", callback_data="factory_main")],
            [InlineKeyboardButton(text="⚗️ Начать Варку", callback_data="cook_menu")],
            [InlineKeyboardButton(text="🛒 Магазин", callback_data="market_main")]
        ])
        
        await message.answer(welcome_text, reply_markup=keyboard)
    
    else:
        # Существующий пользователь
        status_emoji = "🟢" if not user['in_jail'] else "🔴"
        
        main_text = f"""
{status_emoji} <b>{user['cartel_name']}</b>

👤 Босс: @{username}
🎯 Уровень: <b>{user['level']}</b> | 🏆 Респект: <b>{user['respect']:,}</b>

💰 <b>ФИНАНСЫ:</b>
├ Грязные: <b>${user['money_dirty']:,}</b>
└ Чистые: <b>${user['money_clean']:,}</b>

⚠️ Розыск: <b>{user['heat']}/100</b> {'🚨' if user['heat'] > 70 else '✅' if user['heat'] < 30 else '⚠️'}

📊 <b>СТАТИСТИКА:</b>
├ Сварено: {user['total_cooked']:,} г
├ Продано: ${user['total_sold']:,}
├ Отмыто: ${user['total_laundered']:,}
└ Взрывов: {user['explosions']} 💥

<i>Выбери действие:</i>
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏭 Завод", callback_data="factory_main"),
                InlineKeyboardButton(text="⚗️ Варить", callback_data="cook_menu")
            ],
            [
                InlineKeyboardButton(text="🛒 Магазин", callback_data="market_main"),
                InlineKeyboardButton(text="💸 Отмыв", callback_data="laundry_main")
            ],
            [
                InlineKeyboardButton(text="🏰 Картель", callback_data="cartel_main"),
                InlineKeyboardButton(text="⚔️ PVP", callback_data="pvp_main")
            ],
            [
                InlineKeyboardButton(text="🏆 Лидеры", callback_data="leaderboard"),
                InlineKeyboardButton(text="👮 Защита", callback_data="security_main")
            ],
            [InlineKeyboardButton(text="💎 Донат", callback_data="donate_menu")]
        ])
        
        await message.answer(main_text, reply_markup=keyboard)


@router.callback_query(F.data == "tutorial")
async def tutorial_callback(callback: CallbackQuery):
    """Обучение"""
    tutorial_text = """
📚 <b>ГАЙД ДЛЯ НОВИЧКОВ</b>

<b>1. ПРОИЗВОДСТВО</b>
├ Выбери вещество в /cook_menu
├ Следи за температурой и давлением
├ Чем выше чистота — тем выше цена
└ Риск взрыва зависит от вещества

<b>2. ОБОРУДОВАНИЕ</b>
├ Реактор — основа производства
├ Центрифуга — повышает чистоту
├ Фильтры — расходники, нужно менять
└ Вентиляция — снижает токсичность

<b>3. ФИНАНСЫ</b>
├ <i>Грязные деньги</i> — от продажи товара
├ <i>Чистые деньги</i> — после отмыва
└ Крутое оборудование можно купить только за чистые

<b>4. РОЗЫСК (HEAT)</b>
├ Растет при варке и продаже
├ При 100 — арест на 24 часа
├ Снижай через /security
└ Или плати взятки ментам

<b>5. КАРТЕЛЬ</b>
├ Создай или вступи в картель
├ Контролируй регионы города
├ Получай пассивный доход
└ Воюй с другими картелями

<b>📖 Полный гайд:</b>
https://telegra.ph/MewBot-Cartel-Polnoe-rukovodstvo-01-27

<i>Удачи в Берломоскве!</i>
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏭 К Заводу", callback_data="factory_main")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    await callback.message.edit_text(tutorial_text, reply_markup=keyboard)


@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    """Вернуться в главное меню"""
    # Просто вызываем команду start
    await cmd_start(callback.message)
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь"""
    help_text = """
🆘 <b>СПИСОК КОМАНД</b>

<b>ОСНОВНЫЕ:</b>
/start — Главное меню
/factory — Управление заводом
/cook_menu — Меню варки
/control_panel — Управление процессом
/inventory — Твой склад

<b>ЭКОНОМИКА:</b>
/market — Черный рынок
/laundry — Отмыв денег
/properties — Твоя недвижимость
/waste — Утилизация отходов

<b>БЕЗОПАСНОСТЬ:</b>
/security — Система защиты
/heat — Проверить розыск
/bribe — Дать взятку

<b>СОЦИАЛЬНОЕ:</b>
/cartel — Картель
/pvp — PVP арена
/leaderboard — Таблица лидеров
/profile — Твой профиль

<b>ПРОЧЕЕ:</b>
/donate — Магазин звезд
/tutorial — Обучение
/stats — Статистика
/settings — Настройки

📖 Подробный гайд: https://telegra.ph/MewBot-Guide
    """
    
    await message.answer(help_text)


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика пользователя"""
    user = await get_user(message.from_user.id)
    
    if not user:
        await message.answer("❌ Сначала используй /start")
        return
    
    total_money = user['money_dirty'] + user['money_clean']
    
    stats_text = f"""
📊 <b>СТАТИСТИКА КАРТЕЛЯ</b>

👤 <b>{user['cartel_name']}</b>
🎯 Уровень: <b>{user['level']}</b>
⭐️ Опыт: <b>{user['experience']:,}</b> XP
🏆 Респект: <b>{user['respect']:,}</b>

💰 <b>ФИНАНСЫ:</b>
├ Всего: <b>${total_money:,}</b>
├ Грязные: ${user['money_dirty']:,}
└ Чистые: ${user['money_clean']:,}

🏭 <b>ПРОИЗВОДСТВО:</b>
├ Всего сварено: <b>{user['total_cooked']:,}</b> г
├ Продано на: <b>${user['total_sold']:,}</b>
└ Отмыто: <b>${user['total_laundered']:,}</b>

⚠️ <b>ИНЦИДЕНТЫ:</b>
├ Взрывов: {user['explosions']} 💥
├ Арестов: {user['busts']} 👮
└ Смертей: {user['deaths']} ☠️

📅 Играет с: {user['created_at'].strftime('%d.%m.%Y')}
    """
    
    await message.answer(stats_text)
