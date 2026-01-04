# 📤 Инструкция: Загрузка cookies.json на Render сервер

## ✅ Статус
- Persistent Disk уже настроен (`/app/data`)
- Сервис работает
- Нужно загрузить cookies.json

## 🚀 Способ 1: Через Render Shell (РЕКОМЕНДУЕТСЯ)

1. **Откройте Render Dashboard:**
   https://dashboard.render.com/web/srv-d5crfrtactks73csled0

2. **Нажмите "Shell"** в левом меню

3. **Выполните команды:**
   ```bash
   mkdir -p /app/data
   cd /app/data
   ```

4. **Создайте файл cookies.json:**
   ```bash
   cat > cookies.json << 'EOF'
   ```
   
5. **Вставьте содержимое cookies.json** (скопируйте весь файл cookies.json с вашего компьютера)

6. **Завершите создание файла:**
   ```bash
   EOF
   ```

7. **Проверьте файл:**
   ```bash
   ls -lh /app/data/cookies.json
   cat /app/data/cookies.json | head -5
   ```
   
   Должно показать размер файла и первые строки JSON.

8. **Перезапустите сервис:**
   - В Dashboard → "Manual Deploy" → "Deploy latest commit"
   - Или просто перезапустите через кнопку "Restart"

## 🔍 Альтернативный способ через nano:

1. В Render Shell выполните:
   ```bash
   mkdir -p /app/data
   nano /app/data/cookies.json
   ```

2. Вставьте содержимое cookies.json (Ctrl+Shift+V или правая кнопка мыши)

3. Сохраните: Ctrl+O, Enter, Ctrl+X

4. Проверьте: `ls -lh /app/data/cookies.json`

## ✅ Проверка после загрузки

После загрузки cookies проверьте логи бота:

```bash
# В Render Shell или через Dashboard → Logs
tail -f /proc/1/fd/1
```

Или просто проверьте логи в Dashboard → Logs. Бот должен автоматически подхватить cookies при следующей проверке проектов.

## 🔄 Что дальше?

После загрузки cookies:
1. Бот автоматически использует cookies при проверке проектов
2. Проверьте работу через команду `/start` в Telegram боте
3. Бот должен начать проверять проекты и делать отклики

## ⚠️ Важно

- Cookies нужно обновлять периодически (когда истечет срок действия)
- Файл должен быть в формате JSON
- Проверьте, что файл содержит все необходимые cookies (rmt2, sid2, rmp и т.д.)

