"""Test script to verify scraping functionality locally."""
import sys
import time
import os
from pathlib import Path
import config
from database import Database
from browser_automation import BrowserAutomation
from freelancehunt_scraper import FreelancehuntScraper

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_scraping():
    """Test scraping projects from Freelancehunt."""
    print("=" * 60)
    print("🧪 ТЕСТОВЫЙ СКРИПТ ДЛЯ ПРОВЕРКИ ПАРСИНГА ПРОЕКТОВ")
    print("=" * 60)
    print()
    
    # Initialize database
    db = Database()
    
    # Initialize browser (non-headless for local testing)
    print("🔄 Инициализация браузера...")
    original_headless = config.HEADLESS_BROWSER
    config.HEADLESS_BROWSER = False  # Force non-headless for local testing
    
    browser = BrowserAutomation(db)
    
    try:
        browser.driver = browser.init_driver()
        print("✅ Браузер запущен (не в фоновом режиме для наблюдения)")
    except Exception as e:
        print(f"❌ Ошибка запуска браузера: {e}")
        return False
    
    # Load cookies
    print("\n📥 Загрузка cookies...")
    if not browser.load_cookies():
        print("❌ Не удалось загрузить cookies")
        print("   Запустите save_cookies.py для сохранения cookies")
        browser.close()
        return False
    print("✅ Cookies загружены")
    
    # Initialize scraper
    print("\n🔍 Инициализация скрапера...")
    scraper = FreelancehuntScraper(db, browser=browser)
    
    # Get categories (use development categories)
    dev_categories = [
        'Backend', 'Frontend', 'Full Stack', 'Mobile Development',
        'iOS Development', 'Android Development', 'Web Development',
        'Desktop Development', 'Game Development', 'DevOps',
        'Database', 'API Development', 'REST API', 'GraphQL',
        'Node.js', 'Python', 'PHP', 'Java', 'C#', 'C++', 'Go',
        'Ruby', 'React', 'Vue.js', 'Angular', 'JavaScript', 'TypeScript',
        'HTML/CSS', 'WordPress', 'Shopify', 'Laravel', 'Django',
        'Flask', 'Express.js', 'Next.js', 'Nuxt.js'
    ]
    
    print(f"\n📋 Ищем проекты по категориям: {len(dev_categories)} категорий")
    print("   (Backend, Frontend, Mobile, Web Development, etc.)")
    print()
    
    # Test scraping
    print("🔍 Начинаю поиск новых проектов...")
    print("   Это может занять 1-2 минуты (ожидание Cloudflare)...")
    print()
    
    start_time = time.time()
    
    try:
        new_projects = scraper.get_new_projects(categories=dev_categories)
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print(f"✅ ПОИСК ЗАВЕРШЕН за {elapsed_time:.1f} секунд")
        print("=" * 60)
        print()
        
        if new_projects:
            print(f"🎉 Найдено новых проектов: {len(new_projects)}")
            print()
            
            for i, project in enumerate(new_projects[:10], 1):  # Show first 10
                print(f"{i}. 📝 {project.get('title', 'Без названия')[:60]}")
                print(f"   💰 Бюджет: {project.get('budget', 'Не указан')}")
                print(f"   📁 Категория: {project.get('category', 'Не указана')}")
                print(f"   📅 Срок: {project.get('deadline', 'Не указан')} дней")
                print(f"   🔗 {project.get('url', '')}")
                print()
            
            if len(new_projects) > 10:
                print(f"   ... и ещё {len(new_projects) - 10} проектов")
                print()
        else:
            print("⚠️ Новых проектов не найдено")
            print("   Возможные причины:")
            print("   - Все проекты уже были сохранены ранее")
            print("   - Cloudflare блокирует запросы")
            print("   - Проблемы с парсингом страницы")
            print()
        
        # Check other projects
        print("🔍 Проверяю проекты вне категорий...")
        other_projects = scraper.get_new_projects(categories=None)  # Get all projects
        
        if other_projects:
            print(f"📊 Всего проектов найдено: {len(other_projects)}")
            print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при поиске проектов: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        try:
            if '--keep-open' in sys.argv:
                input("\nНажмите Enter для закрытия браузера...")
        except (EOFError, KeyboardInterrupt):
            pass
        browser.close()
        config.HEADLESS_BROWSER = original_headless


def main():
    """Main test function."""
    try:
        success = test_scraping()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        return 1
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

