// Тестовый вывод для диагностики
console.log('JavaScript файл загружен и выполняется!');

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('windexai_token');
        this.user = null;
        this.initializeAuth();
    }

    initializeAuth() {
        if (this.token) {
            this.verifyToken();
        } else {
            this.showAuthModal();
        }
    }

    async verifyToken() {
        try {
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                this.user = await response.json();
                this.showMainApp();
            } else {
                this.logout();
            }
        } catch (error) {
            console.error('Token verification failed:', error);
            this.logout();
        }
    }

    async login(email, password) {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });

            if (response.ok) {
                const data = await response.json();
                this.token = data.access_token;
                localStorage.setItem('windexai_token', this.token);
                await this.verifyToken();
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка входа');
            }
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    }

    async register(username, email, password) {
        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, email, password })
            });

            if (response.ok) {
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка регистрации');
            }
        } catch (error) {
            console.error('Registration failed:', error);
            throw error;
        }
    }

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('windexai_token');
        this.showAuthModal();
    }

    showAuthModal() {
        document.getElementById('auth-modal').style.display = 'flex';
        document.getElementById('main-app').classList.add('hidden');
    }

    showMainApp() {
        document.getElementById('auth-modal').style.display = 'none';
        document.getElementById('main-app').classList.remove('hidden');
    }

    getAuthHeaders() {
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }
}

class WindexAI {
    constructor(authManager) {
        this.authManager = authManager;
        this.currentConversationId = null;
        this.currentModel = 'gpt-4o-mini';
        this.isLoading = false;

        this.initializeElements();
        this.bindEvents();
        this.loadConversations();
    }

    initializeElements() {
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.voiceBtn = document.getElementById('voice-btn');
        this.connectBtn = document.getElementById('connect-btn');
        this.documentBtn = document.getElementById('document-btn');
        this.documentInput = document.getElementById('document-input');
        this.toolsBtn = document.getElementById('tools-btn');
        this.toolsDropdown = document.getElementById('tools-dropdown');
        this.chatContainer = document.getElementById('chat-container');
        this.chatMessages = document.getElementById('chat-messages');
        this.welcomeMessage = document.getElementById('welcome-message');
        this.selectedModel = document.getElementById('selected-model');
        this.modelIcon = document.getElementById('model-icon');
        this.modelName = document.getElementById('model-name');
        this.modelDescription = document.getElementById('model-description');
        // Typing indicator is now created dynamically
        this.documentUploadIndicator = document.getElementById('document-upload-indicator');
        this.conversationsList = document.getElementById('conversations-list');
        this.clearHistoryBtn = document.getElementById('clear-history-btn');
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.modelCards = document.querySelectorAll('.model-card');
        this.userAvatar = document.getElementById('user-avatar');
        this.userName = document.getElementById('user-name');

        // Connect modal elements
        this.connectModal = document.getElementById('connect-modal');
        this.closeConnectBtn = document.querySelector('.close-connect');
        this.connectionUsernameInput = document.getElementById('connection-username');
        this.connectionPasswordInput = document.getElementById('connection-password');
        this.testConnectionBtn = document.getElementById('test-connection-btn');
        this.connectBtnModal = document.getElementById('connect-btn-modal');
        this.connectionStatus = document.getElementById('connection-status');
        this.connectionResult = document.getElementById('connection-result');

        // Voice recording variables
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.recordingTimer = null;
        this.recordingStartTime = null;

        // Debug: Check if all elements are found
    }

