import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = (
        f"Привет, {user.first_name}!\n\n"
        f"Я бот погоды. Я могу:\n"
        f"• Показать текущую погоду в любом городе\n"
        f"• Отправлять уведомления об изменениях погоды\n\n"
        f"Просто напиши мне название города или используй /weather"
    )
    await update.message.reply_text(welcome_text)
    logger.info(f"Пользователь {user.id} начал работу с ботом")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "*Помощь по боту погоды*\n\n"
        "*Доступные команды:*\n"
        "• /start - Начать работу\n"
        "• /help - Справка\n"
        "• /weather <город> - Погода в городе\n"
        "• /subscribe - Подписаться на уведомления\n\n"
        "*Как использовать:*\n"
        "1. Напишите название города (например, 'Москва')\n"
        "2. Или используйте команду /weather Москва\n"
        "3. Получите информацию о погоде\n\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /weather"""
    if not context.args:
        await update.message.reply_text(
            "Укажите город после команды:\n"
            "Пример: /weather Москва\n"
            "Или просто отправьте название города"
        )
        return

    city = " ".join(context.args)

    await update.message.reply_chat_action(action="typing")

    # Заглушка
    weather_response = (
        f"*Погода в {city}*\n\n"
        f"Температура: +15°C\n"
        f"Ощущается как: +14°C\n"
        f"Состояние: Облачно\n"
        f"Влажность: 65%\n"
        f"Ветер: 3 м/с\n\n"
    )

    await update.message.reply_text(weather_response, parse_mode='Markdown')
    logger.info(f"Запрос погоды для города: {city}")


async def handle_city_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений (названия городов)"""
    city = update.message.text.strip()

    if len(city) < 2:
        await update.message.reply_text("Пожалуйста, укажите название города")
        return

    # Используем ту же логику, что и для /weather
    context.args = [city]
    await weather_command(update, context)


def main():
    """Запуск бота"""
    print("=" * 50)
    print("ЗАПУСК БОТА ПОГОДЫ")
    print("=" * 50)

    if not TOKEN:
        print("Ошибка: TELEGRAM_BOT_TOKEN не найден в .env файле")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city_message))

    print("Бот запущен и готов к работе")
    print("Команды: /start, /help, /weather <город>")
    print("Для остановки: Ctrl+C")
    print("=" * 50)

    app.run_polling()


if __name__ == "__main__":
    main()