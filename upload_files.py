#!/usr/bin/env python3
"""
Скрипт для загрузки файлов на сервер
"""
import subprocess
import os
import sys

def run_command(cmd, description):
    """Выполнить команду и показать результат"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - успешно")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - ошибка")
            if result.stderr:
                print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} - исключение: {e}")
        return False

def main():
    print("🚀 Загрузка мобильной адаптивности на сервер")
    print("=" * 50)
    
    # Проверяем наличие файлов
    files_to_upload = [
        "static/style.css",
        "static/script.js", 
        "static/index.html"
    ]
    
    for file_path in files_to_upload:
        if not os.path.exists(file_path):
            print(f"❌ Файл {file_path} не найден!")
            return False
    
    print("✅ Все файлы найдены")
    
    # Создаем архив
    if not run_command("tar -czf mobile_update.tar.gz static/style.css static/script.js static/index.html", 
                      "Создание архива"):
        return False
    
    print("\n📦 Архив создан: mobile_update.tar.gz")
    print("\n📋 Инструкции для загрузки:")
    print("1. Загрузите архив на сервер:")
    print("   scp -P 1100 mobile_update.tar.gz rvs@37.110.51.35:~/windexai-project/")
    print("\n2. Подключитесь к серверу:")
    print("   ssh rvs@37.110.51.35 -p 1100")
    print("\n3. На сервере выполните:")
    print("   cd ~/windexai-project")
    print("   tar -xzf mobile_update.tar.gz")
    print("   rm mobile_update.tar.gz")
    print("   sudo systemctl restart windexai")
    print("\n🎉 Мобильная адаптивность будет активирована!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