    bindEvents() {
        // Message input
        this.messageInput.addEventListener('input', () => {
            this.toggleSendButton();
            this.autoResize();
        });

        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (this.toolsDropdown && !this.toolsDropdown.contains(e.target) && !this.toolsBtn.contains(e.target)) {
                this.hideToolsDropdown();
            }
        });

        // Logo click handler
        const logoClickable = document.getElementById('logo-clickable');
        if (logoClickable) {
            logoClickable.addEventListener('click', () => {
                this.showWelcomeMessage();
            });
        }

        // Send button
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        // Voice button
        if (this.voiceBtn) {
            this.voiceBtn.addEventListener('click', () => {
                this.toggleVoiceRecording();
            });
        }

        // Connect button
        if (this.connectBtn) {
            this.connectBtn.addEventListener('click', () => {
                this.showConnectModal();
                this.hideToolsDropdown();
            });
        }

        // Tools dropdown button - enable toggling
        if (this.toolsBtn) {
            this.toolsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleToolsDropdown();
            });
        }

        // Document button
        if (this.documentBtn) {
            this.documentBtn.addEventListener('click', () => {
                this.documentInput.click();
                this.hideToolsDropdown();
            });
        }

        // Document input
        if (this.documentInput) {
            this.documentInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.uploadDocument(e.target.files[0]);
                }
            });
        }

        // Model cards
        this.modelCards.forEach((card, index) => {
            card.addEventListener('click', (e) => {
                const model = card.dataset.model;
                this.selectModel(model);
            });
        });

        // Specialist cards
        const specialistCards = document.querySelectorAll('.specialist-card');
        specialistCards.forEach((card) => {
            card.addEventListener('click', (e) => {
                const specialist = card.dataset.specialist;
                const model = card.dataset.model;
                this.selectSpecialist(specialist, model);
            });
        });


        // Clear history button
        this.clearHistoryBtn.addEventListener('click', () => {
            this.clearHistory();
        });


        // Connect modal handlers
        if (this.closeConnectBtn) {
            this.closeConnectBtn.addEventListener('click', () => {
                this.hideConnectModal();
            });
        }

        if (this.testConnectionBtn) {
            this.testConnectionBtn.addEventListener('click', () => {
                this.testConnection();
            });
        }

        if (this.connectBtnModal) {
            this.connectBtnModal.addEventListener('click', () => {
                this.connectToChat();
            });
        }

    }

    async selectModel(model) {
        // Проверяем подписку для Pro модели
        if (model === 'gpt-4o') {
            const hasProSubscription = await checkProSubscription();
            if (!hasProSubscription) {
                showProSubscriptionModal();
                return;
            }
        }

        this.currentModel = model;

        // Update model info
        const modelInfo = this.getModelInfo(model);
        this.modelIcon.textContent = modelInfo.icon;
        this.modelName.textContent = modelInfo.name;
        this.modelDescription.textContent = modelInfo.description;

        // Show selected model and hide welcome message
        this.showSelectedModel();
        this.hideWelcomeMessage();

        showNotification(`Выбрана модель: ${modelInfo.name}`, 'success');
        this.messageInput.focus();
    }

    selectSpecialist(specialist, model) {
        this.currentModel = model;
        this.currentSpecialist = specialist;

        // Update model info with specialist details
        const specialistInfo = this.getSpecialistInfo(specialist);
        const modelInfo = this.getModelInfo(model);

        this.modelIcon.textContent = specialistInfo.icon;
        this.modelName.textContent = specialistInfo.name;
        this.modelDescription.textContent = specialistInfo.description;

        // Show selected model and hide welcome message
        this.showSelectedModel();
        this.hideWelcomeMessage();

        showNotification(`Выбран специалист: ${specialistInfo.name}`, 'success');
        this.messageInput.focus();
    }

    getModelInfo(model) {
        const models = {
            'gpt-4o-mini': {
                icon: 'L',
                name: 'WIndexAI Lite',
                description: 'Быстрая и эффективная модель для повседневных задач'
            },
            'gpt-4o': {
                icon: 'P',
                name: 'WIndexAI Pro',
                description: 'Продвинутая модель с расширенными возможностями'
            }
        };
        return models[model] || models['gpt-4o-mini'];
    }

    getSpecialistInfo(specialist) {
        const specialists = {
            'mentor': {
                icon: '🎓',
                name: 'AI Ментор',
                description: 'Персональный наставник для развития навыков и карьеры'
            },
            'psychologist': {
                icon: '🧠',
                name: 'AI Психолог',
                description: 'Поддержка психического здоровья и эмоционального благополучия'
            },
            'programmer': {
                icon: '💻',
                name: 'AI Программист',
                description: 'Эксперт по разработке и техническим решениям'
            },
            'accountant': {
                icon: '📊',
                name: 'AI Бухгалтер',
                description: 'Финансовый консультант и эксперт по учету'
            },
            'analyst': {
                icon: '📈',
                name: 'AI Аналитик',
                description: 'Специалист по анализу данных и бизнес-процессов'
            },
            'general': {
                icon: '',
                name: 'Универсальный AI',
                description: 'Многофункциональный помощник для любых задач'
            }
        };
        return specialists[specialist] || specialists['general'];
    }

    showSelectedModel() {
        this.selectedModel.classList.remove('hidden');
    }

    hideSelectedModel() {
        this.selectedModel.classList.add('hidden');
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;

        this.isLoading = true;
        this.showLoading();

        // Hide welcome message if it's showing
        this.hideWelcomeMessage();
        this.showChatMessages();

        // Add user message to chat
        this.addMessageToChat('user', message);
        this.messageInput.value = '';
        this.toggleSendButton();

        // Show typing indicator
        this.showTypingIndicator();

        // Check if web search will be performed and show search indicator
        if (this.shouldShowWebSearchIndicator(message)) {
            this.showWebSearchIndicator();
        }

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: this.authManager.getAuthHeaders(),
                body: JSON.stringify({
                    message: message,
                    model: this.currentModel,
                    conversation_id: this.currentConversationId,
                    specialist: this.currentSpecialist || null
                })
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.authManager.logout();
                    throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
                }
                throw new Error('Ошибка при отправке сообщения');
            }

            const data = await response.json();
            this.currentConversationId = data.conversation_id;

            // Hide typing indicator and add AI response
            this.hideTypingIndicator();
            this.hideWebSearchIndicator();
            this.addMessageToChat('assistant', data.response);

            // Update conversations list
            this.loadConversations();

        } catch (error) {
            console.error('Error:', error);
            this.hideTypingIndicator();
            this.hideWebSearchIndicator();
            this.addMessageToChat('assistant', 'Извините, произошла ошибка. Попробуйте еще раз.');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    // Проверка, нужно ли показывать индикатор поиска в интернете
    shouldShowWebSearchIndicator(message) {
        const message_lower = message.toLowerCase().trim();

        // Исключения - запросы, для которых НЕ нужен поиск
        const no_search_patterns = [
            // Приветствия и благодарности
            /^(привет|здравствуй|добрый день|доброе утро|добрый вечер|спасибо|благодар|пока|до свидания)$/,
            /^(hi|hello|hey|thanks|thank you|bye|goodbye)$/,

            // Простые ответы на вопросы бота
            /как дела|что делаешь|кто ты|что ты умеешь/,
            /расскажи о себе|что ты можешь/,

            // Команды управления
            /очистить|удалить|новый чат|стоп|хватит/,
            /clear|delete|new chat|stop/,

            // Математические операции (простые)
            /^\d+[\+\-\*\/]\d+.*$/,
            /^вычисли|посчитай|сколько будет/,

            // Очень короткие сообщения (1-2 слова)
            /^\w{1,10}(\s+\w{1,10})?$/
        ];

        // Проверяем, попадает ли сообщение под исключения
        for (const pattern of no_search_patterns) {
            if (pattern.test(message_lower)) {
                return false;
            }
        }

        // Для ВСЕХ остальных запросов показываем индикатор поиска
        return true;
    }

    // Показать индикатор поиска в интернете
    showWebSearchIndicator() {
        // Remove existing search indicator if any
        this.hideWebSearchIndicator();

        // Create new search indicator
        const searchDiv = document.createElement('div');
        searchDiv.id = 'web-search-indicator';
        searchDiv.className = 'web-search-indicator';

        searchDiv.innerHTML = `
            <div class="chat-avatar"></div>
            <div class="search-bubble">
                <div class="search-content">
                    <div class="search-icon">🔍</div>
                    <div class="search-text">
                        <span>Ищу актуальную информацию в интернете...</span>
                    </div>
                </div>
            </div>
        `;

        // Add to chat messages
        this.chatMessages.appendChild(searchDiv);

        // Scroll to bottom
        setTimeout(() => this.scrollToBottom(), 50);
    }

    // Скрыть индикатор поиска в интернете
    hideWebSearchIndicator() {
        const searchIndicator = document.getElementById('web-search-indicator');
        if (searchIndicator) {
            searchIndicator.remove();
        }
    }

    // Функция для конвертации Markdown в HTML
    convertMarkdownToHtml(text) {
        if (!text) return '';

        // Специальная обработка математических выражений - сохраняем их в HTML комментариях
        // Блочные математические выражения $$...$$ или \[...\]
        const blockMathRegex = /(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\])/g;
        text = text.replace(blockMathRegex, (match) => {
            // Сохраняем в HTML комментариях, которые не будут обрабатываться markdown
            return `<!-- MATH_BLOCK_START -->${match}<!-- MATH_BLOCK_END -->`;
        });

        // Inline математические выражения - только если содержат LaTeX команды или операторы
        const inlineMathRegex = /(\$[^\$\n]*\$|\\\(.*\)\))/g;
        text = text.replace(inlineMathRegex, (match) => {
            // Проверяем, что это действительно математическое выражение
            const hasMathSymbols = /\\[a-zA-Z]+|[-+=×÷∑∫√^_]/.test(match);
            if (match.length > 2 && hasMathSymbols) {
                return `<!-- MATH_INLINE_START -->${match}<!-- MATH_INLINE_END -->`;
            }
            return match;
        });

        // Экранируем HTML теги
        text = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');

        // Специальная обработка для случаев, когда код идет сплошным текстом
        // Ищем паттерны типа "python def function()" в начале строк
        text = text.replace(/(\n|^)(python|javascript|html|css|json|sql|bash|java|cpp|c\+\+|c#|php|ruby|go|rust|swift|kotlin|typescript|js|py|sh)\s+(def\s+\w+|function\s+\w+|class\s+\w+|import\s+|from\s+|if\s+.*:|for\s+.*:|while\s+.*:|try:|except|catch|var\s+|let\s+|const\s+|<html|<head|<body|<div|<script|<style|SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)([\s\S]*?)(?=\n\n|\n[А-Я]|\n[а-я]|\n[A-Z][a-z]|\n\d+\.|\n-|\n\*|$)/g, (match, prefix, language, start, code) => {
            // Проверяем, что это действительно код (содержит отступы, ключевые слова)
            if (code.includes('    ') || code.includes('\t') || code.includes('def ') || code.includes('function ') || code.includes('class ') || code.includes('<') || code.includes('SELECT') || code.includes('INSERT')) {
                return `${prefix}\`\`\`${language}\n${start}${code.trim()}\`\`\``;
            }
            return match;
        });

        // Сначала обрабатываем блоки кода - это приоритетно
        // Исправляем неправильные маркеры кода типа `python def function()`
        text = text.replace(/`(\w+)\s+([\s\S]*?)`/g, (match, language, code) => {
            // Если код содержит переносы строк или длинный - это блок кода
            if (code.includes('\n') || code.length > 50) {
                return `\`\`\`${language}\n${code}\`\`\``;
            }
            return match; // Оставляем как inline код
        });

        // Обрабатываем правильные блоки кода ```language\ncode```
        text = text.replace(/```(\w+)?\n?([\s\S]*?)```/g, (match, language, code) => {
            const lang = language || 'text';
            const cleanCode = code.trim();
            return `<div class="code-block">
                <div class="code-header">
                    <span class="code-language">${lang}</span>
                    <button class="code-copy-button" onclick="copyCodeToClipboard(this)">📋 Копировать</button>
                </div>
                <pre data-language="${lang}"><code>${cleanCode}</code></pre>
            </div>`;
        });

        // After escaping HTML tags, add table conversion
        text = text.split('\n').map(line => line).join('\n');
        let lines = text.split('\n');
        let resultLines = [];
        for (let i = 0; i < lines.length; i++) {
            // Detect start of markdown table
            if (lines[i].trim().startsWith('|') && i + 1 < lines.length && lines[i+1].includes('---')) {
                // Header and separator found
                let headerLine = lines[i].trim();
                let sepLine = lines[i+1];
                let j = i + 2;
                let rows = [];
                while (j < lines.length && lines[j].trim().startsWith('|')) {
                    rows.push(lines[j].trim());
                    j++;
                }
                // Parse header cells
                let headers = headerLine.slice(1, -1).split('|').map(h => h.trim());
                // Build HTML table
                let tableHtml = '<table class="markdown-table"><thead><tr>';
                headers.forEach(cell => tableHtml += `<th>${cell}</th>`);
                tableHtml += '</tr></thead><tbody>';
                rows.forEach(rowLine => {
                    let cells = rowLine.slice(1, -1).split('|').map(c => c.trim());
                    tableHtml += '<tr>';
                    cells.forEach(cell => tableHtml += `<td>${cell}</td>`);
                    tableHtml += '</tr>';
                });
                tableHtml += '</tbody></table>';
                resultLines.push(tableHtml);
                i = j - 1; // Skip processed lines
            } else {
                resultLines.push(lines[i]);
            }
        }
        text = resultLines.join('\n');

        // Теперь обрабатываем остальной markdown
        // Жирный текст **text** или __text__
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/__(.*?)__/g, '<strong>$1</strong>');

        // Курсив *text* или _text_
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        text = text.replace(/_(.*?)_/g, '<em>$1</em>');

        // Заголовки (обрабатываем от h6 к h1, чтобы избежать пересечений)
        text = text.replace(/^######\s+(.*)$/gim, '<h6>$1</h6>');
        text = text.replace(/^#####\s+(.*)$/gim, '<h5>$1</h5>');
        text = text.replace(/^####\s+(.*)$/gim, '<h4>$1</h4>');
        text = text.replace(/^###\s+(.*)$/gim, '<h3>$1</h3>');
        text = text.replace(/^##\s+(.*)$/gim, '<h2>$1</h2>');
        text = text.replace(/^#\s+(.*)$/gim, '<h1>$1</h1>');

        // Списки
        text = text.replace(/^\d+\.\s+(.*$)/gim, '<li>$1</li>');
        text = text.replace(/^[-*]\s+(.*$)/gim, '<li>$1</li>');

        // Обертываем списки в ul/ol
        text = text.replace(/(<li>.*<\/li>)/gs, (match) => {
            if (match.match(/^\d+\./)) {
                return '<ol>' + match + '</ol>';
            } else {
                return '<ul>' + match + '</ul>';
            }
        });

        // Inline код `code` (только если не внутри блока кода)
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Ссылки [text](url)
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

        // Разделители ---
        text = text.replace(/^---$/gim, '<hr>');

        // Переносы строк в параграфы
        text = text.replace(/\n\n/g, '</p><p>');
        text = '<p>' + text + '</p>';

        // Обрабатываем различные форматы диаграмм
        // Mermaid диаграммы
        text = text.replace(/```mermaid\s*([\s\S]*?)```/g, (match, diagramCode) => {
            const cleanCode = diagramCode.trim();
            return `<div class="mermaid-diagram">
                <div class="diagram-header">
                    <span class="diagram-title">Диаграмма Mermaid</span>
                    <button class="diagram-copy-btn" onclick="copyDiagramCode(this)">📋</button>
                </div>
                <div class="mermaid" data-code="${btoa(cleanCode)}">${cleanCode}</div>
            </div>`;
        });

        // Диаграммы в формате блок-схем (flowchart)
        text = text.replace(/```flowchart\s*([\s\S]*?)```/g, (match, diagramCode) => {
            const cleanCode = diagramCode.trim();
            return `<div class="flowchart-diagram">
                <div class="diagram-header">
                    <span class="diagram-title">Блок-схема</span>
                    <button class="diagram-copy-btn" onclick="copyDiagramCode(this)">📋</button>
                </div>
                <div class="flowchart" data-code="${btoa(cleanCode)}">${cleanCode}</div>
            </div>`;
        });

        // Диаграммы последовательности (sequence)
        text = text.replace(/```sequence\s*([\s\S]*?)```/g, (match, diagramCode) => {
            const cleanCode = diagramCode.trim();
            return `<div class="sequence-diagram">
                <div class="diagram-header">
                    <span class="diagram-title">Диаграмма последовательности</span>
                    <button class="diagram-copy-btn" onclick="copyDiagramCode(this)">📋</button>
                </div>
                <div class="sequence" data-code="${btoa(cleanCode)}">${cleanCode}</div>
            </div>`;
        });

        // Автоматическое распознавание диаграмм в тексте
        text = text.replace(/```(\w+)?\s*([\s\S]*?)```/g, (match, lang, code) => {
            const cleanCode = code.trim();
            const lowerLang = (lang || '').toLowerCase();

            // Определяем тип диаграммы
            if (lowerLang.includes('diagram') || lowerLang.includes('chart') || lowerLang.includes('graph')) {
                return `<div class="auto-diagram">
                    <div class="diagram-header">
                        <span class="diagram-title">Диаграмма</span>
                        <button class="diagram-copy-btn" onclick="copyDiagramCode(this)">📋</button>
                    </div>
                    <div class="diagram-content" data-code="${btoa(cleanCode)}">${cleanCode}</div>
                </div>`;
            }

            return match; // Оставляем как есть для других типов кода
        });

        // Убираем пустые параграфы
        text = text.replace(/<p><\/p>/g, '');
        text = text.replace(/<p>\s*<\/p>/g, '');

        // Восстанавливаем математические выражения из HTML комментариев
        text = text.replace(/<!-- MATH_BLOCK_START -->(.*?)<!-- MATH_BLOCK_END -->/g, '$1');
        text = text.replace(/<!-- MATH_INLINE_START -->(.*?)<!-- MATH_INLINE_END -->/g, '$1');

        return text;
    }

    addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role} fade-in`;

        // Добавляем аватар только для ассистента
        if (role === 'assistant') {
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = '';
            messageDiv.appendChild(avatar);
        }

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';

        // Конвертируем Markdown в HTML для сообщений ассистента
        if (role === 'assistant') {
            bubble.innerHTML = this.convertMarkdownToHtml(content);
        } else {
            bubble.textContent = content;
        }

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageContent.appendChild(bubble);
        messageContent.appendChild(time);
        
        // Add action text for assistant messages
        if (role === 'assistant') {
            const copyText = document.createElement('span');
            copyText.className = 'action-text copy-text';
            copyText.textContent = 'Копировать';
            copyText.style.cursor = 'pointer';
            copyText.addEventListener('click', (e) => {
                e.stopPropagation();
                this.copyMessage(messageDiv);
            });
            time.appendChild(copyText);
            
            
            const voiceText = document.createElement('span');
            voiceText.className = 'action-text voice-text';
            voiceText.textContent = 'Озвучить';
            voiceText.style.cursor = 'pointer';
            voiceText.addEventListener('click', (e) => {
                e.stopPropagation();
                this.speakMessage(messageDiv);
            });
            time.appendChild(voiceText);
        }
        
        messageDiv.appendChild(messageContent);

        this.chatMessages.appendChild(messageDiv);
        setTimeout(() => this.scrollToBottom(), 50);

        // Рендерим математические выражения в новом сообщении
        setTimeout(() => renderMathInChat(), 100);
    }


    copyMessage(messageElement) {
        const bubble = messageElement.querySelector('.message-bubble');
        if (bubble) {
            const text = bubble.textContent || bubble.innerText;
            navigator.clipboard.writeText(text).then(() => {
                showNotification('Сообщение скопировано в буфер обмена', 'success');
            }).catch(() => {
                showNotification('Не удалось скопировать сообщение', 'error');
            });
        }
    }

    startNewChat() {
        this.currentConversationId = null;
        this.chatMessages.innerHTML = '';
        this.hideChatMessages();
        this.showWelcomeMessage();
        showNotification('Начат новый чат', 'success');
    }

    async speakMessage(messageElement) {
        const bubble = messageElement.querySelector('.message-bubble');
        if (!bubble) return;
        
        const text = bubble.textContent || bubble.innerText;
        if (!text || text.trim().length === 0) {
            showNotification('Нет текста для озвучивания', 'error');
            return;
        }
        
        // Limit text length for TTS
        const textToSpeak = text.length > 1000 ? text.substring(0, 1000) + '...' : text;
        
        try {
            showNotification('Генерация аудио...', 'info');
            
            const formData = new FormData();
            formData.append('text', textToSpeak);
            
            const response = await fetch('/api/tts/generate', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authManager.token}`
                },
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка генерации аудио');
            }
            
            const data = await response.json();
            
            // Play the generated audio
            const audio = new Audio(data.audio_url);
            audio.play();
            
            showNotification('Озвучивание начато', 'success');
            
        } catch (error) {
            console.error('TTS error:', error);
            showNotification(`Ошибка озвучивания: ${error.message}`, 'error');
        }
    }

    // Функция копирования кода диаграммы
    copyDiagramCode(button) {
        const diagramContainer = button.closest('.mermaid-diagram, .flowchart-diagram, .sequence-diagram, .auto-diagram');
        const codeElement = diagramContainer.querySelector('.mermaid, .flowchart, .sequence, .diagram-content');
        const code = atob(codeElement.getAttribute('data-code'));

        navigator.clipboard.writeText(code).then(() => {
            // Показываем уведомление о копировании
            showNotification('Код диаграммы скопирован в буфер обмена', 'success');
        }).catch(() => {
            showNotification('Ошибка при копировании кода', 'error');
        });
    }

    showChatMessages() {
        this.chatMessages.classList.remove('hidden');
    }

    hideChatMessages() {
        this.chatMessages.classList.add('hidden');
    }

    showTypingIndicator() {
        this.createTypingIndicator();
    }

    hideTypingIndicator() {
        this.removeTypingIndicator();
    }


    async loadConversations() {
        try {
            const response = await fetch('/api/conversations', {
                headers: this.authManager.getAuthHeaders()
            });

            if (response.ok) {
                const data = await response.json();
                this.renderConversations(data.conversations);
            } else {
                console.error('Failed to load conversations:', response.status);
                this.renderConversations([]);
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
            this.renderConversations([]);
        }
    }

    renderConversations(conversations) {
        this.conversationsList.innerHTML = '';

        if (conversations.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'text-center';
            emptyState.style.color = 'var(--gray-500)';
            emptyState.style.padding = 'var(--spacing-4)';
            emptyState.textContent = 'Нет сохраненных чатов';
            this.conversationsList.appendChild(emptyState);
            return;
        }

        conversations.forEach(conv => {
            const convElement = document.createElement('div');
            convElement.className = 'conversation-item';
            if (conv.id === this.currentConversationId) convElement.classList.add('active');

            // Main content container
            const contentContainer = document.createElement('div');
            contentContainer.className = 'conversation-content';

            // Title text (first user message)
            const title = document.createElement('div');
            title.className = 'conversation-title';
            title.textContent = conv.title || 'Новый чат';

            // Date and time
            const date = document.createElement('div');
            date.className = 'conversation-date';
            const dt = new Date(conv.date);
            date.textContent = dt.toLocaleDateString('ru-RU') + ' ' + dt.toLocaleTimeString('ru-RU', {hour:'2-digit', minute:'2-digit'});

            contentContainer.appendChild(title);
            contentContainer.appendChild(date);

            // Action buttons container
            const actionsContainer = document.createElement('div');
            actionsContainer.className = 'conversation-actions';

            // Delete button
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'conversation-delete-btn';
            deleteBtn.innerHTML = '🗑️';
            deleteBtn.title = 'Удалить чат';
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteConversation(conv.id);
            });

            // Rename button
            const renameBtn = document.createElement('button');
            renameBtn.className = 'conversation-rename-btn';
            renameBtn.innerHTML = '✏️';
            renameBtn.title = 'Переименовать чат';
            renameBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.renameConversation(conv.id, conv.title);
            });

            actionsContainer.appendChild(renameBtn);
            actionsContainer.appendChild(deleteBtn);

            convElement.appendChild(contentContainer);
            convElement.appendChild(actionsContainer);
            convElement.addEventListener('click', () => this.loadConversation(conv.id));
            this.conversationsList.appendChild(convElement);
        });
    }

    async loadConversation(conversationId) {
        this.currentConversationId = conversationId;
        this.loadConversations(); // Refresh to show active state

        try {
            const response = await fetch(`/api/conversations/${conversationId}`, {
                headers: this.authManager.getAuthHeaders()
            });

            if (response.ok) {
                const data = await response.json();
                this.displayConversation(data.conversation);
            } else {
                console.error('Failed to load conversation:', response.status);
                this.chatContainer.innerHTML = '';
                this.showWelcomeMessage();
            }
        } catch (error) {
            console.error('Error loading conversation:', error);
            this.chatContainer.innerHTML = '';
            this.showWelcomeMessage();
        }
    }

    displayConversation(conversation) {
        this.chatMessages.innerHTML = '';

        if (conversation.messages && conversation.messages.length > 0) {
            this.showChatMessages();
            this.hideWelcomeMessage(); // Скрываем приветственное сообщение
            conversation.messages.forEach(message => {
                this.addMessageToChat(message.role, message.content);
            });

            // Рендерим математические выражения во всех загруженных сообщениях
            setTimeout(() => renderMathInChat(), 200);
        } else {
            this.hideChatMessages();
            this.showWelcomeMessage();
        }

        setTimeout(() => this.scrollToBottom(), 100);
    }

    startNewChat() {
        this.currentConversationId = null;
        this.chatMessages.innerHTML = '';
        this.hideChatMessages();
        this.hideSelectedModel();
        this.showWelcomeMessage();
        this.loadConversations();
    }

    async clearHistory() {
        if (confirm('Вы уверены, что хотите очистить всю историю чатов?')) {
            try {
                const response = await fetch('/api/conversations', {
                    method: 'DELETE',
                    headers: this.authManager.getAuthHeaders()
                });

                if (response.ok) {
                    this.startNewChat();
                    showNotification('История чатов очищена', 'success');
                } else {
                    showNotification('Ошибка при очистке истории', 'error');
                }
            } catch (error) {
                console.error('Error clearing history:', error);
                showNotification('Ошибка при очистке истории', 'error');
            }
        }
    }

    async deleteConversation(conversationId) {
        if (confirm('Вы уверены, что хотите удалить этот чат?')) {
            try {
                const response = await fetch(`/api/conversations/${conversationId}`, {
                    method: 'DELETE',
                    headers: this.authManager.getAuthHeaders()
                });

                if (response.ok) {
                    if (this.currentConversationId === conversationId) {
                        this.startNewChat();
                    }
                    this.loadConversations();
                    showNotification('Чат удален', 'success');
                } else {
                    showNotification('Ошибка при удалении чата', 'error');
                }
            } catch (error) {
                console.error('Error deleting conversation:', error);
                showNotification('Ошибка при удалении чата', 'error');
            }
        }
    }

    async renameConversation(conversationId, currentTitle) {
        const newTitle = prompt('Введите новое название чата:', currentTitle);
        if (newTitle && newTitle.trim() && newTitle !== currentTitle) {
            try {
                const response = await fetch(`/api/conversations/${conversationId}`, {
                    method: 'PUT',
                    headers: {
                        ...this.authManager.getAuthHeaders(),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ title: newTitle.trim() })
                });

                if (response.ok) {
                    this.loadConversations();
                    showNotification('Чат переименован', 'success');
                } else {
                    showNotification('Ошибка при переименовании чата', 'error');
                }
            } catch (error) {
                console.error('Error renaming conversation:', error);
                showNotification('Ошибка при переименовании чата', 'error');
            }
        }
    }

    showWelcomeMessage() {
        this.welcomeMessage.classList.remove('hidden');

        // Re-bind model card events
        this.modelCards = document.querySelectorAll('.model-card');
        this.modelCards.forEach((card, index) => {
            card.addEventListener('click', (e) => {
                const model = card.dataset.model;
                this.selectModel(model);
            });
        });
    }

    hideWelcomeMessage() {
        this.welcomeMessage.classList.add('hidden');
    }



    toggleSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendBtn.disabled = !hasText || this.isLoading;
    }

    autoResize() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }

    showLoading() {
        // Create and show typing indicator at the end of messages
        this.createTypingIndicator();
        this.sendBtn.disabled = true;
        this.sendBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="loading-spinner">
                <circle cx="12" cy="12" r="10" stroke-dasharray="31.416" stroke-dashoffset="31.416">
                    <animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416" repeatCount="indefinite"/>
                    <animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416" repeatCount="indefinite"/>
                </circle>
            </svg>
        `;
    }

    hideLoading() {
        // Remove typing indicator and restore send button
        this.removeTypingIndicator();
        this.sendBtn.disabled = false;
        this.sendBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22,2 15,22 11,13 2,9 22,2"></polygon>
            </svg>
        `;
    }

    createTypingIndicator() {
        // Remove existing typing indicator if any
        this.removeTypingIndicator();
        
        // Create new typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'typing-indicator';
        
        typingDiv.innerHTML = `
            <div class="chat-avatar"></div>
            <div class="typing-bubble">
                <div class="typing-text">
                    <span class="typing-char">W</span>
                    <span class="typing-char">i</span>
                    <span class="typing-char">n</span>
                    <span class="typing-char">d</span>
                    <span class="typing-char">e</span>
                    <span class="typing-char">x</span>
                    <span class="typing-char">A</span>
                    <span class="typing-char">I</span>
                    <span class="typing-char">.</span>
                    <span class="typing-char">.</span>
                    <span class="typing-char">.</span>
                </div>
            </div>
        `;
        
        // Add to the end of chat messages (same as addMessageToChat)
        this.chatMessages.appendChild(typingDiv);
        
        // Debug: log the position
        console.log('Typing indicator added, chat messages children count:', this.chatMessages.children.length);
        console.log('Typing indicator position:', Array.from(this.chatMessages.children).indexOf(typingDiv));
        console.log('Chat messages container:', this.chatMessages);
        console.log('All children:', Array.from(this.chatMessages.children).map(child => child.className));
        
        // Ensure it's visible and scroll to it
        this.chatMessages.classList.remove('hidden');
        setTimeout(() => this.scrollToBottom(), 50);
    }

    removeTypingIndicator() {
        const existingIndicator = document.getElementById('typing-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }
    }

    // Voice recording methods
    async toggleVoiceRecording() {
        if (this.isRecording) {
            this.stopVoiceRecording();
        } else {
            await this.startVoiceRecording();
        }
    }

    async startVoiceRecording() {
        try {
            console.log('Starting voice recording...');
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log('Audio stream obtained:', stream);
            
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                console.log('Audio data available:', event.data.size, 'bytes');
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.processVoiceRecording();
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.recordingStartTime = Date.now();

            this.updateVoiceButton();
            this.startRecordingTimer();

        } catch (error) {
            console.error('Error starting voice recording:', error);
            showNotification('Не удалось получить доступ к микрофону', 'error');
        }
    }

    stopVoiceRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;

            this.updateVoiceButton();
            this.stopRecordingTimer();

            // Stop all tracks
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }


    updateVoiceButton() {
        if (this.voiceBtn) {
            if (this.isRecording) {
                this.voiceBtn.classList.add('recording');
                this.voiceBtn.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="6" y="6" width="12" height="12" rx="2"></rect>
                    </svg>
                `;
            } else {
                this.voiceBtn.classList.remove('recording');
                this.voiceBtn.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                        <line x1="8" y1="23" x2="16" y2="23"></line>
                    </svg>
                `;
            }
        }
    }

    startRecordingTimer() {
        this.recordingTimer = setInterval(() => {
            if (this.recordingStartTime) {
                const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

                // Timer display removed with voice recording indicator
            }
        }, 1000);
    }

    stopRecordingTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
    }

    async processVoiceRecording() {
        if (this.audioChunks.length === 0) {
            console.error('No audio chunks recorded');
            showNotification('Не удалось записать аудио. Попробуйте еще раз.', 'error');
            return;
        }

        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        console.log('Audio blob created:', {
            size: audioBlob.size,
            type: audioBlob.type,
            chunks: this.audioChunks.length
        });
        
        await this.sendVoiceMessage(audioBlob);
    }

    async sendVoiceMessage(audioBlob) {
        this.isLoading = true;
        this.showLoading();

        // Hide welcome message if it's showing
        this.hideWelcomeMessage();
        this.showChatMessages();

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Validate audio blob
            if (!audioBlob || audioBlob.size === 0) {
                throw new Error('Аудио файл пуст или поврежден');
            }
            
            if (audioBlob.size > 25 * 1024 * 1024) { // 25MB limit
                throw new Error('Аудио файл слишком большой (максимум 25MB)');
            }

            console.log('Sending voice message:', {
                size: audioBlob.size,
                type: audioBlob.type,
                conversationId: this.currentConversationId,
                model: this.currentModel
            });

            const formData = new FormData();
            formData.append('audio_file', audioBlob, 'voice-message.webm');
            
            // Send conversation_id as integer or omit if null/undefined
            if (this.currentConversationId) {
                formData.append('conversation_id', this.currentConversationId.toString());
            }
            
            formData.append('model', this.currentModel);
            
            // Debug: log what we're sending
            console.log('FormData contents:');
            for (let [key, value] of formData.entries()) {
                console.log(`${key}:`, value);
            }

            const response = await fetch('/api/voice/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authManager.token}`
                },
                body: formData
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.authManager.logout();
                    throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
                }
                
                // Try to get error details from response
                let errorMessage = 'Ошибка при отправке голосового сообщения';
                let errorDetails = null;
                try {
                    const errorData = await response.json();
                    console.error('Server error response:', errorData);
                    if (errorData.detail) {
                        errorMessage = errorData.detail;
                    }
                    errorDetails = errorData;
                } catch (e) {
                    // If we can't parse JSON, use status text
                    errorMessage = response.statusText || errorMessage;
                    console.error('Could not parse error response:', e);
                }
                
                const error = new Error(errorMessage);
                error.status = response.status;
                error.details = errorDetails;
                throw error;
            }

            const data = await response.json();
            this.currentConversationId = data.conversation_id;

            // Hide typing indicator and add AI response
            this.hideTypingIndicator();

            // Add user voice message (transcribed text)
            this.addVoiceMessageToChat('user', 'Голосовое сообщение', null);

            // Add AI response
            if (data.audio_url) {
                this.addVoiceMessageToChat('assistant', data.response, data.audio_url);
            } else {
                this.addMessageToChat('assistant', data.response);
            }

            // Update conversations list
            this.loadConversations();

        } catch (error) {
            console.error('Voice message error:', error);
            console.error('Error details:', {
                message: error.message,
                status: error.status,
                response: error.response
            });
            this.hideTypingIndicator();
            
            // Show more detailed error message
            let errorMessage = 'Извините, произошла ошибка при обработке голосового сообщения. Попробуйте еще раз.';
            if (error.message) {
                errorMessage += ` Детали: ${error.message}`;
            }
            this.addMessageToChat('assistant', errorMessage);
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    addVoiceMessageToChat(role, content, audioUrl) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role} voice fade-in`;

        // Добавляем аватар только для ассистента
        if (role === 'assistant') {
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = '';
            messageDiv.appendChild(avatar);
        }

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';

        // Add transcribed text
        if (role === 'assistant') {
            bubble.innerHTML = this.convertMarkdownToHtml(content);
        } else {
            // For user voice messages, show audio visualization instead of text
            if (role === 'user') {
                const audioVisualization = this.createAudioVisualization();
                bubble.appendChild(audioVisualization);
            } else {
                bubble.textContent = content;
            }
        }

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageContent.appendChild(bubble);
        messageContent.appendChild(time);
        
        // Add action buttons for assistant messages
        if (role === 'assistant') {
            const copyText = document.createElement('span');
            copyText.className = 'action-text copy-text';
            copyText.textContent = 'Копировать';
            copyText.style.cursor = 'pointer';
            copyText.addEventListener('click', (e) => {
                e.stopPropagation();
                this.copyMessage(messageDiv);
            });
            time.appendChild(copyText);
            
            const voiceText = document.createElement('span');
            voiceText.className = 'action-text voice-text';
            voiceText.textContent = 'Озвучить';
            voiceText.style.cursor = 'pointer';
            voiceText.addEventListener('click', (e) => {
                e.stopPropagation();
                this.speakMessage(messageDiv);
            });
            time.appendChild(voiceText);
        }
        
        messageDiv.appendChild(messageContent);

        this.chatMessages.appendChild(messageDiv);
        setTimeout(() => this.scrollToBottom(), 50);
    }

    createAudioVisualization() {
        const container = document.createElement('div');
        container.className = 'audio-visualization';
        
        // Create waveform container
        const waveformContainer = document.createElement('div');
        waveformContainer.className = 'waveform-container';
        
        // Generate random waveform data for visualization
        const waveformData = this.generateWaveformData();
        
        // Create SVG for the waveform
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', '0 0 300 60');
        svg.setAttribute('class', 'waveform-svg');
        
        // Create waveform path
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', this.createWaveformPath(waveformData));
        path.setAttribute('class', 'waveform-path');
        
        svg.appendChild(path);
        waveformContainer.appendChild(svg);
        
        // Add duration only
        const audioInfo = document.createElement('div');
        audioInfo.className = 'audio-info';
        
        const duration = document.createElement('span');
        duration.className = 'audio-duration';
        duration.textContent = this.formatDuration(this.getRandomDuration());
        
        audioInfo.appendChild(duration);
        
        container.appendChild(waveformContainer);
        container.appendChild(audioInfo);
        
        // Add click to play functionality
        container.style.cursor = 'pointer';
        container.addEventListener('click', () => {
            // Add a subtle animation when clicked
            container.style.transform = 'scale(0.98)';
            setTimeout(() => {
                container.style.transform = 'scale(1)';
            }, 150);
        });
        
        return container;
    }

    generateWaveformData() {
        const data = [];
        const numBars = 60;
        
        for (let i = 0; i < numBars; i++) {
            // Create more realistic audio waveform with multiple frequency components
            const t = i / numBars;
            const baseHeight = 0.2 + Math.random() * 0.3;
            
            // Add multiple sine waves for more realistic audio pattern
            const wave1 = Math.sin(t * Math.PI * 8) * 0.15;
            const wave2 = Math.sin(t * Math.PI * 16) * 0.1;
            const wave3 = Math.sin(t * Math.PI * 4) * 0.2;
            const noise = (Math.random() - 0.5) * 0.1;
            
            const height = Math.max(0.05, Math.min(1, baseHeight + wave1 + wave2 + wave3 + noise));
            data.push(height);
        }
        
        return data;
    }

    createWaveformPath(data) {
        const width = 300;
        const height = 60;
        const barWidth = width / data.length;
        
        let path = '';
        
        for (let i = 0; i < data.length; i++) {
            const x = i * barWidth + barWidth / 2;
            const barHeight = data[i] * height * 0.8;
            const y1 = (height - barHeight) / 2;
            const y2 = y1 + barHeight;
            
            if (i === 0) {
                path += `M ${x} ${y1}`;
            } else {
                path += ` L ${x} ${y1}`;
            }
        }
        
        // Create the bottom part of the waveform
        for (let i = data.length - 1; i >= 0; i--) {
            const x = i * barWidth + barWidth / 2;
            const barHeight = data[i] * height * 0.8;
            const y1 = (height - barHeight) / 2;
            const y2 = y1 + barHeight;
            
            path += ` L ${x} ${y2}`;
        }
        
        path += ' Z';
        return path;
    }

    getRandomDuration() {
        // Generate random duration between 2-15 seconds
        return Math.floor(Math.random() * 13) + 2;
    }

    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    playAudio(audioUrl, playBtn) {
        const audio = new Audio(audioUrl);

        if (playBtn.classList.contains('playing')) {
            audio.pause();
            playBtn.classList.remove('playing');
            playBtn.innerHTML = '▶️';
        } else {
            audio.play();
            playBtn.classList.add('playing');
            playBtn.innerHTML = '⏸️';

            audio.onended = () => {
                playBtn.classList.remove('playing');
                playBtn.innerHTML = '▶️';
            };
        }
    }

    // Document upload methods
    async uploadDocument(file) {
        // Validate file type
        const allowedTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/plain',
            'text/csv',
            'application/rtf'
        ];

        if (!allowedTypes.includes(file.type)) {
            showNotification('Неподдерживаемый тип файла. Поддерживаются: PDF, DOCX, DOC, TXT, CSV, RTF', 'error');
            return;
        }

        // Validate file size (10MB)
        if (file.size > 10 * 1024 * 1024) {
            showNotification('Файл слишком большой. Максимальный размер: 10MB', 'error');
            return;
        }

        this.isLoading = true;
        this.showLoading();
        this.showDocumentUploadIndicator();
        this.updateDocumentButton(true);

        // Hide welcome message if it's showing
        this.hideWelcomeMessage();
        this.showChatMessages();

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('conversation_id', this.currentConversationId || '');
            formData.append('model', this.currentModel);

            const response = await fetch('/api/documents/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authManager.token}`
                },
                body: formData
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.authManager.logout();
                    throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
                }
                throw new Error('Ошибка при загрузке документа');
            }

            const data = await response.json();
            this.currentConversationId = data.conversation_id;

            // Hide indicators and add responses
            this.hideTypingIndicator();
            this.hideDocumentUploadIndicator();

            // Add user document message
            this.addDocumentMessageToChat('user', data.document_name, data.document_id);

            // Add AI response
            this.addMessageToChat('assistant', data.response);

            // Update conversations list
            this.loadConversations();

            showNotification(`Документ "${data.document_name}" успешно загружен и обработан`, 'success');

        } catch (error) {
            console.error('Error:', error);
            this.hideTypingIndicator();
            this.hideDocumentUploadIndicator();
            this.addMessageToChat('assistant', 'Извините, произошла ошибка при обработке документа. Попробуйте еще раз.');
            showNotification(error.message, 'error');
        } finally {
            this.isLoading = false;
            this.hideLoading();
            this.updateDocumentButton(false);
            // Clear file input
            this.documentInput.value = '';
        }
    }

    showDocumentUploadIndicator() {
        if (this.documentUploadIndicator) {
            this.documentUploadIndicator.classList.remove('hidden');
            setTimeout(() => this.scrollToBottom(), 100);
        }
    }

    hideDocumentUploadIndicator() {
        if (this.documentUploadIndicator) {
            this.documentUploadIndicator.classList.add('hidden');
        }
    }

    updateDocumentButton(uploading) {
        if (this.documentBtn) {
            if (uploading) {
                this.documentBtn.classList.add('uploading');
                this.documentBtn.disabled = true;
            } else {
                this.documentBtn.classList.remove('uploading');
                this.documentBtn.disabled = false;
            }
        }
    }

    addDocumentMessageToChat(role, documentName, documentId) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role} document fade-in`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';

        // Add document info
        const documentInfo = document.createElement('div');
        documentInfo.className = 'document-info';

        const documentIcon = document.createElement('div');
        documentIcon.className = 'document-icon';
        documentIcon.textContent = '📄';

        const documentDetails = document.createElement('div');
        documentDetails.className = 'document-details';

        const documentNameEl = document.createElement('div');
        documentNameEl.className = 'document-name';
        documentNameEl.textContent = documentName;

        const documentMeta = document.createElement('div');
        documentMeta.className = 'document-meta';
        documentMeta.textContent = 'Документ загружен';

        documentDetails.appendChild(documentNameEl);
        documentDetails.appendChild(documentMeta);

        const documentActions = document.createElement('div');
        documentActions.className = 'document-actions';

        const viewBtn = document.createElement('button');
        viewBtn.className = 'document-action-btn';
        viewBtn.innerHTML = '👁️';
        viewBtn.title = 'Просмотреть документ';
        viewBtn.addEventListener('click', () => this.viewDocument(documentId));

        documentActions.appendChild(viewBtn);

        documentInfo.appendChild(documentIcon);
        documentInfo.appendChild(documentDetails);
        documentInfo.appendChild(documentActions);

        bubble.appendChild(documentInfo);

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageContent.appendChild(bubble);
        messageContent.appendChild(time);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);

        this.chatMessages.appendChild(messageDiv);
        setTimeout(() => this.scrollToBottom(), 50);
    }

    viewDocument(documentId) {
        // Open document in new tab
        window.open(`/api/documents/${documentId}`, '_blank');
    }


    // Connect Modal Functions
    showConnectModal() {
        if (this.connectModal) {
            this.connectModal.classList.remove('hidden');
            this.connectionUsernameInput.focus();
            this.resetConnectModal();
        }
    }

    hideConnectModal() {
        if (this.connectModal) {
            this.connectModal.classList.add('hidden');
            this.resetConnectModal();
        }
    }

    toggleToolsDropdown() {
        if (this.toolsDropdown) {
            this.toolsDropdown.classList.toggle('show');
        }
    }

    hideToolsDropdown() {
        if (this.toolsDropdown) {
            this.toolsDropdown.classList.remove('show');
        }
    }

    resetConnectModal() {
        if (this.connectionUsernameInput) {
            this.connectionUsernameInput.value = 'admin';
        }
        if (this.connectionPasswordInput) {
            this.connectionPasswordInput.value = 'admin123';
        }
        if (this.connectBtnModal) {
            this.connectBtnModal.disabled = false;
        }
        if (this.connectionStatus) {
            this.connectionStatus.style.display = 'none';
        }
        if (this.connectionResult) {
            this.connectionResult.style.display = 'none';
        }
    }


    async testConnection() {
        const username = document.getElementById('connection-username').value.trim();
        const password = document.getElementById('connection-password').value.trim();
        
        if (!username || !password) {
            this.showConnectionResult('error', 'Пожалуйста, введите имя пользователя и пароль');
            return;
        }

        // Показываем статус загрузки
        if (this.connectionStatus) {
            this.connectionStatus.style.display = 'block';
        }
        if (this.connectionResult) {
            this.connectionResult.style.display = 'none';
        }

        try {
            // Test cloud API connection
            const cloudApi = new WindexsCloudAPI({username, password}, 'http://localhost:8080/api');
            const result = await cloudApi.testConnection();

            // Скрываем статус загрузки
            if (this.connectionStatus) {
                this.connectionStatus.style.display = 'none';
            }

            // Показываем результат
            if (this.connectionResult) {
                this.connectionResult.style.display = 'block';

                if (result.success) {
                    this.connectionResult.innerHTML = `
                        <div class="alert alert-success">
                            <div class="d-flex align-items-center">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="me-2">
                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                                    <polyline points="22,4 12,14.01 9,11.01"></polyline>
                                </svg>
                                <div>
                                    <strong>Подключение к облаку успешно!</strong><br>
                                    <small>${result.message || 'Облачный сервис доступен для подключения'}</small>
                                </div>
                            </div>
                        </div>
                    `;

                    if (this.connectBtnModal) {
                        this.connectBtnModal.disabled = false;
                    }
                } else {
                    this.connectionResult.innerHTML = `
                        <div class="alert alert-danger">
                            <div class="d-flex align-items-center">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="me-2">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <line x1="15" y1="9" x2="9" y2="15"></line>
                                    <line x1="9" y1="9" x2="15" y2="15"></line>
                                </svg>
                                <div>
                                    <strong>Ошибка подключения</strong><br>
                                    <small>${result.message || 'Неверный код подключения'}</small>
                                </div>
                            </div>
                        </div>
                    `;
                }
            }

        } catch (error) {
            console.error('Connection test error:', error);

            // Скрываем статус загрузки
            if (this.connectionStatus) {
                this.connectionStatus.style.display = 'none';
            }

            // Показываем ошибку
            if (this.connectionResult) {
                this.connectionResult.style.display = 'block';
                this.connectionResult.innerHTML = `
                    <div class="alert alert-danger">
                        <div class="d-flex align-items-center">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="me-2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="15" y1="9" x2="9" y2="15"></line>
                                <line x1="9" y1="9" x2="15" y2="15"></line>
                            </svg>
                            <div>
                                <strong>Ошибка сети</strong><br>
                                <small>Не удалось проверить подключение</small>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
    }

    async connectToChat() {
        const username = document.getElementById('connection-username').value.trim();
        const password = document.getElementById('connection-password').value.trim();
        
        if (!username || !password) {
            this.showConnectionResult('error', 'Пожалуйста, введите имя пользователя и пароль');
            return;
        }

        try {
            // Initialize cloud API with the credentials
            const cloudApi = new WindexsCloudAPI({username, password}, 'http://localhost:8080/api');
            
            // Test the connection
            const testResult = await cloudApi.testConnection();
            
            if (testResult.success) {
                // Initialize cloud file manager
                cloudManager = new CloudFileManager(cloudApi);
                await cloudManager.init();
                
                // Hide connection modal and show cloud manager
                this.hideConnectModal();
                cloudManager.show();
                
                this.addMessageToChat('assistant', `✅ Подключение к облаку установлено! Теперь вы можете управлять файлами в облаке.`);
                showNotification('Подключение к облаку установлено', 'success');
            } else {
                showNotification('Ошибка подключения к облаку: ' + testResult.message, 'error');
            }

        } catch (error) {
            console.error('Connect error:', error);
            showNotification('Ошибка подключения к облаку: ' + error.message, 'error');
        }
    }
}

