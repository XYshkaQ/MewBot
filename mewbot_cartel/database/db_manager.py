# -*- coding: utf-8 -*-
"""
Менеджер базы данных
Использует asyncpg для PostgreSQL
"""

import asyncpg
import json
from datetime import datetime
from typing import Optional, Dict, List
from config.settings import DATABASE_URL, GAME_CONFIG


# Глобальный пул соединений
pool: Optional[asyncpg.Pool] = None


async def init_db():
    """Инициализация БД и создание таблиц"""
    global pool
    
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
    
    async with pool.acquire() as conn:
        # Таблица пользователей
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                cartel_name VARCHAR(255) DEFAULT 'Новый Картель',
                money_dirty BIGINT DEFAULT 5000,
                money_clean BIGINT DEFAULT 1000,
                heat INTEGER DEFAULT 0,
                respect INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                experience BIGINT DEFAULT 0,
                premium_until TIMESTAMP,
                in_jail BOOLEAN DEFAULT FALSE,
                jail_until TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                last_active TIMESTAMP DEFAULT NOW(),
                total_cooked BIGINT DEFAULT 0,
                total_sold BIGINT DEFAULT 0,
                total_laundered BIGINT DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                explosions INTEGER DEFAULT 0,
                busts INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица заводов/лаб
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS factories (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                location_id INTEGER,
                property_type VARCHAR(50),
                slots_total INTEGER DEFAULT 2,
                slots_used INTEGER DEFAULT 0,
                equipment JSONB DEFAULT '{}',
                staff JSONB DEFAULT '{}',
                status VARCHAR(20) DEFAULT 'IDLE',
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Таблица активных варок
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS cooking_sessions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                factory_id INTEGER REFERENCES factories(id) ON DELETE CASCADE,
                substance VARCHAR(50),
                amount INTEGER,
                start_time TIMESTAMP DEFAULT NOW(),
                end_time TIMESTAMP,
                current_temp REAL DEFAULT 20.0,
                target_temp REAL,
                pressure REAL DEFAULT 0.0,
                purity REAL DEFAULT 0.0,
                fumes INTEGER DEFAULT 0,
                stage VARCHAR(50) DEFAULT 'mixing',
                precursors_used JSONB,
                status VARCHAR(20) DEFAULT 'ACTIVE',
                last_interaction TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Таблица инвентаря
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                item_type VARCHAR(50),
                item_id VARCHAR(100),
                quantity INTEGER DEFAULT 0,
                durability REAL DEFAULT 100.0,
                metadata JSONB DEFAULT '{}',
                PRIMARY KEY (user_id, item_type, item_id)
            )
        ''')
        
        # Таблица картелей/банд
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS cartels (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE,
                leader_id BIGINT REFERENCES users(user_id),
                treasury_dirty BIGINT DEFAULT 0,
                treasury_clean BIGINT DEFAULT 0,
                respect INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT NOW(),
                description TEXT,
                member_count INTEGER DEFAULT 1
            )
        ''')
        
        # Таблица членов картелей
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS cartel_members (
                cartel_id INTEGER REFERENCES cartels(id) ON DELETE CASCADE,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                rank VARCHAR(50) DEFAULT 'soldier',
                joined_at TIMESTAMP DEFAULT NOW(),
                contribution BIGINT DEFAULT 0,
                PRIMARY KEY (cartel_id, user_id)
            )
        ''')
        
        # Таблица контроля регионов
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS region_control (
                region_id INTEGER,
                cartel_id INTEGER REFERENCES cartels(id) ON DELETE SET NULL,
                control_percentage REAL DEFAULT 0.0,
                last_battle TIMESTAMP,
                defense_power INTEGER DEFAULT 0,
                PRIMARY KEY (region_id, cartel_id)
            )
        ''')
        
        # Таблица недвижимости
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                property_type VARCHAR(100),
                region_id INTEGER,
                purchase_price BIGINT,
                current_value BIGINT,
                income_daily BIGINT DEFAULT 0,
                last_income TIMESTAMP DEFAULT NOW(),
                metadata JSONB DEFAULT '{}',
                purchased_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Таблица транзакций (для отмыва)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS laundry_transactions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                property_id INTEGER REFERENCES properties(id) ON DELETE SET NULL,
                amount_dirty BIGINT,
                amount_clean BIGINT,
                rate REAL,
                timestamp TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Таблица рынка (динамические цены)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS market_prices (
                substance VARCHAR(50) PRIMARY KEY,
                current_price REAL,
                demand REAL DEFAULT 1.0,
                supply REAL DEFAULT 1.0,
                last_update TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Таблица PVP атак
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS pvp_attacks (
                id SERIAL PRIMARY KEY,
                attacker_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                defender_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                region_id INTEGER,
                attacker_power INTEGER,
                defender_power INTEGER,
                result VARCHAR(20),
                loot JSONB,
                timestamp TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Таблица истории взрывов/смертей
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS incident_log (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                incident_type VARCHAR(50),
                details JSONB,
                timestamp TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Инициализация рыночных цен
        for substance, data in GAME_CONFIG['SUBSTANCES'].items():
            await conn.execute('''
                INSERT INTO market_prices (substance, current_price, demand, supply)
                VALUES ($1, $2, 1.0, 1.0)
                ON CONFLICT (substance) DO NOTHING
            ''', substance, data['base_price'])


async def get_user(user_id: int) -> Optional[Dict]:
    """Получить данные пользователя"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
        return dict(row) if row else None


async def create_user(user_id: int, username: str) -> Dict:
    """Создать нового пользователя"""
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO users (user_id, username, money_dirty, money_clean)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO NOTHING
        ''', user_id, username, 
           GAME_CONFIG['START_MONEY_DIRTY'], 
           GAME_CONFIG['START_MONEY_CLEAN'])
        
        # Создать стартовый завод
        await conn.execute('''
            INSERT INTO factories (user_id, location_id, property_type, slots_total)
            VALUES ($1, 1, 'garage', 2)
        ''', user_id)
        
        return await get_user(user_id)


async def update_user(user_id: int, **kwargs):
    """Обновить данные пользователя"""
    if not kwargs:
        return
    
    fields = ', '.join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
    values = list(kwargs.values())
    
    async with pool.acquire() as conn:
        await conn.execute(
            f'UPDATE users SET {fields}, last_active = NOW() WHERE user_id = $1',
            user_id, *values
        )


async def get_factory(user_id: int) -> Optional[Dict]:
    """Получить завод пользователя"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow('''
            SELECT * FROM factories WHERE user_id = $1 ORDER BY id LIMIT 1
        ''', user_id)
        
        if row:
            result = dict(row)
            result['equipment'] = json.loads(result['equipment']) if isinstance(result['equipment'], str) else result['equipment']
            result['staff'] = json.loads(result['staff']) if isinstance(result['staff'], str) else result['staff']
            return result
        return None


async def get_active_cooking(user_id: int) -> Optional[Dict]:
    """Получить активную варку"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow('''
            SELECT * FROM cooking_sessions 
            WHERE user_id = $1 AND status = 'ACTIVE'
            ORDER BY id DESC LIMIT 1
        ''', user_id)
        
        if row:
            result = dict(row)
            result['precursors_used'] = json.loads(result['precursors_used']) if isinstance(result['precursors_used'], str) else result['precursors_used']
            return result
        return None


async def start_cooking(user_id: int, factory_id: int, substance: str, amount: int, precursors: Dict) -> int:
    """Начать варку"""
    substance_data = GAME_CONFIG['SUBSTANCES'][substance]
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow('''
            INSERT INTO cooking_sessions 
            (user_id, factory_id, substance, amount, target_temp, precursors_used, end_time)
            VALUES ($1, $2, $3, $4, $5, $6, NOW() + INTERVAL '%s seconds')
            RETURNING id
        ''' % substance_data['cook_time'], 
           user_id, factory_id, substance, amount, 
           substance_data['optimal_temp'], json.dumps(precursors))
        
        return row['id']


async def update_cooking(session_id: int, **kwargs):
    """Обновить параметры варки"""
    if not kwargs:
        return
    
    fields = ', '.join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
    values = list(kwargs.values())
    
    async with pool.acquire() as conn:
        await conn.execute(
            f'UPDATE cooking_sessions SET {fields}, last_interaction = NOW() WHERE id = $1',
            session_id, *values
        )


async def get_inventory(user_id: int, item_type: Optional[str] = None) -> List[Dict]:
    """Получить инвентарь"""
    async with pool.acquire() as conn:
        if item_type:
            rows = await conn.fetch('''
                SELECT * FROM inventory WHERE user_id = $1 AND item_type = $2
            ''', user_id, item_type)
        else:
            rows = await conn.fetch('''
                SELECT * FROM inventory WHERE user_id = $1
            ''', user_id)
        
        result = []
        for row in rows:
            item = dict(row)
            item['metadata'] = json.loads(item['metadata']) if isinstance(item['metadata'], str) else item['metadata']
            result.append(item)
        return result


async def add_to_inventory(user_id: int, item_type: str, item_id: str, quantity: int, **metadata):
    """Добавить предмет в инвентарь"""
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO inventory (user_id, item_type, item_id, quantity, metadata)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id, item_type, item_id) 
            DO UPDATE SET quantity = inventory.quantity + $4
        ''', user_id, item_type, item_id, quantity, json.dumps(metadata))


async def remove_from_inventory(user_id: int, item_type: str, item_id: str, quantity: int) -> bool:
    """Убрать предмет из инвентаря"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow('''
            SELECT quantity FROM inventory 
            WHERE user_id = $1 AND item_type = $2 AND item_id = $3
        ''', user_id, item_type, item_id)
        
        if not row or row['quantity'] < quantity:
            return False
        
        new_quantity = row['quantity'] - quantity
        
        if new_quantity <= 0:
            await conn.execute('''
                DELETE FROM inventory 
                WHERE user_id = $1 AND item_type = $2 AND item_id = $3
            ''', user_id, item_type, item_id)
        else:
            await conn.execute('''
                UPDATE inventory SET quantity = $4
                WHERE user_id = $1 AND item_type = $2 AND item_id = $3
            ''', user_id, item_type, item_id, new_quantity)
        
        return True


async def get_leaderboard(category: str = 'money', limit: int = 10) -> List[Dict]:
    """Получить таблицу лидеров"""
    order_by = {
        'money': 'money_clean + money_dirty DESC',
        'respect': 'respect DESC',
        'cooked': 'total_cooked DESC',
        'level': 'level DESC, experience DESC'
    }.get(category, 'respect DESC')
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(f'''
            SELECT user_id, username, cartel_name, money_clean, money_dirty, 
                   respect, level, total_cooked, total_sold
            FROM users
            WHERE NOT in_jail
            ORDER BY {order_by}
            LIMIT $1
        ''', limit)
        
        return [dict(row) for row in rows]


async def close_db():
    """Закрыть пул соединений"""
    global pool
    if pool:
        await pool.close()
