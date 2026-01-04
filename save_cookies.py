"""Script to save Freelancehunt cookies for bot authentication."""
import json
import time
import os
from glob import glob
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from pathlib import Path
import config


def save_cookies_interactive():
    """Interactive script to save cookies from browser session."""
    print("=" * 60)
    print("Freelancehunt Cookies Saver")
    print("=" * 60)
    print()
    print("Этот скрипт поможет сохранить cookies для авторизации бота.")
    print()
    
    # Initialize Edge browser
    edge_options = Options()
    # Don't use headless mode for this - user needs to login
    edge_options.add_argument('--disable-blink-features=AutomationControlled')
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    edge_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0')
    
    # Try to detect Edge version for better compatibility
    try:
        import subprocess
        import re
        edge_paths = [
            os.path.join(os.environ.get('ProgramFiles', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        ]
        for edge_path in edge_paths:
            if os.path.exists(edge_path):
                try:
                    result = subprocess.run([edge_path, '--version'], capture_output=True, text=True, timeout=5)
                    version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if version_match:
                        print(f"🔍 Обнаружена версия Edge: {version_match.group(1)}")
                except:
                    pass
                break
    except:
        pass
    
    # Try different methods to initialize EdgeDriver
    driver = None
    errors = []
    
    # Method 1: Try with automatic driver management (Selenium 4+)
    try:
        print("🔍 Попытка 1: Автоматическое определение драйвера (Selenium 4+)...")
        # Try without service first
        driver = webdriver.Edge(options=edge_options)
        print("✅ Браузер успешно запущен!")
    except Exception as e1:
        errors.append(f"Метод 1 (авто): {str(e1)}")
        print(f"❌ Метод 1 не сработал: {str(e1)[:100]}")
        
        # Method 2: Try to find EdgeDriver in common locations
        try:
            print("🔍 Попытка 2: Поиск EdgeDriver в стандартных путях...")
            
            # Check Edge installation paths for built-in driver
            edge_paths = [
                os.path.join(os.environ.get('ProgramFiles', ''), 'Microsoft', 'Edge', 'Application'),
                os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Microsoft', 'Edge', 'Application'),
            ]
            
            # Check current directory FIRST - most likely location
            current_dir_driver = os.path.join(os.getcwd(), 'msedgedriver.exe')
            possible_paths = [current_dir_driver] if os.path.exists(current_dir_driver) else []
            
            # Then check Edge installation paths for built-in driver
            for edge_path in edge_paths:
                if os.path.exists(edge_path):
                    # Check for msedgedriver.exe in Edge folder
                    driver_in_edge = os.path.join(edge_path, 'msedgedriver.exe')
                    if os.path.exists(driver_in_edge):
                        possible_paths.append(driver_in_edge)
                    # Also check subdirectories
                    try:
                        for item in os.listdir(edge_path):
                            sub_path = os.path.join(edge_path, item, 'msedgedriver.exe')
                            if os.path.exists(sub_path):
                                possible_paths.append(sub_path)
                    except:
                        pass
            
            # Add other common paths
            possible_paths.extend([
                os.path.join(os.path.expanduser('~'), '.wdm', 'drivers', 'edgedriver', '*', 'msedgedriver.exe'),
                'msedgedriver.exe',  # PATH
            ])
            
            driver_path = None
            for path in possible_paths:
                if '*' in path:
                    matches = glob(path)
                    if matches:
                        driver_path = matches[0]
                        print(f"✅ Найден драйвер: {driver_path}")
                        break
                elif os.path.exists(path):
                    driver_path = path
                    print(f"✅ Найден драйвер: {driver_path}")
                    break
            
            if driver_path:
                service = Service(executable_path=driver_path)
                driver = webdriver.Edge(service=service, options=edge_options)
                print("✅ Браузер успешно запущен!")
            else:
                raise Exception("EdgeDriver не найден в стандартных путях")
                
        except Exception as e2:
            errors.append(f"Метод 2 (поиск): {str(e2)}")
            print(f"❌ Метод 2 не сработал: {str(e2)[:100]}")
            
                # Method 3: Try using Service with debug output
            try:
                print("🔍 Попытка 3: Использование Service с отладкой...")
                # Enable logging to see what's happening
                import logging
                selenium_logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
                selenium_logger.setLevel(logging.WARNING)
                
                service = Service()  # Let Selenium Manager find driver
                # Add verbose logging
                service.service_args = ['--verbose']
                driver = webdriver.Edge(service=service, options=edge_options)
                print("✅ Браузер успешно запущен!")
            except Exception as e3:
                errors.append(f"Метод 3 (Service): {str(e3)}")
                print(f"❌ Метод 3 не сработал: {str(e3)[:100]}")
                
                # Method 4: Try downloading driver manually with webdriver-manager
                try:
                    print("🔍 Попытка 4: Использование webdriver-manager (требуется интернет)...")
                    from webdriver_manager.microsoft import EdgeChromiumDriverManager
                    print("   Скачивание драйвера...")
                    # Try to use cache first, then download if needed
                    driver_path = EdgeChromiumDriverManager().install()
                    service = Service(executable_path=driver_path)
                    driver = webdriver.Edge(service=service, options=edge_options)
                    print("✅ Браузер успешно запущен!")
                except Exception as e4:
                    errors.append(f"Метод 4 (webdriver-manager): {str(e4)}")
                    print(f"❌ Метод 4 не сработал: {str(e4)[:100]}")
                    
                    # Method 5: Try to use existing msedgedriver if it's in PATH
                    try:
                        print("🔍 Попытка 5: Поиск msedgedriver в PATH...")
                        import shutil
                        driver_exe = shutil.which('msedgedriver')
                        if driver_exe:
                            print(f"   Найден драйвер в PATH: {driver_exe}")
                            service = Service(executable_path=driver_exe)
                            driver = webdriver.Edge(service=service, options=edge_options)
                            print("✅ Браузер успешно запущен!")
                        else:
                            raise Exception("msedgedriver не найден в PATH")
                    except Exception as e5:
                        errors.append(f"Метод 5 (PATH): {str(e5)}")
                        
                        # All methods failed
                        print("\n" + "=" * 60)
                        print("❌ Не удалось запустить браузер Edge")
                        print("=" * 60)
                        print("\nВсе попытки:")
                        for i, error in enumerate(errors, 1):
                            print(f"  {i}. {error}")
                        print("\n💡 Решения:")
                        print("1. Запустите скрипт для автоматического скачивания:")
                        print("   python download_edgedriver.py")
                        print("2. Или скачайте EdgeDriver вручную:")
                        print("   https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
                        print("3. Поместите msedgedriver.exe в папку проекта")
                        print("4. Или добавьте msedgedriver.exe в системную переменную PATH")
                        print("5. Проверьте интернет-соединение (для webdriver-manager)")
                        print("6. Убедитесь, что Microsoft Edge установлен и обновлен")
                        print("\n📝 После установки драйвера, запустите скрипт снова.")
                        return False
    
    try:
        # Open Freelancehunt
        print("🌐 Открываю Freelancehunt...")
        driver.get(config.FREELANCEHUNT_URL)
        time.sleep(3)
        
        print()
        print("=" * 60)
        print("⚠️  ВАЖНО:")
        print("=" * 60)
        print("1. В открывшемся браузере Edge авторизуйтесь на Freelancehunt")
        print("2. Вы можете войти через Google аккаунт (кнопка 'Войти через Google')")
        print("3. Убедитесь, что вы полностью авторизованы и видите главную страницу")
        print("4. После успешной авторизации вернитесь сюда и нажмите Enter")
        print("=" * 60)
        print()
        print("⏳ Ожидаю авторизации...")
        print("   (Процесс входа через Google может занять некоторое время)")
        print()
        
        input("Нажмите Enter после успешной авторизации...")
        
        # Check if user is logged in by checking current URL
        current_url = driver.current_url
        print(f"📄 Текущий URL: {current_url}")
        
        # Get cookies
        print("📥 Получаю cookies...")
        cookies = driver.get_cookies()
        
        if not cookies:
            print("❌ Cookies не найдены. Убедитесь, что вы авторизованы.")
            return False
        
        # Check if we have authentication cookies
        auth_cookies = [c for c in cookies if 'auth' in c.get('name', '').lower() or 'session' in c.get('name', '').lower() or 'token' in c.get('name', '').lower()]
        if not auth_cookies:
            print("⚠️  Предупреждение: Не найдено явных cookies авторизации.")
            print("   Это может быть нормально, если сайт использует другие методы.")
        
        # Save cookies
        cookies_path = config.COOKIES_PATH
        with open(cookies_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Cookies успешно сохранены в: {cookies_path}")
        print(f"   Найдено {len(cookies)} cookies")
        if auth_cookies:
            print(f"   В том числе {len(auth_cookies)} cookies авторизации")
        print()
        print("Теперь вы можете запустить бота: python bot.py")
        
        return True
        
    except KeyboardInterrupt:
        print("\n❌ Прервано пользователем")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        print("\n🔄 Закрываю браузер...")
        driver.quit()
        time.sleep(1)


if __name__ == '__main__':
    success = save_cookies_interactive()
    if not success:
        exit(1)