// Notification system
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;

    const icon = type === 'success' ? '✓' : '✕';

    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-icon">${icon}</div>
            <div class="notification-text">${message}</div>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;

    document.body.appendChild(notification);

    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);

    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 300);
    }, 5000);
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const authManager = new AuthManager();

    // Initialize WindexAI only after authentication
    authManager.showMainApp = function() {
        document.getElementById('auth-modal').style.display = 'none';
        document.getElementById('main-app').classList.remove('hidden');
        // Initialize WindexAI after showing main app
        if (!window.windexAI) {
            window.windexAI = new WindexAI(authManager);
        }
    };

    // Auth form handlers
    const loginForm = document.getElementById('login-form-element');
    const registerForm = document.getElementById('register-form-element');
    const showRegisterLink = document.getElementById('show-register');
    const showLoginLink = document.getElementById('show-login');
    const loginFormDiv = document.getElementById('login-form');
    const registerFormDiv = document.getElementById('register-form');

    // Debug: Check if all auth elements are found

    // Show register form
    if (showRegisterLink) {
        showRegisterLink.addEventListener('click', (e) => {
        e.preventDefault();
        loginFormDiv.style.opacity = '0';
        loginFormDiv.style.transform = 'translateX(-20px)';

        setTimeout(() => {
            loginFormDiv.classList.add('hidden');
            registerFormDiv.classList.remove('hidden');
            registerFormDiv.style.opacity = '0';
            registerFormDiv.style.transform = 'translateX(20px)';

            setTimeout(() => {
                registerFormDiv.style.opacity = '1';
                registerFormDiv.style.transform = 'translateX(0)';
            }, 50);
        }, 300);
        });
    }

    // Show login form
    if (showLoginLink) {
        showLoginLink.addEventListener('click', (e) => {
        e.preventDefault();
        registerFormDiv.style.opacity = '0';
        registerFormDiv.style.transform = 'translateX(-20px)';

        setTimeout(() => {
            registerFormDiv.classList.add('hidden');
            loginFormDiv.classList.remove('hidden');
            loginFormDiv.style.opacity = '0';
            loginFormDiv.style.transform = 'translateX(20px)';

            setTimeout(() => {
                loginFormDiv.style.opacity = '1';
                loginFormDiv.style.transform = 'translateX(0)';
            }, 50);
        }, 300);
        });
    }

    // Handle login
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const submitBtn = loginForm.querySelector('button[type="submit"]');

        if (!submitBtn) {
            console.error('Submit button not found');
            return;
        }

        // Show loading state
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Вход...';

        try {
            await authManager.login(email, password);
        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            // Restore button state
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
        });
    }

    // Handle registration
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        const submitBtn = registerForm.querySelector('button[type="submit"]');

        if (!submitBtn) {
            console.error('Submit button not found');
            return;
        }

        // Show loading state
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Регистрация...';

        try {
            await authManager.register(username, email, password);
            showNotification('Регистрация успешна! Теперь войдите в систему.', 'success');
            registerFormDiv.style.opacity = '0';
            registerFormDiv.style.transform = 'translateX(-20px)';

            setTimeout(() => {
                registerFormDiv.classList.add('hidden');
                loginFormDiv.classList.remove('hidden');
                loginFormDiv.style.opacity = '0';
                loginFormDiv.style.transform = 'translateX(20px)';

                setTimeout(() => {
                    loginFormDiv.style.opacity = '1';
                    loginFormDiv.style.transform = 'translateX(0)';
                }, 50);
            }, 300);
        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            // Restore button state
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
        });
    }

    // Agreement modal handlers
    const agreementLink = document.getElementById('agreement-link');
    const agreementModal = document.getElementById('agreement-modal');
    const agreementOverlay = document.getElementById('agreement-overlay');
    const agreementClose = document.getElementById('agreement-close');

    if (agreementLink && agreementModal) {
        agreementLink.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            agreementModal.classList.remove('hidden');
        });
    }

    if (agreementOverlay) {
        agreementOverlay.addEventListener('click', () => {
            agreementModal.classList.add('hidden');
        });
    }

    if (agreementClose) {
        agreementClose.addEventListener('click', () => {
            agreementModal.classList.add('hidden');
        });
    }

    // Мобильное меню
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    
    if (mobileMenuBtn && sidebar) {
        // Открытие/закрытие мобильного меню
        mobileMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleMobileMenu();
        });
        
        // Закрытие меню при клике на overlay
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', () => {
                closeMobileMenu();
            });
        }
        
        // Закрытие меню при клике на элемент списка чатов
        const conversationItems = sidebar.querySelectorAll('.conversation-item');
        conversationItems.forEach(item => {
            item.addEventListener('click', () => {
                closeMobileMenu();
            });
        });
        
        // Закрытие меню при изменении размера окна (если переходим на десктоп)
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                closeMobileMenu();
            }
        });
    }
    
    function toggleMobileMenu() {
        if (sidebar && sidebarOverlay) {
            const isOpen = sidebar.classList.contains('mobile-open');
            if (isOpen) {
                closeMobileMenu();
            } else {
                openMobileMenu();
            }
        }
    }
    
    function openMobileMenu() {
        if (sidebar && sidebarOverlay) {
            sidebar.classList.add('mobile-open');
            sidebarOverlay.classList.add('active');
            document.body.style.overflow = 'hidden'; // Предотвращаем скролл фона
        }
    }
    
    function closeMobileMenu() {
        if (sidebar && sidebarOverlay) {
            sidebar.classList.remove('mobile-open');
            sidebarOverlay.classList.remove('active');
            document.body.style.overflow = ''; // Восстанавливаем скролл
        }
    }
    
    // Обработка свайпов для закрытия мобильного меню
    let touchStartX = 0;
    let touchEndX = 0;
    
    if (sidebar) {
        sidebar.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });
        
        sidebar.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        });
    }
    
    function handleSwipe() {
        const swipeThreshold = 50;
        const swipeDistance = touchStartX - touchEndX;
        
        // Свайп влево для закрытия меню
        if (swipeDistance > swipeThreshold && sidebar.classList.contains('mobile-open')) {
            closeMobileMenu();
        }
    }
    
    // Предотвращаем зум при двойном тапе на кнопках
    document.addEventListener('touchstart', (e) => {
        if (e.target.closest('.btn, .nav-link, .conversation-item, .model-card, .specialist-card, .action-btn, .send-btn')) {
            e.preventDefault();
        }
    }, { passive: false });

    
    // Улучшенная обработка клавиатуры на мобильных
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.addEventListener('focus', () => {
            // Небольшая задержка для корректного позиционирования
            setTimeout(() => {
                messageInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 300);
        });
    }
});

