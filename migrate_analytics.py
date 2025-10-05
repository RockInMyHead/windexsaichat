#!/usr/bin/env python3
"""
Миграция для добавления таблицы аналитики сайтов
"""

import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from database import Base, SiteAnalytics

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./windexai.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def migrate_analytics():
    """Добавляет таблицу site_analytics если её нет"""
    print("🚀 Запуск миграции аналитики...")

    # Проверяем существующие таблицы
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "site_analytics" not in existing_tables:
        print("📊 Создаем таблицу site_analytics...")
        SiteAnalytics.__table__.create(engine)
        print("✅ Таблица site_analytics создана успешно!")
    else:
        print("ℹ️ Таблица site_analytics уже существует")

    print("🎉 Миграция аналитики завершена!")


if __name__ == "__main__":
    migrate_analytics()
# flake8: noqa
