# Инструкции для загрузки проекта на GitHub

## Проблема с доступом
Получена ошибка доступа к репозиторию `https://github.com/NexDjen/WindexsAI.git`. 

## Возможные решения:

### 1. Проверьте права доступа
Убедитесь, что у вас есть права на запись в репозиторий `NexDjen/WindexsAI`:
- Вы должны быть владельцем репозитория
- Или быть добавлены как collaborator с правами на запись

### 2. Настройте SSH ключи (если используете SSH)
```bash
# Проверьте существующие SSH ключи
ls -la ~/.ssh

# Если ключей нет, создайте новый
ssh-keygen -t ed25519 -C "your_email@example.com"

# Добавьте ключ в ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Скопируйте публичный ключ
cat ~/.ssh/id_ed25519.pub
```

Затем добавьте этот ключ в настройки GitHub: Settings → SSH and GPG keys

### 3. Используйте Personal Access Token
```bash
# Настройте remote с токеном
git remote set-url nexjen https://YOUR_TOKEN@github.com/NexDjen/WindexsAI.git
```

### 4. Создайте форк репозитория
Если у вас нет прав на оригинальный репозиторий:
1. Перейдите на https://github.com/NexDjen/WindexsAI
2. Нажмите "Fork" в правом верхнем углу
3. Создайте форк в своем аккаунте
4. Обновите remote URL:
```bash
git remote set-url nexjen https://github.com/YOUR_USERNAME/WindexsAI.git
```

### 5. Альтернативный способ - создание нового репозитория
Если репозиторий пустой или недоступен:
1. Создайте новый репозиторий в своем аккаунте
2. Обновите remote URL:
```bash
git remote set-url nexjen https://github.com/YOUR_USERNAME/NEW_REPO_NAME.git
```

## После настройки доступа выполните:

```bash
# Проверьте remote
git remote -v

# Загрузите проект
git push nexjen main

# Если это первый push в пустой репозиторий
git push -u nexjen main
```

## Текущее состояние проекта:
- ✅ Все изменения зафиксированы в Git
- ✅ Remote настроен на `NexDjen/WindexsAI`
- ❌ Нет прав доступа для загрузки

## Файлы готовые для загрузки:
- Основной код проекта
- Статические файлы (HTML, CSS, JS)
- Скрипты деплоя
- Документация
- Архив проекта для серверного деплоя
