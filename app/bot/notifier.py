import threading
import time
import schedule
import logging
from datetime import datetime
import os
import sys
import asyncio
from threading import Thread

logger = logging.getLogger(__name__)


class WeatherNotifier:
    def __init__(self, application):
        self.application = application
        self.bot = application.bot
        self.is_running = False
        self.thread = None
        self.loop = None

        from app.api.weather import WeatherAPI
        from app.database.db import get_db_connection

        self.weather_api = WeatherAPI()
        self.get_db_connection = get_db_connection

        logger.info("Сервис уведомлений инициализирован")

    def send_notification(self, chat_id: int, city: str):
        try:
            weather_data = self.weather_api.get_current_weather(city)
            if not weather_data:
                logger.warning(f"Не удалось получить погоду для {city}")
                return False

            message = (
                f"⏰ *{weather_data['city']}, {weather_data.get('country', '')}*\n\n"
                f"🌡️ Температура: *{weather_data['temperature']:.1f}°C*\n"
                f"🤏 Ощущается как: *{weather_data['feels_like']:.1f}°C*\n"
                f"💧 Влажность: *{weather_data['humidity']}%*\n"
                f"💨 Ветер: *{weather_data['wind_speed']} м/с*\n"
                f"📝 *{weather_data['weather']}*\n\n"
                f"Хорошего дня! ☀"
            )

            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._async_send_message(chat_id, message),
                    self.loop
                )
            else:
                asyncio.run(self._async_send_message(chat_id, message))

            logger.info(f"Уведомление отправлено в {chat_id} для {city}")
            return True

        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
            return False

    async def _async_send_message(self, chat_id: int, message: str):
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка в _async_send_message: {e}")

    def check_and_send_notifications(self):
        try:
            current_time = datetime.now().strftime("%H:%M")
            logger.debug(f"Проверка уведомления для времени {current_time}")

            conn = self.get_db_connection()
            if not conn:
                return

            cur = conn.cursor()
            cur.execute("""
                SELECT u.telegram_id, s.city, s.notification_time
                FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                WHERE s.notification_time = %s
            """, (current_time,))

            subscriptions = cur.fetchall()
            cur.close()
            conn.close()

            if not subscriptions:
                logger.debug(f"Нет подписок на время {current_time}")
                return

            logger.info(f"Найдено {len(subscriptions)} подписок на {current_time}")

            for telegram_id, city, _ in subscriptions:
                self.send_notification(telegram_id, city)
                time.sleep(0.5)

        except Exception as e:
            logger.error(f"Ошибка проверки уведомлений: {e}")

    def run_scheduler(self):
        logger.info("Запуск планировщика уведомлений...")

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        schedule.every(1).minutes.do(self.check_and_send_notifications)

        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")
                time.sleep(60)

        if self.loop and self.loop.is_running():
            self.loop.close()

    def start(self):
        if self.is_running:
            logger.warning("Сервис уведомлений уже запущен")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()

        self.check_and_send_notifications()

        logger.info("Сервис уведомлений запущен")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Сервис уведомлений остановлен")


_notifier_instance = None


def get_notifier(application=None):
    global _notifier_instance

    if _notifier_instance is None and application:
        _notifier_instance = WeatherNotifier(application)

    return _notifier_instance


def start_notifier(application):
    notifier = get_notifier(application)
    if notifier:
        notifier.start()
        return True
    return False


def stop_notifier():
    global _notifier_instance
    if _notifier_instance:
        _notifier_instance.stop()
        _notifier_instance = None
        return True
    return False