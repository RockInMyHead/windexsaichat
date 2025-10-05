#!/bin/bash

# WindexAI Chat - Ngrok Management Script
# Автор: WindexAI Assistant

NGROK_URL=""
NGROK_PID=""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Функция для проверки статуса сервера
check_server() {
    if lsof -i :8003 > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Функция для запуска ngrok
start_ngrok() {
    if ! check_server; then
        error "Сервер не запущен на порту 8003"
        info "Сначала запустите сервер: python main.py"
        exit 1
    fi

    log "Запуск ngrok туннеля для порта 8003..."

    # Запускаем ngrok в фоне
    ngrok http 8003 --log=stdout > /dev/null 2>&1 &
    NGROK_PID=$!

    # Ждем запуска
    sleep 3

    # Получаем URL туннеля
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['tunnels']:
    print(data['tunnels'][0]['public_url'])
else:
    print('')
")

    if [ -n "$NGROK_URL" ]; then
        log "✅ Ngrok туннель запущен!"
        info "🌐 Публичный URL: $NGROK_URL"
        info "📊 Веб-интерфейс ngrok: http://localhost:4040"
        info "🛑 Для остановки нажмите Ctrl+C"

        # Сохраняем URL в файл
        echo "$NGROK_URL" > .ngrok_url

        # Ждем сигнала завершения
        trap cleanup EXIT
        wait $NGROK_PID
    else
        error "Не удалось получить URL туннеля"
        exit 1
    fi
}

# Функция для остановки ngrok
stop_ngrok() {
    if [ -n "$NGROK_PID" ]; then
        log "Остановка ngrok туннеля..."
        kill $NGROK_PID 2>/dev/null
    fi

    # Убиваем все процессы ngrok
    pkill ngrok 2>/dev/null

    # Удаляем файл с URL
    rm -f .ngrok_url

    log "Ngrok туннель остановлен"
}

# Функция очистки при выходе
cleanup() {
    stop_ngrok
    exit 0
}

# Функция для показа статуса
show_status() {
    if check_server; then
        info "✅ Сервер запущен на порту 8003"
    else
        warning "❌ Сервер не запущен на порту 8003"
    fi

    if pgrep ngrok > /dev/null; then
        info "✅ Ngrok туннель активен"
        if [ -f .ngrok_url ]; then
            NGROK_URL=$(cat .ngrok_url)
            info "🌐 Публичный URL: $NGROK_URL"
        fi
    else
        warning "❌ Ngrok туннель не активен"
    fi
}

# Основная логика
case "$1" in
    "start")
        start_ngrok
        ;;
    "stop")
        stop_ngrok
        ;;
    "status")
        show_status
        ;;
    "restart")
        stop_ngrok
        sleep 2
        start_ngrok
        ;;
    *)
        echo "WindexAI Chat - Ngrok Management"
        echo ""
        echo "Использование: $0 {start|stop|status|restart}"
        echo ""
        echo "Команды:"
        echo "  start   - Запустить ngrok туннель"
        echo "  stop    - Остановить ngrok туннель"
        echo "  status  - Показать статус сервера и туннеля"
        echo "  restart - Перезапустить ngrok туннель"
        echo ""
        echo "Примеры:"
        echo "  $0 start    # Запустить туннель"
        echo "  $0 status   # Проверить статус"
        echo "  $0 stop     # Остановить туннель"
        ;;
esac
