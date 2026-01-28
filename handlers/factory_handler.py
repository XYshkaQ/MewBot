# -*- coding: utf-8 -*-
"""
Хендлер завода - ПОЛНАЯ ВЕРСИЯ
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_manager import get_user, get_factory
from config.settings import GAME_CONFIG

router = Router()

@router.message(Command("factory"))
@router.callback_query(F.data == "factory_main")
async def factory_main(event):
    """Главное меню завода"""
    message = event.message if isinstance(event, CallbackQuery) else event
    user_id = event.from_user.id
    
    user = await get_user(user_id)
    factory = await get_factory(user_id)
    
    if not factory:
        await message.answer("❌ У тебя нет завода! Что-то пошло не так...")
        return
    
    # Получаем локацию
    location = GAME_CONFIG['REGIONS'][factory['location_id'] - 1]
    
    # Получаем оборудование
    equipment = factory.get('equipment', {})
    equipment_list = []
    
    if equipment:
        for eq_id, eq_data in equipment.items():
            eq_info = GAME_CONFIG['EQUIPMENT'].get(eq_id, {})
            durability = eq_data.get('durability', 100)
            status = "✅" if durability > 70 else "⚠️" if durability > 30 else "🔴"
            equipment_list.append(f"{status} {eq_info.get('name', eq_id)}")
    else:
        equipment_list.append("❌ Нет оборудования")
    
    # Статус завода
    status_emoji = {
        'IDLE': '💤',
        'COOKING': '🔥',
        'BROKEN': '💥'
    }.get(factory['status'], '❓')
    
    text = f"""
🏭 <b>ТВОЙ ЗАВОД</b>

📍 <b>Локация:</b> {location['name']}
🎯 <b>Tier:</b> {location['tier']} | ⚠️ Опасность: {location['danger']}%

{status_emoji} <b>Статус:</b> {factory['status']}
📦 <b>Слоты:</b> {factory['slots_used']}/{factory['slots_total']}

<b>⚙️ ОБОРУДОВАНИЕ:</b>
{chr(10).join(equipment_list)}

<i>Используй /market для покупки оборудования</i>
<i>Начни варку через /cook_menu</i>
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚙️ Оборудование", callback_data="factory_equipment"),
            InlineKeyboardButton(text="👥 Персонал", callback_data="factory_staff")
        ],
        [
            InlineKeyboardButton(text="⚗️ Начать варку", callback_data="cook_menu"),
            InlineKeyboardButton(text="🛒 Магазин", callback_data="market_main")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
        await event.answer()
    else:
        await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "factory_equipment")
async def factory_equipment(callback: CallbackQuery):
    """Меню оборудования"""
    user_id = callback.from_user.id
    factory = await get_factory(user_id)
    
    equipment = factory.get('equipment', {})
    
    text = "<b>⚙️ ОБОРУДОВАНИЕ ЗАВОДА</b>\n\n"
    
    if not equipment:
        text += "❌ Оборудование не установлено\n\n"
        text += "Купи оборудование в /market"
    else:
        for eq_id, eq_data in equipment.items():
            eq_info = GAME_CONFIG['EQUIPMENT'].get(eq_id, {})
            durability = eq_data.get('durability', 100)
            
            # Статус
            if durability > 70:
                status = "✅ Отлично"
            elif durability > 30:
                status = "⚠️ Изношено"
            else:
                status = "🔴 Сломано"
            
            text += f"<b>{eq_info.get('name', eq_id)}</b>\n"
            text += f"├ Прочность: {durability:.0f}%\n"
            text += f"└ Статус: {status}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить оборудование", callback_data="market_equipment")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="factory_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "factory_staff")
async def factory_staff(callback: CallbackQuery):
    """Меню персонала"""
    user_id = callback.from_user.id
    factory = await get_factory(user_id)
    
    staff = factory.get('staff', {})
    
    text = "<b>👥 ПЕРСОНАЛ ЗАВОДА</b>\n\n"
    
    if not staff:
        text += "❌ Персонал не нанят\n\n"
        text += "Нанимай работников в /market:\n"
        text += "• Химики — повышают чистоту\n"
        text += "• Дилеры — продают товар\n"
        text += "• Охрана — защищает от рейдов\n"
        text += "• Адвокат — снижает Heat"
    else:
        for staff_id, staff_data in staff.items():
            staff_info = GAME_CONFIG['STAFF'].get(staff_id, {})
            
            text += f"<b>{staff_info.get('name', staff_id)}</b>\n"
            text += f"├ Буст: +{staff_info.get('boost', 0)}%\n"
            text += f"└ Зарплата: ${staff_info.get('salary', 0)}/день\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Нанять персонал", callback_data="market_staff")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="factory_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
