#!/bin/bash

echo "🔥 MewBot Cartel - Быстрый старт"
echo "================================="
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден! Установи Python 3.9+"
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"

# Проверка PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL не найден. Используй Docker:"
    echo "   docker-compose up -d postgres"
    echo ""
fi

# Создание venv
if [ ! -d "venv" ]; then
    echo "📦 Создаю виртуальное окружение..."
    python3 -m venv venv
fi

# Активация venv
source venv/bin/activate

# Установка зависимостей
echo "📥 Устанавливаю зависимости..."
pip install -r requirements.txt

# Проверка .env
if [ ! -f ".env" ]; then
    echo "⚙️  Создаю .env файл..."
    cp .env.example .env
    echo ""
    echo "⚠️  ВАЖНО! Отредактируй .env файл:"
    echo "   nano .env"
    echo ""
    echo "Добавь:"
    echo "   BOT_TOKEN=твой_токен_от_@BotFather"
    echo "   DATABASE_URL=postgresql://..."
    echo ""
    exit 1
fi

# Проверка токена
if grep -q "your_bot_token_here" .env; then
    echo "❌ Токен бота не настроен!"
    echo "   Открой .env и добавь токен от @BotFather"
    exit 1
fi

echo ""
echo "✅ Всё готово!"
echo ""
echo "🚀 Запуск бота:"
echo "   python main.py"
echo ""
echo "🐳 Или через Docker:"
echo "   docker-compose up"
echo ""
echo "📚 Документация: README.md"
echo ""
