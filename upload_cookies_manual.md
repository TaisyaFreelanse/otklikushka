# 📤 Загрузка cookies.json на Render сервер

## Способ 1: Через Render Shell (Рекомендуется)

1. Откройте Render Dashboard:
   https://dashboard.render.com/web/srv-d5crfrtactks73csled0

2. Нажмите **"Shell"** в левом меню

3. Выполните команды:
   ```bash
   mkdir -p /app/data
   cd /app/data
   nano cookies.json
   ```

4. Вставьте содержимое вашего локального `cookies.json`:
   - В nano: `Ctrl+Shift+V` для вставки (или правая кнопка мыши)
   - Или скопируйте весь файл и вставьте

5. Сохраните файл:
   - `Ctrl+O` (сохранить)
   - `Enter` (подтвердить имя файла)
   - `Ctrl+X` (выйти)

6. Проверьте, что файл создан:
   ```bash
   ls -lh /app/data/cookies.json
   cat /app/data/cookies.json | head -20
   ```

7. Перезапустите сервис (в Dashboard → "Manual Deploy" → "Deploy latest commit")

## Способ 2: Через SSH (если настроен ключ)

1. Подключитесь через SSH:
   ```bash
   ssh srv-d5crfrtactks73csled0@ssh.oregon.render.com
   ```

2. Создайте директорию и файл:
   ```bash
   mkdir -p /app/data
   cd /app/data
   nano cookies.json
   ```

3. Вставьте содержимое cookies.json и сохраните

4. Проверьте файл:
   ```bash
   ls -lh cookies.json
   ```

## Способ 3: Через Python скрипт

Запустите локально:
```bash
python upload_cookies_to_render.py
```

⚠️ **Примечание**: Для работы скрипта нужен SSH ключ, настроенный в Render Dashboard.

## ✅ Проверка после загрузки

После загрузки cookies проверьте логи:
```bash
# В Render Shell или через Dashboard → Logs
tail -f /var/log/render.log
```

Бот должен автоматически подхватить cookies при следующей проверке проектов.

