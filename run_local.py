"""Local runner for the bot in headless mode."""
import sys
import os
import config

# Force headless mode for local testing
config.HEADLESS_BROWSER = True
os.environ['HEADLESS_BROWSER'] = 'true'

# Import and run bot
if __name__ == '__main__':
    from bot import main
    print("=" * 60)
    print("🤖 ЗАПУСК БОТА ЛОКАЛЬНО (HEADLESS РЕЖИМ)")
    print("=" * 60)
    print()
    print("⚠️  Браузер будет работать в фоновом режиме")
    print("   Для остановки нажмите Ctrl+C")
    print()
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Бот остановлен пользователем")
        sys.exit(0)

