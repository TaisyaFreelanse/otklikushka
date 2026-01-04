"""Telegram bot for managing Freelancehunt auto-bidding."""
import asyncio
import logging
from datetime import datetime
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    JobQueue,
)
from telegram.constants import ParseMode
from telegram.error import Conflict, NetworkError, RetryAfter
import sys
import config
from database import Database
from freelancehunt_scraper import FreelancehuntScraper
from browser_automation import BrowserAutomation

# Start health check server for Render
try:
    from health_check import start_health_check_server
    start_health_check_server(8000)
except:
    pass

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global instances
db = Database()
scraper = None
browser = None
bot_application = None

# Development categories for Freelancehunt
DEV_CATEGORIES = [
    # Основные категории программирования
    "Программирование",
    "Веб-разработка",
    "Веб-программирование",
    
    # Языки программирования
    "PHP",
    "JavaScript",
    "Javascript и Typescript",
    "TypeScript",
    "Python",
    "Java",
    "C#",
    "C++",
    "C и C++",
    "Ruby",
    "Go",
    "Kotlin",
    "Swift",
    "Dart",
    "Node.js",
    
    # Веб-технологии
    "HTML и CSS верстка",
    "HTML/CSS",
    "Sass/SCSS",
    "Bootstrap",
    "Tailwind CSS",
    "React",
    "Vue.js",
    "Angular",
    
    # Backend фреймворки
    "Laravel",
    "Django",
    "Flask",
    "ASP.NET",
    "Spring",
    "Symfony",
    
    # Мобильная разработка
    "Мобильная разработка",
    "Разработка под iOS (iPhone и iPad)",
    "iOS разработка",
    "Разработка под Android",
    "Android разработка",
    "Гибридные мобильные приложения",
    "React Native",
    "Flutter",
    "Xamarin",
    
    # Специализации
    "Бэкенд разработка",
    "Frontend разработка",
    "Full Stack разработка",
    "API разработка",
    "REST API",
    "GraphQL",
    "Десктопные приложения",
    
    # Базы данных
    "Базы данных и SQL",
    "Базы данных",
    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "Redis",
    
    # CMS
    "CMS",
    "WordPress",
    "OpenCart",
    "Drupal",
    "Joomla",
    "1C-Битрикс",
    
    # E-commerce
    "E-commerce",
    "Magento",
    "PrestaShop",
    "Shopify",
    
    # Дополнительные категории из скриншотов
    "AI и машинное обучение",
    "AR и VR разработка",
    "Криптовалюта и blockchain",
    "Парсинг данных",
    "Разработка ботов",
    "Разработка игр",
    "Тестирование и QA",
    
    # Дизайн (если нужен)
    "Веб-дизайн",
    "UI/UX дизайн",
    "3D моделирование и визуализация",
    "Векторная графика",
    
    # DevOps
    "DevOps",
    "Docker",
    "Kubernetes",
    "CI/CD",
    "Git",
    "Linux",
    "AWS",
    "Azure",
    "Google Cloud",
]


def check_user_access(update: Update) -> bool:
    """Check if user has access to bot."""
    if not config.ALLOWED_USER_IDS:
        return True
    user_id = update.effective_user.id
    return user_id in config.ALLOWED_USER_IDS


def get_main_keyboard():
    """Create main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Статус", callback_data="status"),
            InlineKeyboardButton("📋 Последние отклики", callback_data="last_bids"),
        ],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton("🔄 Вкл/Выкл", callback_data="toggle"),
        ],
        [
            InlineKeyboardButton("📁 Категории", callback_data="categories"),
            InlineKeyboardButton("🔍 Другие проекты", callback_data="other_projects"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    if not check_user_access(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    # Initialize dev categories if not set
    categories = db.get_categories()
    if not categories:
        db.set_categories(DEV_CATEGORIES)
        categories = DEV_CATEGORIES
    
    enabled = db.get_enabled()
    status_text = "🟢 Включен" if enabled else "🔴 Выключен"
    last_check = db.get_last_check_time()
    if last_check:
        # Format: "сегодня 02:01" or "вчера 15:30" or "04.01 12:00"
        now = datetime.now()
        # Handle timezone-aware datetime
        if last_check.tzinfo:
            now = now.replace(tzinfo=last_check.tzinfo)
        diff = now - last_check
        if diff.days == 0:
            last_check_text = f"сегодня {last_check.strftime('%H:%M')}"
        elif diff.days == 1:
            last_check_text = f"вчера {last_check.strftime('%H:%M')}"
        else:
            last_check_text = last_check.strftime("%d.%m %H:%M")
    else:
        last_check_text = "Никогда"
    
    categories_count = len(categories) if categories else 0
    
    message = f"""
