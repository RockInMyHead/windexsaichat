#!/usr/bin/env python3
import subprocess
import sys
import os

def upload_file(local_file, remote_path):
    """Загрузить файл на сервер"""
    print(f"📤 Загружаем {local_file}...")
    
    # Команда scp
    cmd = f"scp -P 1100 {local_file} rvs@37.110.51.35:{remote_path}"
    
    try:
        # Запускаем процесс
        process = subprocess.Popen(
            cmd, 
            shell=True, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Отправляем пароль
        stdout, stderr = process.communicate(input="640509040147\n")
        
        if process.returncode == 0:
            print(f"✅ {local_file} загружен успешно")
            return True
        else:
            print(f"❌ Ошибка загрузки {local_file}: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при загрузке {local_file}: {e}")
        return False

def main():
    print("🚀 Загрузка мобильной адаптивности на сервер")
    print("=" * 50)
    
    # Файлы для загрузки
    files = [
        ("static/style.css", "~/windexai-project/static/"),
        ("static/script.js", "~/windexai-project/static/"),
        ("static/index.html", "~/windexai-project/static/")
    ]
    
    success_count = 0
    
    for local_file, remote_path in files:
        if os.path.exists(local_file):
            if upload_file(local_file, remote_path):
                success_count += 1
        else:
            print(f"❌ Файл {local_file} не найден!")
    
    print(f"\n📊 Результат: {success_count}/{len(files)} файлов загружено")
    
    if success_count == len(files):
        print("\n🔄 Перезапускаем сервер...")
        restart_cmd = "ssh -p 1100 rvs@37.110.51.35 'cd ~/windexai-project && sudo systemctl restart windexai'"
        
        try:
            process = subprocess.Popen(
                restart_cmd, 
                shell=True, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input="640509040147\n")
            
            if process.returncode == 0:
                print("✅ Сервер перезапущен успешно!")
                print("\n🎉 Мобильная адаптивность активирована!")
                print("📱 Откройте http://37.110.51.35:1107 на мобильном устройстве")
            else:
                print(f"❌ Ошибка перезапуска сервера: {stderr}")
                
        except Exception as e:
            print(f"❌ Исключение при перезапуске: {e}")
    else:
        print("\n❌ Не все файлы загружены. Проверьте ошибки выше.")

if __name__ == "__main__":
    main()

