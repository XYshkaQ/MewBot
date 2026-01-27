# 🚀 БЫСТРЫЙ СТАРТ

## Вариант 1: Локально (для разработки)

```bash
# 1. Клонируй репозиторий
git clone https://github.com/yourusername/mewbot_cartel.git
cd mewbot_cartel

# 2. Запусти скрипт установки
./start.sh

# 3. Настрой .env
nano .env
# Добавь BOT_TOKEN от @BotFather

# 4. Запусти PostgreSQL (если нет локального)
docker-compose up -d postgres

# 5. Запусти бота
python main.py
```

## Вариант 2: Docker (рекомендуется)

```bash
# 1. Клонируй
git clone https://github.com/yourusername/mewbot_cartel.git
cd mewbot_cartel

# 2. Создай .env
cp .env.example .env
nano .env  # Добавь BOT_TOKEN

# 3. Запусти всё
docker-compose up -d

# 4. Логи
docker-compose logs -f bot
```

## Вариант 3: Облако (Railway.app)

**Самый простой способ!**

1. Создай аккаунт на [railway.app](https://railway.app)
2. Нажми "New Project" → "Deploy from GitHub"
3. Выбери этот репозиторий
4. Добавь PostgreSQL из Marketplace
5. В переменных окружения добавь `BOT_TOKEN`
6. Деплой автоматический!

**URL для Railway:**
```
https://railway.app/new/template/...
```

## Вариант 4: Heroku

```bash
# 1. Установи Heroku CLI
# 2. Логин
heroku login

# 3. Создай приложение
heroku create mewbot-cartel

# 4. Добавь PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# 5. Установи переменные
heroku config:set BOT_TOKEN=твой_токен

# 6. Деплой
git push heroku main
```

## Вариант 5: VPS (Ubuntu)

```bash
# SSH на сервер
ssh user@your-server.com

# Установка зависимостей
sudo apt update
sudo apt install python3-pip postgresql git

# Клонирование
git clone https://github.com/yourusername/mewbot_cartel.git
cd mewbot_cartel

# PostgreSQL
sudo -u postgres createdb mewbot_cartel
sudo -u postgres createuser mewbot
sudo -u postgres psql -c "ALTER USER mewbot WITH PASSWORD 'твой_пароль';"

# Python пакеты
pip3 install -r requirements.txt

# .env
nano .env
# BOT_TOKEN=...
# DATABASE_URL=postgresql://mewbot:пароль@localhost/mewbot_cartel

# Systemd сервис
sudo nano /etc/systemd/system/mewbot.service
```

Содержимое сервиса:
```ini
[Unit]
Description=MewBot Cartel
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/mewbot_cartel
ExecStart=/usr/bin/python3 /root/mewbot_cartel/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Запуск
sudo systemctl enable mewbot
sudo systemctl start mewbot

# Логи
sudo journalctl -u mewbot -f
```

## Получение токена бота

1. Открой Telegram
2. Найди [@BotFather](https://t.me/botfather)
3. Отправь `/newbot`
4. Введи имя и username
5. Скопируй токен
6. Добавь в `.env`: `BOT_TOKEN=твой_токен`

## Проверка работы

```bash
# Логи
tail -f logs/bot.log

# Или Docker
docker-compose logs -f bot

# Или systemd
sudo journalctl -u mewbot -f
```

## Первый запуск

1. Найди своего бота в Telegram
2. Отправь `/start`
3. Пройди обучение
4. Начни первую варку!

## Проблемы?

**Бот не отвечает:**
- Проверь токен в .env
- Проверь подключение к БД
- Посмотри логи

**Ошибка подключения к БД:**
- Убедись что PostgreSQL запущен
- Проверь DATABASE_URL в .env
- Проверь права пользователя БД

**Взрывы постоянно:**
- Следи за давлением!
- Купи лучшее оборудование
- Читай гайд: /tutorial

## Полезные команды

```bash
# Обновление кода
git pull
pip install -r requirements.txt
# Перезапуск бота

# Бэкап БД
pg_dump mewbot_cartel > backup.sql

# Восстановление
psql mewbot_cartel < backup.sql

# Просмотр БД
psql mewbot_cartel
\dt  # Список таблиц
SELECT * FROM users LIMIT 10;
```

## Продакшен рекомендации

- Используй environment variables для секретов
- Настрой автоматические бэкапы БД
- Мониторинг: Sentry, LogDNA
- Reverse proxy: Nginx
- SSL сертификат: Let's Encrypt
- Webhook вместо long polling (опционально)

---

**Готово! Теперь запускай и зарабатывай! 💰**
