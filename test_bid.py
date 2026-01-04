"""Test script to verify bid functionality on a specific project."""
import asyncio
import sys
import time
from pathlib import Path
import config
from database import Database
from browser_automation import BrowserAutomation
from freelancehunt_scraper import FreelancehuntScraper

# Test project URL
TEST_PROJECT_URL = "https://freelancehunt.com/project/dizayn-e-commerce-shtuchni-yalinki-igrashki-girlyandi/1591331.html"


def test_project_info(scraper: FreelancehuntScraper, project_url: str):
    """Extract and display project information."""
    print("=" * 60)
    print("📋 Получение информации о проекте...")
    print("=" * 60)
    
    try:
        scraper.load_cookies()
        response = scraper.session.get(project_url, timeout=30)
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Try to extract project info
        title = soup.find('h1')
        if title:
            print(f"📝 Название: {title.get_text(strip=True)}")
        
        # Look for budget
        budget_elem = soup.find(string=lambda text: text and ('грн' in text.lower() or 'uah' in text.lower() or '₴' in text))
        if budget_elem:
            budget_text = budget_elem if isinstance(budget_elem, str) else budget_elem.get_text()
            print(f"💰 Бюджет: {budget_text[:100]}")
        
        # Look for deadline
        deadline_elem = soup.find(string=lambda text: text and ('дн' in text.lower() or 'день' in text.lower() or 'days' in text.lower()))
        if deadline_elem:
            deadline_text = deadline_elem if isinstance(deadline_elem, str) else deadline_elem.get_text()
            print(f"📅 Срок: {deadline_text[:100]}")
        
        print(f"\n🔗 URL: {project_url}")
        print("=" * 60)
        
    except Exception as e:
        print(f"⚠️ Ошибка при получении информации: {e}")


def test_bid_submission(browser: BrowserAutomation, scraper: FreelancehuntScraper, project_url: str):
    """Test bid submission on a project."""
    print("\n" + "=" * 60)
    print("🤖 Тестирование отправки ставки...")
    print("=" * 60)
    print()
    print("⚠️  ВНИМАНИЕ:")
    print("   Этот скрипт создаст РЕАЛЬНЫЙ отклик на проект!")
    print("   Убедитесь, что вы хотите это сделать.")
    print()
    
    response = input("Продолжить? (yes/no): ").strip().lower()
    if response not in ['yes', 'y', 'да', 'д']:
        print("❌ Отменено пользователем")
        return False
    
    print("\n🔄 Инициализация браузера...")
    if not browser.driver:
        try:
            # Force non-headless mode for testing
            original_headless = config.HEADLESS_BROWSER
            config.HEADLESS_BROWSER = False
            
            browser.driver = browser.init_driver()
            print("✅ Браузер запущен (не в фоновом режиме для наблюдения)")
            
            # Restore original setting
            config.HEADLESS_BROWSER = original_headless
        except Exception as e:
            print(f"❌ Ошибка запуска браузера: {e}")
            return False
    
    print("📥 Загрузка cookies...")
    if not browser.load_cookies():
        print("❌ Не удалось загрузить cookies")
        print("   Запустите save_cookies.py для сохранения cookies")
        return False
    
    print("✅ Cookies загружены")
    
    print(f"\n🌐 Открываю проект: {project_url}")
    
    try:
        # Extract project ID
        project_id = scraper.extract_project_id(project_url)
        print(f"📌 ID проекта: {project_id}")
        
        # Try to get real project info from page
        print("\n📋 Получаю информацию о проекте со страницы...")
        browser.driver.get(project_url)
        time.sleep(3)  # Wait for page to load
        
        # Try to extract budget and deadline from page
        project_budget = None
        project_deadline = None
        
        try:
            page_source = browser.driver.page_source
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Look for budget
            budget_text = None
            for text in soup.stripped_strings:
                if 'грн' in text.lower() or 'uah' in text.lower() or '₴' in text:
                    budget_text = text
                    break
            
            if budget_text:
                project_budget = scraper.parse_budget(budget_text)
                if project_budget:
                    print(f"💰 Бюджет проекта: {project_budget:.0f} грн")
            
            # Look for deadline
            deadline_text = None
            for text in soup.stripped_strings:
                if any(word in text.lower() for word in ['дн', 'день', 'дней', 'days', 'day']):
                    deadline_text = text
                    break
            
            if deadline_text:
                project_deadline = scraper.parse_deadline(deadline_text)
                if project_deadline:
                    print(f"📅 Срок проекта: {project_deadline} дней")
        except Exception as e:
            print(f"⚠️ Не удалось извлечь информацию о проекте: {e}")
        
        # Use real budget/deadline if found, otherwise use defaults
        if not project_budget:
            project_budget = 15000.0
            print(f"💰 Использую тестовый бюджет: {project_budget:.0f} грн")
        
        if not project_deadline:
            project_deadline = 14
            print(f"📅 Использую тестовый срок: {project_deadline} дней")
        
        # Calculate bid amount and deadline
        calculated_amount = browser.calculate_bid_amount(project_budget)
        calculated_deadline = browser.calculate_deadline(project_deadline)
        
        print(f"\n💡 Рассчитанная ставка:")
        print(f"   💰 Сумма: {calculated_amount:.0f} грн (на основе бюджета {project_budget:.0f} грн)")
        print(f"   📅 Срок: {calculated_deadline} дней (на основе {project_deadline} дней)")
        
        print("\n" + "=" * 60)
        print("🚀 Начинаю отправку ставки...")
        print("=" * 60)
        print()
        print("Браузер уже открыт, наблюдайте процесс...")
        print()
        
        # Submit bid
        success, message, bid_amount, bid_deadline = browser.submit_bid(
            project_url,
            project_budget,  # Use real or test budget
            project_deadline  # Use real or test deadline
        )
        
        print("\n" + "=" * 60)
        if success:
            print("✅ СТАВКА УСПЕШНО ОТПРАВЛЕНА!")
            print("=" * 60)
        else:
            print("❌ ОШИБКА ПРИ ОТПРАВКЕ СТАВКИ")
            print("=" * 60)
        
        print(f"\n📊 Результаты:")
        print(f"   Статус: {'✅ Успешно' if success else '❌ Ошибка'}")
        print(f"   Сумма: {bid_amount:.0f} грн")
        print(f"   Срок: {bid_deadline} дней")
        print(f"   Сообщение: {message}")
        print()
        
        if success:
            print("💡 Проверьте на сайте Freelancehunt, что ставка действительно отправлена.")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        input("\nНажмите Enter для закрытия браузера...")
        browser.close()


def main():
    """Main test function."""
    print("=" * 60)
    print("🧪 ТЕСТОВЫЙ СКРИПТ ДЛЯ ПРОВЕРКИ ОТКЛИКА")
    print("=" * 60)
    print()
    print(f"Тестируемый проект: {TEST_PROJECT_URL}")
    print()
    
    # Initialize database
    db = Database()
    
    # Initialize scraper
    scraper = FreelancehuntScraper(db)
    
    # Get project info
    test_project_info(scraper, TEST_PROJECT_URL)
    
    # Initialize browser
    browser = BrowserAutomation(db)
    
    # Test bid submission
    success = test_bid_submission(browser, scraper, TEST_PROJECT_URL)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО")
    else:
        print("❌ ТЕСТ ЗАВЕРШЕН С ОШИБКАМИ")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

