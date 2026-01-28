# ЗАМЕНИ ФУНКЦИЮ finish_cooking В mechanics/scheduler.py НА ЭТУ:

async def finish_cooking(bot: Bot, session: dict):
    """Завершить варку - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
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
    
    # ИСПРАВЛЕНИЕ: Импортируем функцию add_to_inventory
    from database.db_manager import add_to_inventory
    
    # Сохраняем продукт В ИНВЕНТАРЬ
    await add_to_inventory(
        user_id,
        'product',
        substance,
        amount,
        purity=final_purity  # Передаем чистоту в metadata
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
            f"📦 Товар добавлен в /inventory\n"
            f"💰 Продай через /market"
        )
    except:
        pass