// Add some utility functions
function formatDate(date) {
    return new Intl.DateTimeFormat('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

function truncateText(text, maxLength = 50) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}



function formatDate(date) {
    return new Intl.DateTimeFormat('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

function truncateText(text, maxLength = 50) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}



// Функция для копирования кода в буфер обмена
function copyCodeToClipboard(button) {
    const codeBlock = button.closest('.code-block');
    const codeElement = codeBlock.querySelector('code');
    const codeText = codeElement.textContent;

    navigator.clipboard.writeText(codeText).then(() => {
        // Показываем успешное копирование
        const originalText = button.textContent;
        button.textContent = '✅ Скопировано';
        button.classList.add('copied');

        // Возвращаем исходный текст через 2 секунды
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Ошибка копирования:', err);
        button.textContent = '❌ Ошибка';
        setTimeout(() => {
            button.textContent = '📋 Копировать';
        }, 2000);
    });
}

// Функция для прокрутки карточек специалистов
function scrollSpecialists(direction) {
    const grid = document.getElementById('specialistsGrid');
    if (!grid) return;

    const scrollAmount = 300; // Количество пикселей для прокрутки
    const currentScroll = grid.scrollLeft;

    if (direction === 'left') {
        grid.scrollTo({
            left: currentScroll - scrollAmount,
            behavior: 'smooth'
        });
    } else if (direction === 'right') {
        grid.scrollTo({
            left: currentScroll + scrollAmount,
            behavior: 'smooth'
        });
    }
}

// Обновление видимости кнопок прокрутки
function updateScrollButtons() {
    const grid = document.getElementById('specialistsGrid');
    const leftBtn = document.querySelector('.scroll-left');
    const rightBtn = document.querySelector('.scroll-right');

    if (!grid || !leftBtn || !rightBtn) return;

    const isScrollable = grid.scrollWidth > grid.clientWidth;
    const isAtStart = grid.scrollLeft <= 0;
    const isAtEnd = grid.scrollLeft >= (grid.scrollWidth - grid.clientWidth);

    // Показываем/скрываем кнопки в зависимости от возможности прокрутки
    leftBtn.style.display = isScrollable ? 'flex' : 'none';
    rightBtn.style.display = isScrollable ? 'flex' : 'none';

    // Отключаем кнопки в крайних позициях
    leftBtn.disabled = isAtStart;
    rightBtn.disabled = isAtEnd;

    // Добавляем/убираем классы для стилизации
    leftBtn.classList.toggle('disabled', isAtStart);
    rightBtn.classList.toggle('disabled', isAtEnd);
}

// Инициализация прокрутки при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const grid = document.getElementById('specialistsGrid');
    if (grid) {
        // Обновляем кнопки при загрузке
        updateScrollButtons();

        // Обновляем кнопки при прокрутке
        grid.addEventListener('scroll', updateScrollButtons);

        // Обновляем кнопки при изменении размера окна
        window.addEventListener('resize', updateScrollButtons);
    }

    // Обработчик клика по карточке Pro модели - удалён, теперь доступ проверяется через selectModel
    // const proModelCard = document.querySelector('.pro-model');
    // if (proModelCard) {
    //     proModelCard.addEventListener('click', function(e) {
    //         e.preventDefault();
    //         window.location.href = '/pricing';
    //     });
    // }
});

