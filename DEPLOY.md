# Инструкция по развертыванию на Render

## Шаг 1: Создайте репозиторий на GitHub

1. Создайте новый репозиторий на GitHub (https://github.com/new)
2. Назовите его, например: `freelancehunt-bot`
3. Инициализируйте Git в локальной папке (если еще не сделано):

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/freelancehunt-bot.git
git push -u origin main
```

## Шаг 2: Развертывание на Render

### Вариант А: Через Render Dashboard

1. Перейдите на https://dashboard.render.com
2. Нажмите "New +" → "Web Service"
3. Подключите ваш GitHub репозиторий
4. Настройте:
   - **Name**: `freelancehunt-bot`
   - **Runtime**: `Docker`
   - **Region**: `Oregon` (или ближайший к вам)
   - **Branch**: `main`
   - **Build Command**: (оставить пустым, Dockerfile сам все соберет)
   - **Start Command**: (оставить пустым, используется CMD из Dockerfile)
   - **Plan**: `Starter` (или выше)

5. **Добавьте переменные окружения** в разделе "Environment":
   ```
   TELEGRAM_BOT_TOKEN=ваш_токен_бота
   HEADLESS_BROWSER=true
   BROWSER_TYPE=edge
   DATABASE_FILE=/app/data/freelancehunt_bot.db
   COOKIES_FILE=/app/data/cookies.json
   CHECK_INTERVAL=60
   MAX_BID_AMOUNT=27000
   ```

6. **Добавьте Persistent Disk** (для хранения базы данных и cookies):
   - Нажмите "Add Disk"
   - **Name**: `bot-data`
   - **Mount Path**: `/app/data`
   - **Size**: 1 GB

7. Нажмите "Create Web Service"

### Вариант Б: Через Render MCP (API)

После создания GitHub репозитория, можно использовать MCP команды (если у вас есть доступ).

## Шаг 3: Загрузите cookies

После деплоя нужно загрузить cookies для авторизации на Freelancehunt:

1. **Локально**: Запустите `python save_cookies.py` и сохраните cookies
2. **На Render**: Используйте Render Shell или загрузите файл через SSH:

```bash
# Подключитесь к сервису через SSH
render ssh

# Создайте файл cookies.json в /app/data
# Скопируйте содержимое вашего локального cookies.json
```

Или используйте Render Dashboard → ваш сервис → "Shell" для загрузки файла.

## Шаг 4: Проверьте работу

1. Проверьте логи в Render Dashboard
2. Отправьте команду `/start` боту в Telegram
3. Убедитесь, что бот отвечает

## Важные замечания

- ✅ Файлы в `/app/data` будут сохраняться между перезапусками (благодаря Persistent Disk)
- ⚠️ Cookies нужно будет обновлять периодически (когда истечет срок действия)
- ⚠️ Бот работает в headless режиме (без GUI)
- ✅ Все логи доступны в Render Dashboard

## Обновление проекта

После изменений в коде:

```bash
git add .
git commit -m "Описание изменений"
git push
```

Render автоматически обнаружит изменения и пересоберет проект (если включен Auto-Deploy).

## Устранение проблем

### Бот не запускается
- Проверьте логи в Render Dashboard
- Убедитесь, что все переменные окружения установлены
- Проверьте, что cookies.json существует в /app/data

### Ошибки с браузером
- Убедитесь, что `HEADLESS_BROWSER=true`
- Проверьте логи на наличие ошибок EdgeDriver

### База данных не сохраняется
- Убедитесь, что Persistent Disk подключен
- Проверьте, что `DATABASE_FILE=/app/data/freelancehunt_bot.db`

