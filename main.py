#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MewBot Cartel - Главный файл запуска
Даркнет-симулятор производства и торговли
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import BOT_TOKEN
from database.db_manager import init_db
from handlers import start_handler, cooking_handler, factory_handler
from handlers.all_handlers import (
    market_router, cartel_router, pvp_router,
    property_router, laundry_router, security_router
)
from mechanics.scheduler import start_game_loop

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Запуск бота"""
    logger.info("🔥 Запуск MewBot Cartel...")
    
    # Инициализация БД
    await init_db()
    logger.info("✅ База данных инициализирована")
    
    # Создание бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Регистрация хендлеров
    dp.include_router(start_handler.router)
    dp.include_router(factory_handler.router)
    dp.include_router(cooking_handler.router)
    dp.include_router(market_router)
    dp.include_router(cartel_router)
    dp.include_router(pvp_router)
    dp.include_router(property_router)
    dp.include_router(laundry_router)
    dp.include_router(security_router)
    
    # Запуск игрового цикла
    asyncio.create_task(start_game_loop(bot))
    
    logger.info("🚀 Бот запущен!")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
