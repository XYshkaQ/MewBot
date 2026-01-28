# -*- coding: utf-8 -*-
"""
Конфигурация бота
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# База данных
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/mewbot')

# Настройки игры
GAME_CONFIG = {
    # Базовые параметры
    'START_MONEY_DIRTY': 5000,
    'START_MONEY_CLEAN': 1000,
    'MAX_HEAT': 100,
    'EXPLOSION_CHANCE_BASE': 5,  # %
    
    # Тайминги (в секундах)
    'TICK_INTERVAL': 60,  # Игровой тик каждую минуту
    'COOK_CHECK_INTERVAL': 30,  # Проверка варки каждые 30 сек
    
    # Регионы города Берломосквы
    'REGIONS': [
        {'id': 1, 'name': 'Кремлёвские Гетто', 'tier': 1, 'danger': 20},
        {'id': 2, 'name': 'Промзона Шпрееваль', 'tier': 2, 'danger': 35},
        {'id': 3, 'name': 'Район Замкадье', 'tier': 2, 'danger': 40},
        {'id': 4, 'name': 'Деловой Квартал Митте-Сити', 'tier': 3, 'danger': 50},
        {'id': 5, 'name': 'Порт "Рейх-Волга"', 'tier': 3, 'danger': 55},
        {'id': 6, 'name': 'Элитный Рублёвбург', 'tier': 4, 'danger': 70},
        {'id': 7, 'name': 'Подземка "Унтерграунд"', 'tier': 4, 'danger': 80},
        {'id': 8, 'name': 'Красная Площадь-Тиргартен', 'tier': 5, 'danger': 95}
    ],
    
    # Вещества и их параметры
    'SUBSTANCES': {
        'mephedrone': {
            'name': '💊 Мефедрон (Meow)',
            'tier': 1,
            'cook_time': 1800,  # 30 минут
            'optimal_temp': 140,
            'temp_range': 10,
            'pressure_max': 300,
            'base_purity': 75,
            'base_price': 50,
            'demand_multi': 1.5,
            'explosion_risk': 5,
            'precursors': {'бензол': 2, 'метиламин': 1, 'ацетон': 1}
        },
        'mdma': {
            'name': '💎 MDMA (Molly)',
            'tier': 2,
            'cook_time': 3600,  # 1 час
            'optimal_temp': 165,
            'temp_range': 8,
            'pressure_max': 450,
            'base_purity': 80,
            'base_price': 120,
            'demand_multi': 1.3,
            'explosion_risk': 15,
            'precursors': {'сафрол': 3, 'метиламин': 2, 'ртуть': 1, 'йод': 1}
        },
        'methamphetamine': {
            'name': '⚗️ Метамфетамин (Ice)',
            'tier': 3,
            'cook_time': 5400,  # 1.5 часа
            'optimal_temp': 180,
            'temp_range': 5,
            'pressure_max': 600,
            'base_purity': 85,
            'base_price': 250,
            'demand_multi': 1.1,
            'explosion_risk': 35,
            'precursors': {'псевдоэфедрин': 4, 'красный фосфор': 2, 'йод': 2, 'ацетон': 2}
        },
        'ketamine': {
            'name': '🐱 Кетамин (Kotik)',
            'tier': 3,
            'cook_time': 4200,  # 1 час 10 мин
            'optimal_temp': 155,
            'temp_range': 7,
            'pressure_max': 520,
            'base_purity': 82,
            'base_price': 180,
            'demand_multi': 1.2,
            'explosion_risk': 25,
            'precursors': {'циклогексанон': 3, 'бромид': 2, 'аммиак': 2, 'эфир': 1}
        },
        'aurora': {
            'name': '🌌 Аврора (Starfield)',
            'tier': 4,
            'cook_time': 7200,  # 2 часа
            'optimal_temp': 195,
            'temp_range': 3,
            'pressure_max': 800,
            'base_purity': 90,
            'base_price': 500,
            'demand_multi': 0.8,
            'explosion_risk': 50,
            'precursors': {'ксенон': 2, 'плутоний-238': 1, 'нанотрубки': 3, 'квантовая пыль': 2, 'жидкий азот': 2}
        },
        'fentanyl': {
            'name': '☠️ Фентанил (The End)',
            'tier': 5,
            'cook_time': 10800,  # 3 часа
            'optimal_temp': 210,
            'temp_range': 2,
            'pressure_max': 1000,
            'base_purity': 95,
            'base_price': 1000,
            'demand_multi': 0.6,
            'explosion_risk': 75,
            'death_risk': 30,  # Риск смерти клиентов при низкой чистоте
            'precursors': {'анилин': 5, 'пропионовая кислота': 3, 'фосген': 2, 'меторфинол': 2, 'HCl': 1}
        }
    },
    
    # Оборудование
    'EQUIPMENT': {
        'reactor_1': {'name': 'Реактор Mk-I', 'price': 10000, 'tier': 1, 'boost': 5, 'durability': 100},
        'reactor_2': {'name': 'Реактор Mk-II', 'price': 50000, 'tier': 2, 'boost': 15, 'durability': 150},
        'reactor_3': {'name': 'Реактор Mk-III', 'price': 200000, 'tier': 3, 'boost': 30, 'durability': 200},
        'reactor_4': {'name': 'Квантовый Реактор', 'price': 1000000, 'tier': 4, 'boost': 50, 'durability': 300},
        
        'centrifuge_1': {'name': 'Центрифуга Базовая', 'price': 8000, 'tier': 1, 'purity_boost': 3},
        'centrifuge_2': {'name': 'Центрифуга Про', 'price': 40000, 'tier': 2, 'purity_boost': 8},
        'centrifuge_3': {'name': 'Центрифуга Ультра', 'price': 150000, 'tier': 3, 'purity_boost': 15},
        
        'dryer_1': {'name': 'Сушилка Обычная', 'price': 5000, 'tier': 1, 'time_reduction': 5},
        'dryer_2': {'name': 'Вакуумная Сушка', 'price': 30000, 'tier': 2, 'time_reduction': 15},
        'dryer_3': {'name': 'Крио-Сушка', 'price': 120000, 'tier': 3, 'time_reduction': 30},
        
        'filter_1': {'name': 'Фильтр Бумажный', 'price': 500, 'tier': 1, 'uses': 5, 'purity_boost': 2},
        'filter_2': {'name': 'Керамический Фильтр', 'price': 2000, 'tier': 2, 'uses': 15, 'purity_boost': 5},
        'filter_3': {'name': 'Наноф��льтр', 'price': 10000, 'tier': 3, 'uses': 50, 'purity_boost': 10},
        
        'generator_1': {'name': 'Бензогенератор', 'price': 7000, 'tier': 1, 'fuel_consumption': 5},
        'generator_2': {'name': 'Дизель-Генератор', 'price': 35000, 'tier': 2, 'fuel_consumption': 3},
        'generator_3': {'name': 'Реактор Холодного Синтеза', 'price': 500000, 'tier': 4, 'fuel_consumption': 0},
        
        'ventilation_1': {'name': 'Вытяжка', 'price': 3000, 'tier': 1, 'fume_reduction': 20},
        'ventilation_2': {'name': 'Промышленная Вентиляция', 'price': 15000, 'tier': 2, 'fume_reduction': 50},
        'ventilation_3': {'name': 'Система Очистки Воздуха', 'price': 80000, 'tier': 3, 'fume_reduction': 90},
        
        'security_cam': {'name': 'Камера Наблюдения', 'price': 2000, 'heat_reduction': 5},
        'alarm_system': {'name': 'Сигнализация', 'price': 8000, 'heat_reduction': 10},
        'bunker_door': {'name': 'Бронированная Дверь', 'price': 25000, 'heat_reduction': 20},
        'emp_jammer': {'name': 'EMP-Глушилка', 'price': 100000, 'heat_reduction': 40}
    },
    
    # Недвижимость
    'PROPERTIES': {
        'garage': {'name': '🚗 Гараж в Гетто', 'price': 50000, 'slots': 2, 'tier': 1, 'income': 0},
        'warehouse': {'name': '🏭 Склад в Промзоне', 'price': 200000, 'slots': 5, 'tier': 2, 'income': 500},
        'factory': {'name': '🏗️ Заброшенный Завод', 'price': 1000000, 'slots': 10, 'tier': 3, 'income': 2000},
        'lab_underground': {'name': '🔬 Подземная Лаборатория', 'price': 5000000, 'slots': 15, 'tier': 4, 'income': 10000},
        'mansion': {'name': '🏰 Особняк в Рублёвбурге', 'price': 20000000, 'slots': 20, 'tier': 5, 'income': 50000},
        
        'bar': {'name': '🍺 Бар "Кристалл"', 'price': 300000, 'type': 'laundry', 'capacity': 50000, 'rate': 0.85},
        'casino': {'name': '🎰 Казино "Берлинская Рулетка"', 'price': 2000000, 'type': 'laundry', 'capacity': 500000, 'rate': 0.75},
        'nightclub': {'name': '🎵 Ночной Клуб "Аврора"', 'price': 5000000, 'type': 'laundry', 'capacity': 2000000, 'rate': 0.70},
        'bank': {'name': '🏦 Частный Банк', 'price': 50000000, 'type': 'laundry', 'capacity': 50000000, 'rate': 0.60}
    },
    
    # Персонал
    'STAFF': {
        'chemist_1': {'name': 'Химик-Новичок', 'price': 5000, 'boost': 5, 'salary': 500},
        'chemist_2': {'name': 'Опытный Химик', 'price': 25000, 'boost': 15, 'salary': 2000},
        'chemist_3': {'name': 'Профессор Химии', 'price': 100000, 'boost': 30, 'salary': 10000},
        
        'dealer_1': {'name': 'Барыга-Школьник', 'price': 2000, 'region_unlock': 1, 'heat_risk': 30},
        'dealer_2': {'name': 'Кладмен', 'price': 10000, 'region_unlock': 3, 'heat_risk': 15},
        'dealer_3': {'name': 'Дилер-Призрак', 'price': 50000, 'region_unlock': 5, 'heat_risk': 5},
        
        'guard_1': {'name': 'Охранник-Гопник', 'price': 3000, 'pvp_defense': 10},
        'guard_2': {'name': 'ЧОП "Беркут"', 'price': 15000, 'pvp_defense': 25},
        'guard_3': {'name': 'Элитный Спецназ', 'price': 100000, 'pvp_defense': 50},
        
        'lawyer': {'name': '⚖️ Адвокат', 'price': 50000, 'heat_reduction': 20, 'jail_escape': True}
    }
}

# Telegram Stars цены (донат)
DONATE_PRICES = {
    'golden_mask': 100,  # Премиум на месяц
    'lawyer_call': 50,  # Выход из тюрьмы
    'express_delivery': 20,  # Моментальная доставка
    'skin_breaking_bad': 30,
    'skin_narcos': 30,
    'skin_cyberpunk': 50,
    'resurrect': 150,  # Воскрешение после взрыва
    'speed_boost_1h': 25,  # Ускорение варки на 1 час
    'purity_guarantee': 40,  # Гарантия 99% чистоты
    'heat_reset': 60  # Сброс розыска
}

# Webhook для облака (если используется)
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', '')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook')
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Webapp URL для Telegraph гайдов
TELEGRAPH_BASE = "https://telegra.ph/MewBot---Rukovodstvo-01-28-2"
