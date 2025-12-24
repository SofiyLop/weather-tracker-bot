import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.api.weather import get_current_weather

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"Привет, {user.first_name}!\n\n"
        f"Я бот погоды. Напиши название города или используй /weather"
    )
    await update.message.reply_text(welcome_text)
    logger.info(f"Пользователь {user.id} начал работу с ботом")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать работу\n"
        "/help - Справка\n"
        "/weather <город> - Погода в городе\n\n"
        "Напишите название города, например: Москва"
    )
    await update.message.reply_text(help_text)


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Укажите город после команды:\n"
            "Пример: /weather Москва"
        )
        return

    city = " ".join(context.args)
    await update.message.reply_chat_action(action="typing")

    weather_data = get_current_weather(city)

    if weather_data:
        weather_response = (
            f"Погода в {weather_data['city']}:\n\n"
            f"Температура: {weather_data['temperature']:.1f}°C\n"
            f"Ощущается как: {weather_data['feels_like']:.1f}°C\n"
            f"Состояние: {weather_data['weather']}\n"
            f"Влажность: {weather_data['humidity']}%\n"
            f"Давление: {weather_data['pressure']} гПа\n"
            f"Ветер: {weather_data['wind_speed']} м/с"
        )
    else:
        weather_response = f"Не удалось получить погоду для города '{city}'"

    await update.message.reply_text(weather_response)
    logger.info(f"Запрос погоды для города: {city}")


async def handle_city_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()

    if len(city) < 2:
        await update.message.reply_text("Пожалуйста, укажите название города")
        return

    context.args = [city]
    await weather_command(update, context)


def main():
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