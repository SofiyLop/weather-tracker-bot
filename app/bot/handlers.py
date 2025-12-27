import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from app.api.weather import WeatherAPI
from app.database import db

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    db.add_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

    welcome_text = (
        f"Привет, {user.first_name}!\n\n"
        f"☀ *Я бот погоды.*\n\n"
        f"*Что я умею:*\n"
        f"• Показывать текущую погоду в любом городе\n"
        f"• Показывать прогноз на 5 дней\n"
        f"• Отправлять уведомления о погоде в любом городе\n\n"
        f"🌤 *Погода сейчас:*\n"
        f"• Напишите название города\n"
        f"• Или команду /weather Москва\n\n"
        f"📅 *Прогноз на 5 дней:*\n"
        f"• /forecast Москва\n\n"
        f"🔔 *Уведомления:*\n"
        f"• /subscribe Москва 08:30\n"
        f"• /mysubs - мои подписки\n"
        f"• /unsubscribe 1 - удалить подписку\n\n"
        f"📖 *Помощь:* /help"
    )

    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 *Справка по командам:*\n\n"

        "🌤️ *Погода сейчас:*\n"
        "• Просто напишите город\n"
        "• Или /weather <город>\n\n"

        "📅 *Прогноз на 5 дней:*\n"
        "• /forecast <город>\n\n"

        "🔔 *Подписки на уведомления:*\n"
        "• /subscribe <город> <время>\n"
        "• /mysubs - список подписок\n"
        "• /unsubscribe <номер> - удалить подписку\n\n"

        "📍 *Примеры:*\n"
        "• /weather Санкт-Петербург\n"
        "• /forecast Лондон\n"
        "• /subscribe Москва 08:30"
    )

    await update.message.reply_text(help_text, parse_mode='Markdown')


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "📍 *Укажите город после команды:*\n"
            "/weather <город>\n\n"
            "*Пример:*\n"
            "/weather Москва\n"
            "Или просто отправьте название города",
            parse_mode='Markdown'
        )
        return

    city = " ".join(context.args)
    await update.message.reply_chat_action(action="typing")

    weather_api = WeatherAPI()
    weather_data = weather_api.get_current_weather(city)

    if weather_data:
        message = (
            f"🌤️ *{weather_data['city']}, {weather_data.get('country', '')}*\n\n"
            f"🌡️ Температура: *{weather_data['temperature']:.1f}°C*\n"
            f"🤏 Ощущается как: *{weather_data['feels_like']:.1f}°C*\n"
            f"💧 Влажность: *{weather_data['humidity']}%*\n"
            f"💨 Ветер: *{weather_data['wind_speed']} м/с*\n"
            f"📝 *{weather_data['weather']}*"
        )
    else:
        message = (
            f"❌ Город *{city}* не найден.\n"
            f"Проверьте правильность написания.",
        )
    await update.message.reply_text(message, parse_mode='Markdown')


async def handle_city_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()
    await update.message.reply_chat_action(action="typing")

    weather_api = WeatherAPI()
    weather_data = weather_api.get_current_weather(city)

    if weather_data:
        message = (
            f"🌤️ *{weather_data['city']}, {weather_data.get('country', '')}*\n\n"
            f"🌡️ Температура: *{weather_data['temperature']:.1f}°C*\n"
            f"🤏 Ощущается как: *{weather_data['feels_like']:.1f}°C*\n"
            f"💧 Влажность: *{weather_data['humidity']}%*\n"
            f"💨 Ветер: *{weather_data['wind_speed']} м/с*\n"
            f"📝 *{weather_data['weather']}*"
        )
    else:
        message = (
            f"❌ Город *{city}* не найден.\n"
            f"Проверьте правильность написания.",
        )
    await update.message.reply_text(message, parse_mode='Markdown')


async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "📍 *Укажите город после команды:*\n"
            "/forecast <город>\n\n"
            "*Пример:*\n"
            "/forecast Москва",
            parse_mode='Markdown'
        )
        return

    city = " ".join(context.args)
    await update.message.reply_chat_action(action="typing")

    weather_api = WeatherAPI()
    forecast_data = weather_api.get_forecast(city, days=5)

    if forecast_data:
        message = f"📅 *Прогноз {forecast_data['city']}, {forecast_data.get('country', '')}:*\n\n"

        for day in forecast_data.get('forecast', [])[:5]:
            try:
                date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
                date_str = date_obj.strftime("%d.%m")
            except:
                date_str = day['date']

            message += (
                f"*{date_str}* ({day.get('day_name', '')})\n"
                f"🌡️ {day['temp_min']:.0f}°...{day['temp_max']:.0f}°C\n"
                f"📝 {day['weather'].capitalize()}\n\n"
            )
    else:
        message = f"❌ Не удалось получить прогноз для *{city}*"
    await update.message.reply_text(message, parse_mode='Markdown')


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📍 *Использование:*\n"
            "/subscribe <город> <время>\n\n"
            "*Пример:*\n"
            "/subscribe Москва 08:30\n"
            "/subscribe Санкт-Петербург 19:00",
            parse_mode='Markdown'
        )
        return

    city = context.args[0]
    time_str = context.args[1]

    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await update.message.reply_text(
            "❌ *Неверный формат времени!*\n"
            "Используйте: ЧЧ:ММ\n"
            "*Пример:* 08:30, 19:00",
            parse_mode='Markdown'
        )
        return

    weather_api = WeatherAPI()
    if not weather_api.get_current_weather(city):
        await update.message.reply_text(
            f"❌ Город *{city}* не найден.\n"
            f"Проверьте правильность написания.",
            parse_mode='Markdown'
        )
        return

    user = update.effective_user
    subscription_id = db.add_subscription(user.id, city, time_str)

    if subscription_id:
        await update.message.reply_text(
            f"✅ *Подписка создана!*\n\n"
            f"📍 Город: *{city}*\n"
            f"⏰ Время: *{time_str}*\n\n"
            f"ID подписки: `{subscription_id}`\n",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ *Ошибка создания подписки*",
            parse_mode='Markdown'
        )


async def mysubs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    subscriptions = db.get_user_subscriptions(user.id)

    if not subscriptions:
        await update.message.reply_text(
            "📭 *У вас нет подписок.*\n\n"
            "Чтобы создать подписку:\n"
            "/subscribe <город> <время>\n\n"
            "*Пример:*\n"
            "/subscribe Москва 08:30",
            parse_mode='Markdown'
        )
        return

    message = "📋 *Ваши подписки:*\n\n"

    for i, (sub_id, city, time_str) in enumerate(subscriptions, 1):
        message += f"{i}. *{city}* в {time_str}\n"
        message += f"   ID: `{sub_id}`\n\n"

    message += "🗑️ *Удалить:* /unsubscribe <ID>"

    await update.message.reply_text(message, parse_mode='Markdown')


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "📍 *Укажите ID подписки:*\n"
            "/unsubscribe <ID>\n\n"
            "ID можно узнать через /mysubs",
            parse_mode='Markdown'
        )
        return

    try:
        subscription_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ *ID должен быть числом*",
            parse_mode='Markdown'
        )
        return

    if db.delete_subscription(subscription_id):
        await update.message.reply_text(
            f"✅ Подписка *{subscription_id}* удалена",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Подписка *{subscription_id}* не найдена",
            parse_mode='Markdown'
        )