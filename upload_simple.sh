#!/usr/bin/expect -f

# Скрипт для загрузки файлов на сервер
set timeout 30
set password "640509040147"

# Загружаем style.css
spawn scp -P 1100 static/style.css rvs@37.110.51.35:~/windexai-project/static/
expect "password:"
send "$password\r"
expect eof

# Загружаем script.js
spawn scp -P 1100 static/script.js rvs@37.110.51.35:~/windexai-project/static/
expect "password:"
send "$password\r"
expect eof

# Загружаем index.html
spawn scp -P 1100 static/index.html rvs@37.110.51.35:~/windexai-project/static/
expect "password:"
send "$password\r"
expect eof

# Перезапускаем сервер
spawn ssh -p 1100 rvs@37.110.51.35 "cd ~/windexai-project && sudo systemctl restart windexai"
expect "password:"
send "$password\r"
expect eof

puts "✅ Все файлы загружены и сервер перезапущен!"

