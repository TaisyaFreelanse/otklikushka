"""Экспорт cookies и Chrome профиля с локальной машины для сервера."""
import json
import os
import shutil
from pathlib import Path
from selenium import webdriver
import undetected_chromedriver as uc
import config

def export_cookies_and_profile():
    """Экспортировать cookies и профиль Chrome с локальной машины."""
    print("=" * 60)
    print("Экспорт cookies и Chrome профиля")
    print("=" * 60)
    print()
    print("Этот скрипт поможет экспортировать:")
    print("1. Cookies из вашего локального браузера")
    print("2. Chrome профиль (если нужно)")
    print()
    
    # Инициализируем браузер в не-headless режиме
    print("Инициализация браузера...")
    try:
        options = uc.ChromeOptions()
        # Не используем headless - нужен реальный браузер
        # Используем тот же профиль, что и на сервере (если есть)
        driver = uc.Chrome(options=options, use_subprocess=False)
    except Exception as e:
        print(f"Ошибка инициализации браузера: {e}")
        print("Попробуйте использовать save_cookies.py вместо этого скрипта")
        return
    
    try:
        print("Откройте браузер и войдите на Freelancehunt...")
        print("1. Зайдите на https://freelancehunt.com")
        print("2. Убедитесь, что вы авторизованы")
        print("3. Подождите, пока Cloudflare пропустит вас")
        print()
        input("Нажмите Enter, когда будете готовы продолжить...")
        
        # Открываем сайт
        driver.get("https://freelancehunt.com")
        print("Ждём загрузки страницы...")
        
        # Ждём, пока страница загрузится (проверяем, что Cloudflare пропустил)
        import time
        max_wait = 30
        waited = 0
        while waited < max_wait:
            if "Just a moment" not in driver.page_source:
                print("✅ Страница загружена, Cloudflare пропустил!")
                break
            time.sleep(2)
            waited += 2
            print(f"Ожидание... ({waited}s/{max_wait}s)")
        
        if waited >= max_wait:
            print("⚠️ Внимание: Cloudflare challenge может всё ещё быть активен")
            response = input("Продолжить экспорт? (y/n): ")
            if response.lower() != 'y':
                print("Отменено")
                return
        
        # Получаем cookies
        print("\nЭкспорт cookies...")
        cookies = driver.get_cookies()
        
        # Сохраняем cookies
        cookies_path = Path("cookies_local_export.json")
        with open(cookies_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Cookies сохранены в: {cookies_path}")
        print(f"   Найдено {len(cookies)} cookies")
        
        # Выводим информацию о cookies
        print("\nИнформация о cookies:")
        for cookie in cookies[:5]:  # Первые 5
            print(f"  - {cookie.get('name', 'N/A')}: {cookie.get('domain', 'N/A')}")
        if len(cookies) > 5:
            print(f"  ... и ещё {len(cookies) - 5} cookies")
        
        # Экспорт профиля Chrome (опционально)
        print("\n" + "=" * 60)
        export_profile = input("Экспортировать Chrome профиль? Это может помочь с Cloudflare (y/n): ")
        
        if export_profile.lower() == 'y':
            # Находим профиль Chrome
            profile_dir = driver.capabilities.get('chrome', {}).get('userDataDir')
            if profile_dir:
                print(f"Найден профиль: {profile_dir}")
                profile_export_path = Path("chrome_profile_export")
                
                # Копируем важные файлы профиля
                important_files = [
                    'Preferences',
                    'Cookies',
                    'Local Storage',
                    'Session Storage'
                ]
                
                print("Экспорт важных файлов профиля...")
                # Это сложнее, так как нужно получить путь к профилю из undetected-chromedriver
                print("⚠️ Экспорт профиля требует дополнительной настройки")
                print("   Рекомендуется просто обновить cookies на сервере")
        
        print("\n" + "=" * 60)
        print("✅ ЭКСПОРТ ЗАВЕРШЁН")
        print("=" * 60)
        print()
        print("Следующие шаги:")
        print(f"1. Файл {cookies_path} готов для загрузки на сервер")
        print("2. Загрузите этот файл на Render сервер:")
        print("   - Через Render Dashboard → Shell")
        print("   - Или через: scp cookies_local_export.json user@server:/app/data/cookies.json")
        print()
        print("3. На сервере переименуйте файл:")
        print("   mv cookies_local_export.json /app/data/cookies.json")
        print()
        print("4. Перезапустите сервис на Render")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        input("\nНажмите Enter, чтобы закрыть браузер...")
        driver.quit()

if __name__ == "__main__":
    export_cookies_and_profile()