🤖 <b>Freelancehunt Auto-Bid Bot</b>

📊 <b>Статус:</b> {status_text}
🕐 <b>Последняя проверка:</b> {last_check_text}
📁 <b>Категории:</b> {categories_count} категорий разработки

Бот автоматически проверяет новые проекты каждые {config.CHECK_INTERVAL} секунд.

<i>Используйте кнопки ниже для управления ботом:</i>
"""
    await update.message.reply_text(
        message, 
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    if not check_user_access(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    enabled = db.get_enabled()
    status_text = "🟢 Включен" if enabled else "🔴 Выключен"
    
    last_check = db.get_last_check_time()
    last_check_text = last_check.strftime("%Y-%m-%d %H:%M:%S") if last_check else "Никогда"
    
    categories = db.get_categories()
    categories_count = len(categories) if categories else 0
    
    # Get stats
    last_bids = db.get_last_bids(5)
    total_bids = len(db.get_last_bids(1000))
    pending_bids = len(db.get_pending_bids())
    
    message = f"""
📊 <b>Статус бота</b>

🔄 <b>Автоотклик:</b> {status_text}
🕐 <b>Последняя проверка:</b> {last_check_text}
📁 <b>Категории:</b> {categories_count} категорий

📈 <b>Статистика:</b>
• Всего откликов: {total_bids}
• В ожидании: {pending_bids}
• Последних: {len(last_bids)}
"""
    await update.message.reply_text(
        message, 
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )


async def last_bids_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /last_bids command."""
    if not check_user_access(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    limit = 10
    if context.args and context.args[0].isdigit():
        limit = min(int(context.args[0]), 20)
    
    bids = db.get_last_bids(limit)
    
    if not bids:
        await update.message.reply_text(
            "📭 Пока нет откликов.",
            reply_markup=get_main_keyboard()
        )
        return
    
    message = "📋 <b>Последние отклики:</b>\n\n"
    
    for i, bid in enumerate(bids, 1):
        status_emoji = {
            'pending': '⏳',
            'sent': '✅',
            'failed': '❌'
        }.get(bid['status'], '❓')
        
        created_at = datetime.fromisoformat(bid['created_at']) if bid['created_at'] else None
        time_str = created_at.strftime("%d.%m %H:%M") if created_at else "?"
        
        title = bid['title'][:50] + "..." if len(bid['title']) > 50 else bid['title']
        
        message += f"""
{status_emoji} <b>{i}.</b> {title}
💰 {bid['bid_amount']:.0f} грн | 📅 {bid['bid_deadline']} дн | 🕐 {time_str}
🔗 <a href="{bid['url']}">Проект</a>
"""
    
    await update.message.reply_text(
        message, 
        parse_mode=ParseMode.HTML, 
        disable_web_page_preview=True,
        reply_markup=get_main_keyboard()
    )


async def toggle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /toggle command."""
    if not check_user_access(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    current_status = db.get_enabled()
    new_status = not current_status
    db.set_enabled(new_status)
    
    status_text = "🟢 Включен" if new_status else "🔴 Выключен"
    action_text = "включен" if new_status else "выключен"
    
    message = f"✅ Автоотклик {action_text}.\n\n📊 Статус: {status_text}"
    await update.message.reply_text(
        message, 
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command."""
    if not check_user_access(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    categories = db.get_categories()
    categories_count = len(categories) if categories else 0
    
    message = f"""
⚙️ <b>Настройки</b>

📁 <b>Категории:</b> {categories_count} категорий разработки

Бот отслеживает проекты по следующим категориям:
• Веб-разработка (Frontend, Backend, Full Stack)
• Мобильная разработка (iOS, Android, React Native, Flutter)
• Языки программирования (Python, JavaScript, PHP, Java, C#, C++, Go, Kotlin, Swift и др.)
• Фреймворки (React, Vue, Angular, Laravel, Django, ASP.NET и др.)
• Базы данных (MySQL, PostgreSQL, MongoDB, Redis)
• CMS (WordPress, OpenCart, Drupal, Joomla, 1C-Битрикс)
• E-commerce (Magento, PrestaShop, Shopify)
• DevOps и облачные технологии

Для изменения категорий используйте кнопки ниже.
"""
    keyboard = [
        [InlineKeyboardButton("📁 Показать все категории", callback_data="show_categories")],
        [InlineKeyboardButton("✅ Использовать категории разработки", callback_data="set_dev_categories")],
        [InlineKeyboardButton("🗑 Очистить категории", callback_data="clear_categories")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")],
    ]
    await update.message.reply_text(
        message, 
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def check_projects_callback(context: ContextTypes.DEFAULT_TYPE):
    """Background job to check for new projects and submit bids."""
    if not db.get_enabled():
        logger.info("Auto-bidding is disabled, skipping check")
        return
    
    logger.info("Starting project check...")
    db.set_last_check_time()
    
    try:
        global scraper, browser
        
        # Initialize browser if needed (reuse same instance to maintain session)
        if browser is None:
            browser = BrowserAutomation(db)
            logger.info("Initializing browser for first time...")
        
        # Initialize driver if not already done (reuse to maintain session and cookies)
        if browser.driver is None:
            logger.info("Initializing browser driver...")
            browser.driver = browser.init_driver()
            # Load cookies once on first initialization
            if browser.load_cookies():
                logger.info("✅ Cookies loaded successfully on browser initialization")
            else:
                logger.warning("⚠️ Failed to load cookies on browser initialization")
        
        # Initialize scraper with browser
        if scraper is None:
            scraper = FreelancehuntScraper(db, browser=browser)
        else:
            # Update browser reference in case it was recreated
            scraper.browser = browser
        
        categories = db.get_categories()
        
        # Get new projects
        new_projects = scraper.get_new_projects(categories if categories else None)
        
        logger.info(f"Found {len(new_projects)} new projects")
        
        # Get new other projects (outside categories) - just save them, no notifications
        new_other_projects = db.get_new_other_projects()
        if new_other_projects:
            logger.info(f"Found {len(new_other_projects)} new projects outside categories (saved, no notifications)")
            # Mark as notified immediately so they don't trigger notifications
            for other_project in new_other_projects:
                db.mark_other_project_notified(other_project['id'])
        
        if not new_projects:
            return
        
        # Initialize browser if needed
        if browser is None:
            browser = BrowserAutomation(db)
            browser.driver = browser.init_driver()
            if not browser.load_cookies():
                error_msg = "⚠️ Не удалось загрузить cookies. Запустите save_cookies.py для сохранения cookies."
                logger.error(error_msg)
                try:
                    await context.bot.send_message(
                        chat_id=context.job.chat_id,
                        text=error_msg
                    )
                except:
                    pass
                return
        
        # Send notifications about found projects BEFORE submitting bids
        for project in new_projects:
            try:
                category_text = f"📁 {project.get('category', 'Неизвестная категория')}" if project.get('category') else ""
                budget_text = f"💰 {project['budget']:.0f} грн" if project.get('budget') else "💰 Бюджет не указан"
                title = project['title'][:60] + "..." if len(project['title']) > 60 else project['title']
                
                notification = f"""
🔔 <b>Найден новый проект!</b>

📝 <b>{title}</b>
{category_text}
{budget_text}
🔗 <a href="{project['url']}">Проект</a>

⏳ <i>Подготавливаю отклик...</i>
"""
                await context.bot.send_message(
                    chat_id=context.job.chat_id,
                    text=notification,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                await asyncio.sleep(0.5)  # Small delay between notifications
            except Exception as e:
                logger.error(f"Error sending project notification: {e}")
        
        # Process each new project and submit bids
        for project in new_projects:
            try:
                project_data = db.get_project(project['id'])
                if not project_data:
                    continue
                
                logger.info(f"Processing project: {project['title']}")
                
                # Submit bid
                success, message, bid_amount, bid_deadline = browser.submit_bid(
                    project['url'],
                    project.get('budget'),
                    project.get('deadline')
                )
                
                # Save bid to database
                bid_id = db.add_bid(
                    project['id'],
                    bid_amount,
                    bid_deadline,
                    'sent' if success else 'failed'
                )
                
                # Update bid status
                if bid_id:
                    db.update_bid_status(bid_id, 'sent' if success else 'failed')
                
                # Send notification about bid result
                status_emoji = "✅" if success else "❌"
                status_text = "Отклик успешно отправлен!" if success else "Ошибка при отправке отклика"
                
                notification = f"""
{status_emoji} <b>{status_text}</b>

📝 <b>{project['title'][:50]}</b>
💰 {bid_amount:.0f} грн
📅 {bid_deadline} дней
📁 {project.get('category', 'Неизвестная категория')}
🔗 <a href="{project['url']}">Проект</a>

{message}
"""
                try:
                    await context.bot.send_message(
                        chat_id=context.job.chat_id,
                        text=notification,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.error(f"Error sending notification: {e}")
                
                # Small delay between projects
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing project {project.get('id', 'unknown')}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error in check_projects_callback: {e}")
        try:
            await context.bot.send_message(
                chat_id=context.job.chat_id,
                text=f"❌ Ошибка при проверке проектов: {str(e)}"
            )
        except:
            pass


# Store active chat IDs for background jobs
active_chats = set()

def start_background_job(job_queue: JobQueue, chat_id: int):
    """Start background job for specific chat."""
    if job_queue is None:
        logger.warning("JobQueue is not available. Install python-telegram-bot[job-queue]")
        return
    
    job_name = f"check_projects_{chat_id}"
    
    # Remove existing job if any
    try:
        current_jobs = job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()
    except:
        pass
    
    # Start new job
    job_queue.run_repeating(
        check_projects_callback,
        interval=config.CHECK_INTERVAL,
        first=10,
        chat_id=chat_id,
        name=job_name
    )
    active_chats.add(chat_id)
    logger.info(f"Started background job for chat {chat_id}")

async def start_with_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with background job initialization."""
    await start_command(update, context)
    chat_id = update.effective_chat.id
    
    # Start background job if not already running
    if chat_id not in active_chats and context.application.job_queue:
        start_background_job(context.application.job_queue, chat_id)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if not check_user_access(update):
        try:
            await query.edit_message_text("❌ У вас нет доступа к этому боту.")
        except Exception:
            pass
        return
    
    data = query.data
    
    if data == "main_menu":
        try:
            await query.edit_message_text(
                "🔙 <b>Главное меню</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_keyboard()
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Error editing message: {e}")
    
    elif data == "status":
        enabled = db.get_enabled()
        status_text = "🟢 Включен" if enabled else "🔴 Выключен"
        last_check = db.get_last_check_time()
        if last_check:
            now = datetime.now()
            diff = now - last_check
            if diff.days == 0:
                last_check_text = f"сегодня {last_check.strftime('%H:%M')}"
            elif diff.days == 1:
                last_check_text = f"вчера {last_check.strftime('%H:%M')}"
            else:
                last_check_text = last_check.strftime("%d.%m %H:%M")
        else:
            last_check_text = "Никогда"
        categories = db.get_categories()
        categories_count = len(categories) if categories else 0
        last_bids = db.get_last_bids(5)
        total_bids = len(db.get_last_bids(1000))
        pending_bids = len(db.get_pending_bids())
        other_projects_count = len(db.get_all_other_projects(1000))
        
        message = f"""
📊 <b>Статус бота</b>

🔄 <b>Автоотклик:</b> {status_text}
🕐 <b>Последняя проверка:</b> {last_check_text}
📁 <b>Категории:</b> {categories_count} категорий

📈 <b>Статистика:</b>
• Всего откликов: {total_bids}
• В ожидании: {pending_bids}
• Других проектов: {other_projects_count}
"""
        try:
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_keyboard()
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Error editing message: {e}")
    
    elif data == "last_bids":
        bids = db.get_last_bids(10)
        if not bids:
            try:
                await query.edit_message_text(
                    "📭 Пока нет откликов.",
                    reply_markup=get_main_keyboard()
                )
            except Exception as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Error editing message: {e}")
            return
        
        message = "📋 <b>Последние отклики:</b>\n\n"
        for i, bid in enumerate(bids, 1):
            status_emoji = {'pending': '⏳', 'sent': '✅', 'failed': '❌'}.get(bid['status'], '❓')
            created_at = datetime.fromisoformat(bid['created_at']) if bid['created_at'] else None
            time_str = created_at.strftime("%d.%m %H:%M") if created_at else "?"
            title = bid['title'][:40] + "..." if len(bid['title']) > 40 else bid['title']
            message += f"{status_emoji} <b>{i}.</b> {title}\n💰 {bid['bid_amount']:.0f} грн | 📅 {bid['bid_deadline']} дн | 🕐 {time_str}\n🔗 <a href=\"{bid['url']}\">Проект</a>\n\n"
        
        try:
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=get_main_keyboard()
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Error editing message: {e}")
    
    elif data == "toggle":
        current_status = db.get_enabled()
        new_status = not current_status
        db.set_enabled(new_status)
        status_text = "🟢 Включен" if new_status else "🔴 Выключен"
        action_text = "включен" if new_status else "выключен"
        
        # Start/stop background job
        chat_id = query.message.chat.id
        if new_status and chat_id not in active_chats and context.application.job_queue:
            start_background_job(context.application.job_queue, chat_id)
        
        message = f"✅ Автоотклик {action_text}.\n\n📊 Статус: {status_text}"
        try:
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_keyboard()
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Error editing message: {e}")
    
    elif data == "settings":
        categories = db.get_categories()
        categories_count = len(categories) if categories else 0
        message = f"""
⚙️ <b>Настройки</b>

📁 <b>Категории:</b> {categories_count} категорий разработки

Бот отслеживает проекты по следующим категориям:
• Веб-разработка (Frontend, Backend, Full Stack)
• Мобильная разработка (iOS, Android, React Native, Flutter)
• Языки программирования (Python, JavaScript, PHP, Java, C#, C++, Go, Kotlin, Swift и др.)
• Фреймворки (React, Vue, Angular, Laravel, Django, ASP.NET и др.)
• Базы данных (MySQL, PostgreSQL, MongoDB, Redis)
• CMS (WordPress, OpenCart, Drupal, Joomla, 1C-Битрикс)
• E-commerce (Magento, PrestaShop, Shopify)
• DevOps и облачные технологии
"""
        keyboard = [
            [InlineKeyboardButton("📁 Показать все категории", callback_data="show_categories")],
            [InlineKeyboardButton("✅ Использовать категории разработки", callback_data="set_dev_categories")],
            [InlineKeyboardButton("🗑 Очистить категории", callback_data="clear_categories")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")],
        ]
        try:
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Error editing message: {e}")
    
    elif data == "categories":
        categories = db.get_categories()
        categories_count = len(categories) if categories else 0
        keyboard = [
            [InlineKeyboardButton("✅ Использовать категории разработки", callback_data="set_dev_categories")],
            [InlineKeyboardButton("🗑 Очистить категории", callback_data="clear_categories")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")],
        ]
        message = f"📁 <b>Категории</b>\n\nТекущее количество: {categories_count} категорий"
        try:
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Error editing message: {e}")
    
    elif data == "show_categories":
        categories = db.get_categories()
        if not categories:
            try:
                await query.edit_message_text(
                    "📁 Категории не установлены.",
                    reply_markup=get_main_keyboard()
                )
            except Exception as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Error editing message: {e}")
            return
        
        message = f"📁 <b>Все категории ({len(categories)}):</b>\n\n"
        # Show first 50 categories
        for i, cat in enumerate(categories[:50], 1):
            message += f"{i}. {cat}\n"
        if len(categories) > 50:
            message += f"\n... и еще {len(categories) - 50} категорий"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Настройки", callback_data="settings")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
        ]
        try:
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Error editing message: {e}")
    
    elif data == "set_dev_categories":
        db.set_categories(DEV_CATEGORIES)
        try:
            await query.edit_message_text(
                f"✅ Установлено {len(DEV_CATEGORIES)} категорий разработки!",
                reply_markup=get_main_keyboard()
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Error editing message: {e}")
    
    elif data == "clear_categories":
        db.set_categories([])
        try:
            await query.edit_message_text(
                "🗑 Категории очищены. Бот будет отслеживать все категории.",
                reply_markup=get_main_keyboard()
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Error editing message: {e}")
    
    elif data == "other_projects":
        other_projects = db.get_new_other_projects()
        all_other = db.get_all_other_projects(20)
        
        if not all_other:
            try:
                await query.edit_message_text(
                    "🔍 <b>Другие проекты</b>\n\n📭 Пока нет проектов вне категорий.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_main_keyboard()
                )
            except Exception as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Error editing message: {e}")
            return
        
        message = f"🔍 <b>Проекты вне категорий</b>\n\nНайдено: {len(all_other)} проектов\n\n"
        
        for i, project in enumerate(all_other[:10], 1):
            created_at = datetime.fromisoformat(project['first_seen_at']) if project.get('first_seen_at') else None
            if created_at:
                now = datetime.now()
                diff = now - created_at
                if diff.days == 0:
                    time_str = f"сегодня {created_at.strftime('%H:%M')}"
                elif diff.days == 1:
                    time_str = f"вчера {created_at.strftime('%H:%M')}"
                else:
                    time_str = created_at.strftime("%d.%m %H:%M")
            else:
                time_str = "?"
            
            title = project['title'][:45] + "..." if len(project['title']) > 45 else project['title']
            budget_text = f"💰 {project['budget']:.0f} грн | " if project.get('budget') else ""
            category_text = f"📁 {project['category']}\n" if project.get('category') else ""
            
            message += f"{i}. <b>{title}</b>\n{category_text}{budget_text}🕐 {time_str}\n🔗 <a href=\"{project['url']}\">Проект</a>\n\n"
        
        if len(all_other) > 10:
            message += f"\n... и еще {len(all_other) - 10} проектов"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="other_projects")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")],
        ]
        try:
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Error editing message: {e}")

def main():
    """Main function to start the bot."""
    global bot_application
    
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    # Initialize default categories if not set
    categories = db.get_categories()
    if not categories:
        db.set_categories(DEV_CATEGORIES)
        logger.info(f"Initialized {len(DEV_CATEGORIES)} development categories")
    
    # Auto-start background job if enabled - will be called after initialization
    async def post_init(app: Application) -> None:
        """Called after application is initialized but before polling starts."""
        if app.job_queue and db.get_enabled():
            # Get first allowed user ID or use default
            allowed_users = config.ALLOWED_USER_IDS
            if allowed_users:
                # Use first allowed user
                chat_id = allowed_users[0]
                logger.info(f"Auto-starting background job for chat {chat_id} (status is enabled)")
                start_background_job(app.job_queue, chat_id)
            else:
                logger.warning("No allowed user IDs configured, auto-start skipped. Please use /start command to begin.")
    
    # Create application with post_init callback
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    bot_application = application
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_with_job))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("last_bids", last_bids_command))
    application.add_handler(CommandHandler("toggle", toggle_command))
    application.add_handler(CommandHandler("settings", settings_command))
    
    # Register callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add error handler for Conflict errors
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the telegram-python-bot library."""
        logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
        
        # Handle Conflict error (multiple bot instances)
        if isinstance(context.error, Conflict):
            logger.error("=" * 60)
            logger.error("CONFLICT ERROR: Multiple bot instances detected!")
            logger.error("The bot is already running somewhere else.")
            logger.error("Please stop the other instance before starting this one.")
            logger.error("=" * 60)
            # Wait a bit and try to continue (in case other instance stops)
            await asyncio.sleep(5)
            return
        
        # Handle network errors
        if isinstance(context.error, NetworkError):
            logger.warning(f"Network error: {context.error}. Will retry...")
            await asyncio.sleep(5)
            return
        
        # Handle rate limiting
        if isinstance(context.error, RetryAfter):
            logger.warning(f"Rate limited. Waiting {context.error.retry_after} seconds...")
            await asyncio.sleep(context.error.retry_after)
            return
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Auto-start background job if enabled
    async def post_init(application: Application) -> None:
        """Called after application is initialized."""
        if application.job_queue and db.get_enabled():
            # Get first allowed user ID or use default
            allowed_users = config.ALLOWED_USER_IDS
            if allowed_users:
                # Use first allowed user
                chat_id = allowed_users[0]
                logger.info(f"Auto-starting background job for chat {chat_id} (status is enabled)")
                start_background_job(application.job_queue, chat_id)
            else:
                logger.warning("No allowed user IDs configured, auto-start skipped")
    
    # Register post_init handler
    application.post_init = post_init
    
    logger.info("Bot starting...")
    
    # Run with retry logic for Conflict errors
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                stop_signals=None,  # Don't stop on SIGTERM (for Docker)
                drop_pending_updates=True  # Drop pending updates on start
            )
            break  # Success, exit loop
        except Conflict as e:
            retry_count += 1
            logger.error(f"Conflict error (attempt {retry_count}/{max_retries}): {e}")
            if retry_count >= max_retries:
                logger.error("Maximum retries reached. Another bot instance is running.")
                logger.error("Please stop the other bot instance and try again.")
                sys.exit(1)
            logger.info(f"Waiting 10 seconds before retry {retry_count + 1}...")
            import time
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            if retry_count >= max_retries:
                sys.exit(1)
            retry_count += 1
            import time
            time.sleep(10)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        if browser:
            browser.close()
        db.close()

