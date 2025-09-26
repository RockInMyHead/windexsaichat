#!/usr/bin/env python3
"""
Скрипт для запуска WindexAI с ngrok
Автоматически получает публичный URL и обновляет конфигурацию
"""

import subprocess
import time
import json
import requests
import os
import signal
import sys
from threading import Thread
import uvicorn

class NgrokManager:
    def __init__(self):
        self.ngrok_process = None
        self.public_url = None
        
    def start_ngrok(self):
        """Запуск ngrok туннеля"""
        try:
            print("🌐 Запуск ngrok туннеля...")
            self.ngrok_process = subprocess.Popen(
                ["ngrok", "start", "windexai", "--config=ngrok.yml"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Ждем запуска ngrok
            time.sleep(3)
            
            # Получаем публичный URL
            self.get_public_url()
            
            if self.public_url:
                print(f"✅ Ngrok запущен успешно!")
                print(f"🔗 Публичный URL: {self.public_url}")
                return True
            else:
                print("❌ Не удалось получить публичный URL")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запуска ngrok: {e}")
            return False
    
    def get_public_url(self):
        """Получение публичного URL из ngrok API"""
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            if response.status_code == 200:
                data = response.json()
                for tunnel in data.get('tunnels', []):
                    if tunnel.get('proto') == 'https':
                        self.public_url = tunnel.get('public_url')
                        break
        except Exception as e:
            print(f"⚠️  Не удалось получить URL из ngrok API: {e}")
    
    def stop_ngrok(self):
        """Остановка ngrok"""
        if self.ngrok_process:
            print("🛑 Остановка ngrok...")
            self.ngrok_process.terminate()
            self.ngrok_process.wait()
    
    def update_deploy_config(self):
        """Обновление конфигурации деплоя с новым URL"""
        if not self.public_url:
            return
            
        # Обновляем переменную окружения
        os.environ['NGROK_URL'] = self.public_url
        print(f"📝 Обновлена переменная окружения NGROK_URL: {self.public_url}")

def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\n🛑 Получен сигнал завершения...")
    if ngrok_manager:
        ngrok_manager.stop_ngrok()
    sys.exit(0)

def start_fastapi():
    """Запуск FastAPI приложения"""
    print("🚀 Запуск FastAPI приложения...")
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=False)

if __name__ == "__main__":
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    ngrok_manager = NgrokManager()
    
    try:
        # Запускаем ngrok
        if not ngrok_manager.start_ngrok():
            print("❌ Не удалось запустить ngrok. Завершение работы.")
            sys.exit(1)
        
        # Обновляем конфигурацию
        ngrok_manager.update_deploy_config()
        
        # Запускаем FastAPI
        start_fastapi()
        
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал прерывания...")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
    finally:
        ngrok_manager.stop_ngrok()
        print("✅ Приложение завершено.")

