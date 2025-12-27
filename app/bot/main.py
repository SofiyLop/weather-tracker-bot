import os
import sys
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from app.bot.handlers import (
    start,
    help_command,
    weather_command,
    forecast_command,
    subscribe_command,
    mysubs_command,
    unsubscribe_command,
    handle_city_message
)

from app.database import db

from app.bot.notifier import start_notifier, stop_notifier


def check_environment():
    required_vars = ['TELEGRAM_BOT_TOKEN', 'OPENWEATHER_API_KEY']
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    if missing_vars:
        logger.error(f"Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        return False
    return True


def main():
    print("\n" + "=" * 50)
    print("ЗАПУСК ТЕЛЕГРАМ БОТА ПОГОДЫ")
    print("=" * 50)

    if not check_environment():
        sys.exit(1)

    if not db.init_database():
        logger.warning("Не удалось инициализировать БД")

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(CommandHandler("forecast", forecast_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("mysubs", mysubs_command))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city_message))

    logger.info("Запуск сервиса уведомлений...")
    if start_notifier(app):
        logger.info("Сервис уведомлений запущен")
    else:
        logger.warning("Не удалось запустить сервис уведомлений")

    logger.info("Бот запускается...")
    print("Бот запускается...")
    print("Для остановки нажмите Ctrl+C")
    print("=" * 50 + "\n")

    try:
        app.run_polling()
    except KeyboardInterrupt:
        stop_notifier()
        print("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        stop_notifier()
        sys.exit(1)


if __name__ == "__main__":
    main()