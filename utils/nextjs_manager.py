"""Next.js Server Manager для управления live-превью проектов"""
import os
import subprocess
import time
import psutil
from typing import Dict, Optional


class NextJSServerManager:
    """Менеджер для управления Next.js серверами"""
    
    def __init__(self):
        self.servers = {}  # project_id -> server_info
        self.base_port = 3000
        
    def start_nextjs_server(self, project_id: str, project_dir: str) -> Dict[str, str]:
        """Запускает Next.js сервер для проекта"""
        
        # Проверяем, не запущен ли уже сервер для этого проекта
        if project_id in self.servers:
            server_info = self.servers[project_id]
            if self._is_port_active(server_info['port']):
                return server_info
            else:
                # Сервер не активен, удаляем из списка
                del self.servers[project_id]
        
        # Находим свободный порт
        port = self._find_free_port()
        if port is None:
            raise Exception("Не удалось найти свободный порт")
        
        # Проверяем наличие package.json
        package_json_path = os.path.join(project_dir, 'package.json')
        if not os.path.exists(package_json_path):
            raise Exception("package.json не найден")
        
        try:
            # Подготавливаем окружение с nvm
            env = os.environ.copy()
            env['NVM_DIR'] = os.path.expanduser('~/.nvm')
            
            # Загружаем nvm
            nvm_script = os.path.join(env['NVM_DIR'], 'nvm.sh')
            if os.path.exists(nvm_script):
                # Используем bash для загрузки nvm и выполнения команд
                bash_cmd = f'source {nvm_script} && nvm use 18 && npm install'
            else:
                # Fallback без nvm
                bash_cmd = 'npm install'
            
            # Устанавливаем зависимости
            npm_install = subprocess.run(
                ['bash', '-c', bash_cmd],
                cwd=project_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if npm_install.returncode != 0:
                stderr = npm_install.stderr or ''
                # При ошибке недостатка места на диске (ENOSPC)
                if 'ENOSPC' in stderr:
                    raise Exception("Недостаточно места на диске для установки зависимостей (ENOSPC)")
                raise Exception(f"Ошибка npm install: {stderr}")
            
            # Запускаем Next.js сервер
            env['PORT'] = str(port)
            
            # Команда для запуска с nvm
            if os.path.exists(nvm_script):
                dev_cmd = f'source {nvm_script} && nvm use 18 && npm run dev -- --port {port} --hostname 0.0.0.0'
            else:
                dev_cmd = f'npm run dev -- --port {port} --hostname 0.0.0.0'
            
            process = subprocess.Popen(
                ['bash', '-c', dev_cmd],
                cwd=project_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Ждем запуска сервера
            start_time = time.time()
            while time.time() - start_time < 60:  # ждем максимум 60 секунд
                if self._is_port_active(port):
                    break
                time.sleep(1)
            else:
                process.terminate()
                # Получаем вывод для диагностики
                stdout, stderr = process.communicate()
                error_msg = f"Таймаут запуска Next.js сервера. STDOUT: {stdout[:200]}... STDERR: {stderr[:200]}..."
                raise Exception(error_msg)
            
            server_info = {
                'process': process,
                'port': port,
                'url': f'http://37.110.51.35:{port}',
                'status': 'running',
                'project_dir': project_dir
            }
            
            self.servers[project_id] = server_info
            return server_info
            
        except Exception as e:
            raise Exception(f"Ошибка запуска Next.js сервера: {str(e)}")
    
    def _find_free_port(self, start_port: int = None) -> Optional[int]:
        """Находит свободный порт"""
        if start_port is None:
            start_port = self.base_port
        
        for port in range(start_port, start_port + 100):
            if not self._is_port_active(port):
                return port
        return None
    
    def _is_port_active(self, port: int) -> bool:
        """Проверяет, активен ли порт"""
        import socket
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(('localhost', port))
                return True
            except (ConnectionRefusedError, OSError):
                return False


# Создаем глобальный экземпляр для обратной совместимости
nextjs_manager = NextJSServerManager()
