#!/usr/bin/env python3
"""
Простой тест для проверки работы ngrok с WindexAI
"""

import subprocess
import time
import requests
import json
import os

def test_ngrok_connection():
    """Тестирование подключения к ngrok"""
    try:
        print("🔍 Проверка ngrok API...")
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            if tunnels:
                for tunnel in tunnels:
                    if tunnel.get('proto') == 'https':
                        public_url = tunnel.get('public_url')
                        print(f"✅ Найден туннель: {public_url}")
                        return public_url
            else:
                print("⚠️  Туннели не найдены")
                return None
        else:
            print(f"❌ Ошибка API ngrok: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Ошибка подключения к ngrok: {e}")
        return None

def test_app_endpoint(public_url):
    """Тестирование доступности приложения"""
    try:
        print(f"🌐 Тестирование {public_url}...")
        response = requests.get(public_url, timeout=10)
        if response.status_code == 200:
            print("✅ Приложение доступно!")
            return True
        else:
            print(f"⚠️  Приложение отвечает с кодом: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к приложению: {e}")
        return False

def main():
    print("🧪 Тестирование ngrok интеграции...")
    
    # Проверяем, запущен ли ngrok
    public_url = test_ngrok_connection()
    
    if not public_url:
        print("❌ ngrok не запущен или не настроен")
        print("💡 Запустите: python3 start_with_ngrok.py")
        return
    
    # Тестируем приложение
    if test_app_endpoint(public_url):
        print(f"🎉 Все работает! Ваше приложение доступно по адресу: {public_url}")
        print(f"📝 Для деплоев используйте: {public_url}/deploy/")
    else:
        print("❌ Приложение недоступно")

if __name__ == "__main__":
    main()

