#!/usr/bin/env python3
"""
Миграция для добавления таблицы deployments
"""

import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./windexai.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_deployments_table():
    """Создает таблицу deployments если она не существует"""
    conn = engine.connect()
    inspector = inspect(engine)

    if "deployments" not in inspector.get_table_names():
        print("🔄 Создаем таблицу deployments...")

        with conn.begin():
            conn.execute(
                text(
                    """
                CREATE TABLE deployments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    user_id INTEGER,
                    deployment_url VARCHAR NOT NULL,
                    deployment_platform VARCHAR DEFAULT 'vercel',
                    deployment_status VARCHAR DEFAULT 'active',
                    site_title VARCHAR,
                    site_description TEXT,
                    total_visits INTEGER DEFAULT 0,
                    unique_visitors INTEGER DEFAULT 0,
                    page_views INTEGER DEFAULT 0,
                    bounce_rate FLOAT DEFAULT 0.0,
                    avg_session_duration FLOAT DEFAULT 0.0,
                    load_time FLOAT DEFAULT 0.0,
                    performance_score FLOAT DEFAULT 0.0,
                    seo_score FLOAT DEFAULT 0.0,
                    accessibility_score FLOAT DEFAULT 0.0,
                    metadata JSON,
                    last_analytics_update DATETIME DEFAULT CURRENT_TIMESTAMP,
                    deployed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """
                )
            )

        print("✅ Таблица deployments создана успешно!")
    else:
        print("✅ Таблица deployments уже существует.")


def add_sample_data():
    """Добавляет примеры данных для тестирования"""
    conn = engine.connect()

    # Проверяем, есть ли уже данные
    result = conn.execute(text("SELECT COUNT(*) FROM deployments")).fetchone()
    if result[0] > 0:
        print("✅ Данные уже существуют.")
        return

    print("🔄 Добавляем примеры данных...")

    with conn.begin():
        # Добавляем примеры деплоев
        conn.execute(
            text(
                """
            INSERT INTO deployments (
                conversation_id, user_id, deployment_url, deployment_platform,
                site_title, site_description, total_visits, unique_visitors,
                page_views, bounce_rate, avg_session_duration, load_time,
                performance_score, seo_score, accessibility_score
            ) VALUES
            (1, 1, 'https://my-awesome-site.vercel.app', 'vercel',
             'Мой крутой сайт', 'Современный сайт на Next.js',
             1250, 890, 2100, 35.5, 180.2, 1.2, 95.0, 88.0, 92.0),
            (2, 1, 'https://business-landing.netlify.app', 'netlify',
             'Бизнес лендинг', 'Корпоративный сайт для бизнеса',
             890, 650, 1450, 42.1, 165.8, 1.5, 89.0, 85.0, 87.0)
        """
            )
        )

    print("✅ Примеры данных добавлены!")


if __name__ == "__main__":
    print("🚀 Запуск миграции для таблицы deployments...")
    create_deployments_table()
    add_sample_data()
    print("✅ Миграция завершена успешно!")
