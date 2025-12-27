import os
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class WeatherAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            logger.warning("OPENWEATHER_API_KEY не найден.")
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_current_weather(self, city: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            logger.error("API ключ не настроен")
            return None

        try:
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
                "lang": "ru"
            }

            response = requests.get(
                f"{self.base_url}/weather",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            return self._format_current_weather(data)

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к OpenWeatherMap: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Ошибка обработки данных: {e}")
            return None

    def get_forecast(self, city: str, days: int = 5) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            logger.error("API ключ не настроен")
            return None

        try:
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
                "lang": "ru",
                "cnt": days * 8
            }

            response = requests.get(
                f"{self.base_url}/forecast",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            return self._format_forecast(data)

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса прогноза: {e}")
            return None

    def _format_current_weather(self, data: Dict) -> Dict[str, Any]:
        return {
            "city": data.get("name", "Неизвестно"),
            "country": data.get("sys", {}).get("country", "N/A"),
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "weather": data["weather"][0]["description"].capitalize(),
            "weather_icon": data["weather"][0]["icon"],
            "wind_speed": data["wind"]["speed"],
            "wind_direction": self._get_wind_direction(data["wind"].get("deg", 0)),
            "clouds": data.get("clouds", {}).get("all", 0),
            "visibility": data.get("visibility", 0),
            "sunrise": data.get("sys", {}).get("sunrise"),
            "sunset": data.get("sys", {}).get("sunset"),
            "timestamp": data.get("dt")
        }

    def _format_forecast(self, data: Dict) -> Dict[str, Any]:
        forecast_by_day = {}

        for item in data.get("list", []):
            date_str = item["dt_txt"].split()[0]
            date = datetime.strptime(date_str, "%Y-%m-%d")

            if date_str not in forecast_by_day:
                forecast_by_day[date_str] = {
                    "date": date_str,
                    "day_name": self._get_day_name(date),
                    "temp_min": item["main"]["temp_min"],
                    "temp_max": item["main"]["temp_max"],
                    "weather": item["weather"][0]["description"],
                    "icon": item["weather"][0]["icon"],
                    "humidity": item["main"]["humidity"],
                    "wind_speed": item["wind"]["speed"]
                }
            else:
                day_data = forecast_by_day[date_str]
                day_data["temp_min"] = min(day_data["temp_min"], item["main"]["temp_min"])
                day_data["temp_max"] = max(day_data["temp_max"], item["main"]["temp_max"])

        return {
            "city": data["city"]["name"],
            "country": data["city"]["country"],
            "forecast": list(forecast_by_day.values())[:5]  # первые 5 дней
        }

    @staticmethod
    def _get_wind_direction(degrees: float) -> str:
        directions = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]
        index = round(degrees / 45) % 8
        return directions[index]

    @staticmethod
    def _get_day_name(date: datetime) -> str:
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        return days[date.weekday()]