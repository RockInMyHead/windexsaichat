#!/usr/bin/env python3
"""
Скрипт для миграции базы данных WindexAI
Добавляет новые колонки для поддержки голосовых сообщений и документов
"""

import os
import sqlite3
from datetime import datetime


def migrate_database():
    """Миграция базы данных"""
    db_path = "windexai.db"

    if not os.path.exists(db_path):
        print("База данных не найдена. Создаем новую...")
        from database import create_tables

        create_tables()
        print("✅ Новая база данных создана")
        return

    print("🔄 Начинаем миграцию базы данных...")

    # Создаем резервную копию
    backup_path = f"windexai_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.rename(db_path, backup_path)
    print(f"📦 Создана резервная копия: {backup_path}")

    # Подключаемся к резервной копии для чтения данных
    old_conn = sqlite3.connect(backup_path)
    old_cursor = old_conn.cursor()

    # Создаем новую базу данных с обновленной схемой
    new_conn = sqlite3.connect(db_path)
    new_cursor = new_conn.cursor()

    try:
        # Создаем новые таблицы
        from database import create_tables

        create_tables()

        # Мигрируем данные пользователей
        print("👥 Мигрируем пользователей...")
        old_cursor.execute(
            "SELECT id, username, email, hashed_password, created_at FROM users"
        )
        users = old_cursor.fetchall()

        for user in users:
            new_cursor.execute(
                """
                INSERT INTO users (id, username, email, hashed_password, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                user,
            )

        # Мигрируем данные разговоров
        print("💬 Мигрируем разговоры...")
        old_cursor.execute(
            "SELECT id, title, created_at, updated_at, user_id FROM conversations"
        )
        conversations = old_cursor.fetchall()

        for conv in conversations:
            new_cursor.execute(
                """
                INSERT INTO conversations (id, title, created_at, updated_at, user_id)
                VALUES (?, ?, ?, ?, ?)
            """,
                conv,
            )

        # Мигрируем данные сообщений
        print("📝 Мигрируем сообщения...")
        old_cursor.execute(
            "SELECT id, role, content, timestamp, conversation_id FROM messages"
        )
        messages = old_cursor.fetchall()

        for msg in messages:
            new_cursor.execute(
                """
                INSERT INTO messages (id, role, content, message_type, audio_url, document_id, timestamp, conversation_id)
                VALUES (?, ?, ?, 'text', NULL, NULL, ?, ?)
            """,
                (msg[0], msg[1], msg[2], msg[3], msg[4]),
            )

        # Мигрируем данные деплоев
        print("🚀 Мигрируем деплои...")
        old_cursor.execute(
            "SELECT id, title, description, deploy_url, html_content, css_content, js_content, is_active, created_at, updated_at, user_id FROM deployments"
        )
        deployments = old_cursor.fetchall()

        for dep in deployments:
            new_cursor.execute(
                """
                INSERT INTO deployments (id, title, description, deploy_url, html_content, css_content, js_content, is_active, created_at, updated_at, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                dep,
            )

        # Сохраняем изменения
        new_conn.commit()
        print("✅ Миграция завершена успешно!")

    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        # Восстанавливаем резервную копию
        new_conn.close()
        os.remove(db_path)
        os.rename(backup_path, db_path)
        print("🔄 Восстановлена резервная копия")
        raise

    finally:
        old_conn.close()
        new_conn.close()


if __name__ == "__main__":
    migrate_database()
