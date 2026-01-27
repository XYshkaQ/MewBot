# -*- coding: utf-8 -*-
"""
Игровой цикл и фоновые процессы
"""

import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Bot
from database.db_manager import pool, get_user, update_user, update_cooking
from config.settings import GAME_CONFIG


async def start_game_loop(bot: Bot):
    """Запуск основного игрового цикла"""
    await asyncio.sleep(5)  # Даем боту запуститься
    
    while True:
        try:
            await process_cooking_sessions(bot)
            await process_heat_decay()
            await process_market_dynamics()
            await process_property_income()
            
            # Тик каждую минуту
            await asyncio.sleep(GAME_CONFIG['TICK_INTERVAL'])
        
        except Exception as e:
            print(f"❌ Ошибка в game loop: {e}")
            await asyncio.sleep(60)


async def process_cooking_sessions(bot: Bot):
    """Обработка активных варок"""
    async with pool.acquire() as conn:
        sessions = await conn.fetch('''
            SELECT cs.*, u.user_id, u.username 
            FROM cooking_sessions cs
            JOIN users u ON cs.user_id = u.user_id
            WHERE cs.status = 'ACTIVE'
        ''')
        
        for session in sessions:
            try:
                await process_single_cooking(bot, dict(session))
            except Exception as e:
                print(f"Ошибка обработки варки {session['id']}: {e}")


async def process_single_cooking(bot: Bot, session: dict):
    """Обработка одной варки"""
    user_id = session['user_id']
    session_id = session['id']
    substance = session['substance']
    
    sub_data = GAME_CONFIG['SUBSTANCES'][substance]
    
    now = datetime.now()
    elapsed = (now - session['start_time']).total_seconds()
    total_time = sub_data['cook_time']
    
    # Проверка завершения
    if elapsed >= total_time:
        await finish_cooking(bot, session)
        return
    
    # Случайные флуктуации
    temp_change = random.uniform(-5, 5)
    pressure_change = random.uniform(-10, 20)
    fume_increase = random.randint(0, 5)
    
    new_temp = session['current_temp'] + temp_change
    new_pressure = max(0, session['pressure'] + pressure_change)
    new_fumes = session['fumes'] + fume_increase
    
    # Проверка на взрыв
    explosion_chance = sub_data['explosion_risk']
    
    if new_pressure > sub_data['pressure_max']:
        explosion_chance += 30
    
    temp_diff = abs(new_temp - session['target_temp'])
    if temp_diff > 30:
        explosion_chance += 20
    
    if random.random() * 100 < explosion_chance:
        await trigger_explosion(bot, session)
        return
    
    # Обновляем состояние
    await update_cooking(
        session_id,
        current_temp=new_temp,
        pressure=new_pressure,
        fumes=new_fumes
    )
    
    # Уведомление при критических параметрах
    if new_pressure > sub_data['pressure_max'] * 0.95:
        try:
            await bot.send_message(
                user_id,
                f"🚨 <b>КРИТИЧЕСКОЕ ДАВЛЕНИЕ!</b>\n"
                f"💨 {new_pressure:.0f}/{sub_data['pressure_max']} PSI\n"
                f"⚠️ Риск взрыва! Срочно используй /control_panel!"
            )
        except:
            pass


