import os
import psycopg2
import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "weather_bot"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres")
        )
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return None


def init_database():
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(100),
                first_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                city VARCHAR(100) NOT NULL,
                notification_time VARCHAR(5) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cur.close()
        conn.close()

        logger.info("База данных инициализирована")
        return True

    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        return False


def add_user(telegram_id: int, username: str = None, first_name: str = None) -> bool:
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (telegram_id, username, first_name) 
            VALUES (%s, %s, %s)
            ON CONFLICT (telegram_id) 
            DO UPDATE SET 
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name
        """, (telegram_id, username, first_name))

        conn.commit()
        cur.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Ошибка добавления пользователя: {e}")
        return False


def add_subscription(telegram_id: int, city: str, notification_time: str) -> Optional[int]:
    conn = get_db_connection()
    if not conn:
        return None

    try:
        add_user(telegram_id)

        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
        user_result = cur.fetchone()

        if not user_result:
            return None

        user_id = user_result[0]

        cur.execute("""
            INSERT INTO subscriptions (user_id, city, notification_time)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (user_id, city, notification_time))

        subscription_id = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        return subscription_id

    except Exception as e:
        logger.error(f"Ошибка добавления подписки: {e}")
        return None


def get_user_subscriptions(telegram_id: int) -> List[Tuple]:
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.id, s.city, s.notification_time
            FROM subscriptions s
            JOIN users u ON s.user_id = u.id
            WHERE u.telegram_id = %s
            ORDER BY s.created_at
        """, (telegram_id,))

        subscriptions = cur.fetchall()
        cur.close()
        conn.close()

        return subscriptions

    except Exception as e:
        logger.error(f"Ошибка получения подписок: {e}")
        return []


def delete_subscription(subscription_id: int) -> bool:
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM subscriptions WHERE id = %s", (subscription_id,))

        conn.commit()
        cur.close()
        conn.close()

        return cur.rowcount > 0

    except Exception as e:
        logger.error(f"Ошибка удаления подписки: {e}")
        return False