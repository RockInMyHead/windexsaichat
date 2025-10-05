#!/usr/bin/env python3
"""
Миграция базы данных для добавления поля conversation_type
"""

import os
import sqlite3
from datetime import datetime


def migrate_database():
    """Добавляет поле conversation_type в таблицу conversations"""

    db_path = "windexai.db"

    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return False

    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем, существует ли уже поле conversation_type
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [column[1] for column in cursor.fetchall()]

        if "conversation_type" in columns:
            print("✅ Поле conversation_type уже существует")
            conn.close()
            return True

        # Добавляем поле conversation_type
        print("🔄 Добавляем поле conversation_type...")
        cursor.execute(
            "ALTER TABLE conversations ADD COLUMN conversation_type TEXT DEFAULT 'chat'"
        )

        # Обновляем существующие записи
        cursor.execute(
            "UPDATE conversations SET conversation_type = 'chat' WHERE conversation_type IS NULL"
        )

        # Сохраняем изменения
        conn.commit()
        conn.close()

        print("✅ Миграция успешно завершена!")
        return True

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Запуск миграции базы данных...")
    success = migrate_database()

    if success:
        print("✅ Миграция завершена успешно!")
    else:
        print("❌ Миграция не удалась!")
# flake8: noqa
