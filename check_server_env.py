"""Diagnostic script to check server environment for browser automation."""
import os
import sys
import subprocess
from pathlib import Path

def check_chrome():
    """Check if Chrome is installed and accessible."""
    print("=" * 60)
    print("🔍 Проверка Chrome...")
    print("=" * 60)
    
    chrome_paths = [
        '/usr/bin/google-chrome-stable',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Найден Chrome: {path}")
            # Check version
            try:
                result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
                print(f"   Версия: {result.stdout.strip()}")
            except Exception as e:
                print(f"   ⚠️ Не удалось получить версию: {e}")
            return True
    
    print("❌ Chrome не найден!")
    return False

def check_xvfb():
    """Check if Xvfb is installed and running."""
    print("\n" + "=" * 60)
    print("🔍 Проверка Xvfb...")
    print("=" * 60)
    
    # Check if Xvfb is installed
    try:
        result = subprocess.run(['which', 'Xvfb'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Xvfb установлен: {result.stdout.strip()}")
        else:
            print("❌ Xvfb не найден!")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки Xvfb: {e}")
        return False
    
    # Check if Xvfb is running
    try:
        result = subprocess.run(['pgrep', '-f', 'Xvfb'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Xvfb запущен (PID: {result.stdout.strip()})")
        else:
            print("⚠️ Xvfb не запущен")
    except Exception as e:
        print(f"⚠️ Не удалось проверить процесс Xvfb: {e}")
    
    # Check DISPLAY
    display = os.environ.get('DISPLAY')
    if display:
        print(f"✅ DISPLAY установлен: {display}")
    else:
        print("❌ DISPLAY не установлен!")
        return False
    
    return True

def check_cookies():
    """Check if cookies file exists."""
    print("\n" + "=" * 60)
    print("🔍 Проверка cookies...")
    print("=" * 60)
    
    import config
    cookies_path = config.COOKIES_PATH
    
    if cookies_path.exists():
        size = cookies_path.stat().st_size
        print(f"✅ Cookies файл найден: {cookies_path}")
        print(f"   Размер: {size} байт")
        
        # Try to read cookies
        try:
            import json
            with open(cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            if isinstance(cookies, list):
                print(f"   Количество cookies: {len(cookies)}")
            elif isinstance(cookies, dict):
                print(f"   Cookies в формате словаря: {len(cookies)} ключей")
            return True
        except Exception as e:
            print(f"   ⚠️ Ошибка чтения cookies: {e}")
            return False
    else:
        print(f"❌ Cookies файл не найден: {cookies_path}")
        return False

def check_dependencies():
    """Check Python dependencies."""
    print("\n" + "=" * 60)
    print("🔍 Проверка зависимостей Python...")
    print("=" * 60)
    
    required = [
        'selenium',
        'undetected_chromedriver',
        'beautifulsoup4',
        'requests',
        'python-telegram-bot',
    ]
    
    all_ok = True
    for dep in required:
        try:
            __import__(dep.replace('-', '_'))
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} не установлен!")
            all_ok = False
    
    return all_ok

def check_browser_init():
    """Try to initialize browser."""
    print("\n" + "=" * 60)
    print("🔍 Попытка инициализации браузера...")
    print("=" * 60)
    
    try:
        from browser_automation import BrowserAutomation
        from database import Database
        
        db = Database()
        browser = BrowserAutomation(db)
        
        print("Попытка создать драйвер...")
        driver = browser.init_driver()
        
        if driver:
            print("✅ Браузер успешно инициализирован!")
            print(f"   Тип: {type(driver).__name__}")
            
            # Try to get a simple page
            try:
                print("Попытка открыть страницу...")
                driver.get("https://www.google.com")
                print(f"✅ Страница открыта: {driver.title}")
            except Exception as e:
                print(f"⚠️ Ошибка открытия страницы: {e}")
            
            driver.quit()
            return True
        else:
            print("❌ Не удалось создать драйвер")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка инициализации браузера: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all checks."""
    print("=" * 60)
    print("🔧 ДИАГНОСТИКА СЕРВЕРНОГО ОКРУЖЕНИЯ")
    print("=" * 60)
    print()
    
    results = {
        'Chrome': check_chrome(),
        'Xvfb': check_xvfb(),
        'Cookies': check_cookies(),
        'Dependencies': check_dependencies(),
        'Browser Init': check_browser_init(),
    }
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ")
    print("=" * 60)
    
    for check, result in results.items():
        status = "✅ OK" if result else "❌ FAIL"
        print(f"{check}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    else:
        print("❌ НАЙДЕНЫ ПРОБЛЕМЫ")
        print("\nРекомендации:")
        if not results['Chrome']:
            print("- Установите Google Chrome в Dockerfile")
        if not results['Xvfb']:
            print("- Установите Xvfb и убедитесь, что он запускается в start.sh")
        if not results['Cookies']:
            print("- Загрузите cookies.json на сервер в /app/data/")
        if not results['Dependencies']:
            print("- Установите недостающие зависимости: pip install -r requirements.txt")
        if not results['Browser Init']:
            print("- Проверьте логи выше для деталей ошибки инициализации браузера")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())