async def finish_cooking(bot: Bot, session: dict):
    """Завершить варку"""
    user_id = session['user_id']
    substance = session['substance']
    amount = session['amount']
    
    sub_data = GAME_CONFIG['SUBSTANCES'][substance]
    
    # Расчет финальной чистоты
    temp_diff = abs(session['current_temp'] - session['target_temp'])
    temp_penalty = min(30, temp_diff * 2)
    
    pressure_penalty = 0
    if session['pressure'] > sub_data['pressure_max'] * 0.8:
        pressure_penalty = 10
    
    fume_penalty = min(20, session['fumes'] // 5)
    
    final_purity = max(30, sub_data['base_purity'] - temp_penalty - pressure_penalty - fume_penalty)
    
    # Проверка на фентанил
    if substance == 'fentanyl' and final_purity < 90:
        deaths = random.randint(1, 5)
        
        async with pool.acquire() as conn:
            await conn.execute('''
                UPDATE cooking_sessions 
                SET status = 'FAILED', purity = $2
                WHERE id = $1
            ''', session['id'], final_purity)
            
            # Увеличиваем Heat на 50
            user = await get_user(user_id)
            new_heat = min(100, user['heat'] + 50)
            await update_user(user_id, heat=new_heat)
        
        try:
            await bot.send_message(
                user_id,
                f"☠️ <b>КАТАСТРОФА!</b>\n\n"
                f"Твой фентанил чистотой {final_purity:.1f}% убил <b>{deaths}</b> человек!\n"
                f"🚨 Менты на хвосте! Heat +50 → {new_heat}/100\n\n"
                f"<i>Фентанил требует чистоты 90%+</i>"
            )
        except:
            pass
        
        return
    
    # Сохраняем продукт
    from database.db_manager import add_to_inventory
    
    await add_to_inventory(
        user_id,
        'product',
        substance,
        amount,
        purity=final_purity
    )
    
    # Обновляем статистику
    user = await get_user(user_id)
    new_cooked = user['total_cooked'] + amount
    new_exp = user['experience'] + (amount * sub_data['tier'])
    
    # Проверка уровня
    new_level = user['level']
    level_threshold = new_level * 1000
    if new_exp >= level_threshold:
        new_level += 1
    
    await update_user(
        user_id,
        total_cooked=new_cooked,
        experience=new_exp,
        level=new_level
    )
    
    async with pool.acquire() as conn:
        await conn.execute('''
            UPDATE cooking_sessions 
            SET status = 'COMPLETED', purity = $2
            WHERE id = $1
        ''', session['id'], final_purity)
    
    # Уведомление
    tier_stars = "⭐" * sub_data['tier']
    quality = "🏆 ИДЕАЛЬНО" if final_purity >= 95 else "💎 ОТЛИЧНО" if final_purity >= 85 else "✅ ХОРОШО" if final_purity >= 75 else "⚠️ УДОВЛЕТВОРИТЕЛЬНО"
    
    try:
        await bot.send_message(
            user_id,
            f"✅ <b>ВАРКА ЗАВЕРШЕНА!</b>\n\n"
            f"⚗️ {sub_data['name']} {tier_stars}\n"
            f"⚖️ Получено: <b>{amount}г</b>\n"
            f"💎 Чистота: <b>{final_purity:.1f}%</b>\n"
            f"{quality}\n\n"
            f"📊 +{amount * sub_data['tier']} XP\n"
            f"{'🎉 НОВЫЙ УРОВЕНЬ! ' + str(new_level) if new_level > user['level'] else ''}\n\n"
            f"💰 Продай через /market или храни в /inventory"
        )
    except:
        pass


async def trigger_explosion(bot: Bot, session: dict):
    """Взрыв лаборатории"""
    user_id = session['user_id']
    substance = session['substance']
    
    sub_data = GAME_CONFIG['SUBSTANCES'][substance]
    
    # Урон финансам (20-50% грязных денег)
    user = await get_user(user_id)
    loss_percent = random.uniform(0.2, 0.5)
    money_lost = int(user['money_dirty'] * loss_percent)
    
    new_money = max(0, user['money_dirty'] - money_lost)
    new_explosions = user['explosions'] + 1
    new_heat = min(100, user['heat'] + 30)
    
    await update_user(
        user_id,
        money_dirty=new_money,
        explosions=new_explosions,
        heat=new_heat
    )
    
    # Удаляем варку
    async with pool.acquire() as conn:
        await conn.execute('''
            UPDATE cooking_sessions 
            SET status = 'EXPLODED'
            WHERE id = $1
        ''', session['id'])
        
        # Логируем инцидент
        await conn.execute('''
            INSERT INTO incident_log (user_id, incident_type, details)
            VALUES ($1, 'explosion', $2)
        ''', user_id, f'{{"substance": "{substance}", "money_lost": {money_lost}}}')
    
    try:
        await bot.send_message(
            user_id,
            f"💥 <b>ВЗРЫВ В ЛАБОРАТОРИИ!</b> 💥\n\n"
            f"⚗️ {sub_data['name']} взорвался!\n"
            f"💸 Потери: <b>${money_lost:,}</b> ({loss_percent*100:.0f}%)\n"
            f"🚨 Heat +30 → {new_heat}/100\n\n"
            f"☠️ Всего взрывов: {new_explosions}\n\n"
            f"<i>Следи за давлением и температурой!</i>\n"
            f"💎 Воскресить лабу за 150⭐ → /donate"
        )
    except:
        pass


async def process_heat_decay():
    """Постепенное снижение Heat"""
    async with pool.acquire() as conn:
        # Снижаем Heat на 1 каждый тик у всех не в тюрьме
        await conn.execute('''
            UPDATE users 
            SET heat = GREATEST(0, heat - 1)
            WHERE NOT in_jail AND heat > 0
        ''')
        
        # Проверяем аресты
        users = await conn.fetch('''
            SELECT user_id, username, heat
            FROM users
            WHERE heat >= 100 AND NOT in_jail
        ''')
        
        for user in users:
            # Арест на 24 часа
            jail_until = datetime.now() + timedelta(hours=24)
            
            await conn.execute('''
                UPDATE users
                SET in_jail = TRUE, jail_until = $2, heat = 50
                WHERE user_id = $1
            ''', user['user_id'], jail_until)
            
            # Логируем
            await conn.execute('''
                INSERT INTO incident_log (user_id, incident_type, details)
                VALUES ($1, 'arrest', '{"reason": "high_heat"}')
            ''', user['user_id'])
        
        # Освобождаем из тюрьмы
        await conn.execute('''
            UPDATE users
            SET in_jail = FALSE, jail_until = NULL
            WHERE in_jail AND jail_until < NOW()
        ''')


async def process_market_dynamics():
    """Обновление рыночных цен"""
    async with pool.acquire() as conn:
        # Получаем статистику продаж за последний час
        for substance in GAME_CONFIG['SUBSTANCES'].keys():
            # Обновляем спрос/предложение
            demand_change = random.uniform(-0.1, 0.1)
            
            await conn.execute('''
                UPDATE market_prices
                SET demand = GREATEST(0.5, LEAST(2.0, demand + $2)),
                    last_update = NOW()
                WHERE substance = $1
            ''', substance, demand_change)


async def process_property_income():
    """Обработка пассивного дохода от недвижимости"""
    async with pool.acquire() as conn:
        # Каждый час
        properties = await conn.fetch('''
            SELECT p.*, u.user_id
            FROM properties p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.income_daily > 0 
            AND p.last_income < NOW() - INTERVAL '1 hour'
        ''')
        
        for prop in properties:
            hourly_income = prop['income_daily'] // 24
            
            await conn.execute('''
                UPDATE users
                SET money_clean = money_clean + $2
                WHERE user_id = $1
            ''', prop['user_id'], hourly_income)
            
            await conn.execute('''
                UPDATE properties
                SET last_income = NOW()
                WHERE id = $1
            ''', prop['id'])