// Pro Subscription Modal Functions
function showProSubscriptionModal() {
    // Создаем модальное окно для Pro подписки
    const modal = document.createElement('div');
    modal.id = 'pro-subscription-modal';
    modal.className = 'connect-modal';
    modal.innerHTML = `
        <div class="pro-modal-overlay">
            <div class="pro-modal-content">
                <div class="pro-modal-header">
                    <h2 class="pro-modal-title">🚀 WindexAI Pro</h2>
                    <button class="close-pro-modal" title="Закрыть">×</button>
                </div>
                <div class="pro-modal-body">
                    <p class="pro-modal-subtitle">Для использования WindexAI Pro требуется активная подписка:</p>

                    <div class="pro-features-list">
                        <div class="pro-feature-item">
                            <span class="pro-feature-check">✅</span>
                            <span class="pro-feature-text">Расширенные возможности</span>
                        </div>
                        <div class="pro-feature-item">
                            <span class="pro-feature-check">✅</span>
                            <span class="pro-feature-text">Безлимитные запросы</span>
                        </div>
                        <div class="pro-feature-item">
                            <span class="pro-feature-check">✅</span>
                            <span class="pro-feature-text">Приоритетная поддержка</span>
                        </div>
                        <div class="pro-feature-item">
                            <span class="pro-feature-check">✅</span>
                            <span class="pro-feature-text">Голосовые сообщения</span>
                        </div>
                        <div class="pro-feature-item">
                            <span class="pro-feature-check">✅</span>
                            <span class="pro-feature-text">Обработка документов</span>
                        </div>
                    </div>

                    <div class="pro-modal-actions">
                        <button id="upgrade-to-pro-btn" class="pro-upgrade-btn">Перейти к тарифам</button>
                        <button id="use-lite-model-btn" class="pro-lite-btn">Использовать Lite</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Обработчики событий
    modal.querySelector('.close-pro-modal').addEventListener('click', () => {
        hideProSubscriptionModal();
    });

    modal.querySelector('#upgrade-to-pro-btn').addEventListener('click', () => {
        window.location.href = '/pricing';
    });

    modal.querySelector('#use-lite-model-btn').addEventListener('click', () => {
        // Выбираем Lite модель
        if (window.chatApp && window.chatApp.selectModel) {
            window.chatApp.selectModel('gpt-4o-mini');
        }
        hideProSubscriptionModal();
    });

    // Показываем модальное окно
    modal.classList.remove('hidden');
}

function hideProSubscriptionModal() {
    const modal = document.getElementById('pro-subscription-modal');
    if (modal) {
        modal.remove();
    }
}

async function checkProSubscription() {
    try {
        const token = localStorage.getItem('windexai_token');
        if (!token) {
            return false;
        }

        const response = await fetch('/api/auth/subscription-status', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const status = await response.json();
            return status.plan === 'pro' && status.is_active;
        }

        return false;
    } catch (error) {
        console.error('Ошибка проверки подписки:', error);
        return false;
    }
}
// Global functions for HTML onclick handlers
function handleDocument() {
    // Get the document input element directly from DOM
    const documentInput = document.getElementById('document-input');
    if (documentInput) {
        documentInput.click();
    } else {
        console.error('Document input element not found');
    }
}

function handleVoice() {
    if (window.windexAI) {
        window.windexAI.toggleVoiceRecording();
    }
}

function handleConnect() {
    if (window.windexAI) {
        window.windexAI.showConnectModal();
    } else {
        showNotification('Сначала подключитесь к облаку', 'error');
    }
}

function openCloudManager() {
    if (cloudManager) {
        cloudManager.show();
    } else {
        showNotification('Сначала подключитесь к облаку', 'error');
    }
}

// Force cache refresh 1760126317
