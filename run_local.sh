#!/bin/bash
# Скрипт для запуска бота локально в фоновом режиме (headless)

echo "========================================"
echo "Запуск Freelancehunt Bot (локально)"
echo "========================================"
echo ""
echo "Убедитесь что:"
echo "1. Установлены все зависимости: pip install -r requirements.txt"
echo "2. Файл cookies.json существует в корневой папке"
echo "3. Telegram Bot Token настроен в config.py или .env"
echo ""
echo "Бот будет работать в фоновом режиме (браузер не откроется)"
echo "Проверка новых проектов каждые 60 секунд"
echo ""
read -p "Нажмите Enter для продолжения..."

# Установить headless режим через переменную окружения
export HEADLESS_BROWSER=true
export BROWSER_TYPE=chrome

# Запустить бота
python bot.py

