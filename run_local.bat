@echo off
REM Скрипт для запуска бота локально в фоновом режиме (headless)
echo ========================================
echo Запуск Freelancehunt Bot (локально)
echo ========================================
echo.
echo Убедитесь что:
echo 1. Установлены все зависимости: pip install -r requirements.txt
echo 2. Файл cookies.json существует в корневой папке
echo 3. Telegram Bot Token настроен в config.py или .env
echo.
echo Бот будет работать в фоновом режиме (браузер не откроется)
echo Проверка новых проектов каждые 60 секунд
echo.
pause

echo.
echo Запуск бота в фоновом режиме...
echo Браузер не будет открываться (headless режим)
echo.

REM Установить headless режим через переменную окружения
set HEADLESS_BROWSER=true
set BROWSER_TYPE=chrome

REM Запустить бота
python bot.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ОШИБКА при запуске бота!
    echo Проверьте:
    echo 1. Установлены ли зависимости: pip install -r requirements.txt
    echo 2. Существует ли файл cookies.json
    echo 3. Правильно ли настроен Telegram Bot Token
    pause
)

