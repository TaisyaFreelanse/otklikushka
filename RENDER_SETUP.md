# ✅ Проект развернут на Render!

## 📊 Информация о сервисе

- **Название**: `freelancehunt-bot`
- **URL**: https://freelancehunt-bot-jpyl.onrender.com
- **Dashboard**: https://dashboard.render.com/web/srv-d5crfrtactks73csled0
- **SSH**: `srv-d5crfrtactks73csled0@ssh.oregon.render.com`
- **Статус**: Деплой в процессе

## ✅ Что уже настроено

1. ✅ Веб-сервис создан на Render
2. ✅ Docker образ настроен
3. ✅ Переменные окружения установлены:
   - `TELEGRAM_BOT_TOKEN` - ваш токен бота
   - `HEADLESS_BROWSER=true` - браузер в фоновом режиме
   - `BROWSER_TYPE=edge` - используется Edge
   - `DATABASE_FILE=/app/data/freelancehunt_bot.db`
   - `COOKIES_FILE=/app/data/cookies.json`
   - `CHECK_INTERVAL=60`
   - `MAX_BID_AMOUNT=27000`
4. ✅ Auto-deploy включен (автоматический деплой при push в main)
5. ✅ Health check endpoint добавлен (порт 8000)

## ⚠️ Что нужно сделать вручную

### 1. Добавить Persistent Disk (ВАЖНО!)

Для сохранения базы данных и cookies между перезапусками:

1. Откройте Dashboard: https://dashboard.render.com/web/srv-d5crfrtactks73csled0
2. Перейдите в раздел **"Disks"** (в левом меню)
3. Нажмите **"Add Disk"**
4. Настройте:
   - **Name**: `bot-data`
   - **Mount Path**: `/app/data`
   - **Size**: 1 GB
5. Нажмите **"Add Disk"**

### 2. Загрузить cookies.json

После добавления Persistent Disk и первого запуска:

**Способ 1: Через Render Shell (рекомендуется)**

1. В Dashboard нажмите **"Shell"** (в левом меню)
2. Выполните команды:
   ```bash
   cd /app/data
   nano cookies.json
   ```
3. Вставьте содержимое вашего локального `cookies.json`
   - В nano: `Ctrl+Shift+V` для вставки
4. Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`
5. Перезапустите сервис в Dashboard (кнопка "Manual Deploy")

**Способ 2: Через SSH**

```bash
ssh srv-d5crfrtactks73csled0@ssh.oregon.render.com
cd /app/data
# Создайте файл cookies.json с содержимым вашего локального файла
```

### 3. Проверить работу

1. Дождитесь завершения деплоя (статус "live")
2. Проверьте логи в Dashboard → "Logs"
3. Отправьте `/start` боту в Telegram
4. Убедитесь, что бот отвечает

## 📝 Полезные команды

### Просмотр логов
```bash
# В Render Dashboard → Logs
# Или через MCP:
mcp_render_list_logs resource=['srv-d5crfrtactks73csled0']
```

### Перезапуск сервиса
- В Dashboard: "Manual Deploy" → "Deploy latest commit"

### Обновление переменных окружения
- В Dashboard: "Environment" → добавьте/измените переменные
- Или через MCP: `mcp_render_update_environment_variables`

## 🔍 Мониторинг

- **Логи**: https://dashboard.render.com/web/srv-d5crfrtactks73csled0/logs
- **Метрики**: https://dashboard.render.com/web/srv-d5crfrtactks73csled0/metrics
- **SSH доступ**: `ssh srv-d5crfrtactks73csled0@ssh.oregon.render.com`

## ⚠️ Важные замечания

1. **Cookies нужно обновлять периодически** (когда истечет срок действия)
2. **База данных сохраняется** только если добавлен Persistent Disk
3. **Бот работает 24/7** пока сервис активен
4. **На бесплатном плане** сервис может "засыпать" после 15 минут бездействия
5. **Логи доступны** в реальном времени в Dashboard

## 🚀 Обновление кода

После изменений в коде:

```bash
git add .
git commit -m "Описание изменений"
git push
```

Render автоматически обнаружит изменения и пересоберет проект (Auto-Deploy включен).

## 📞 Поддержка

При проблемах:
1. Проверьте логи в Dashboard
2. Убедитесь, что Persistent Disk добавлен
3. Проверьте, что cookies.json загружен
4. Убедитесь, что все переменные окружения установлены

---

**Статус деплоя**: Проверьте в Dashboard или через:
```bash
mcp_render_get_deploy serviceId="srv-d5crfrtactks73csled0" deployId="dep-d5crg4hr7b3s73ai14k0"
```

