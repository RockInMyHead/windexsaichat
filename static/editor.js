class AIEditor {
    constructor() {
        this.conversationHistory = [];
        this.currentGeneration = null;
        this.currentConversationId = null;
        this.authToken = localStorage.getItem('windexai_token');
        this.currentMode = 'lite'; // Default to Lite mode
        this.useTwoStage = true; // Default to two-stage LLM system
        this.thinkingStep = 0;
        this.thinkingInterval = null;
        this.thinkingPollingInterval = null;
        this.hasGeneratedContent = false;
        console.log('🎯 Initial mode set to:', this.currentMode);
        console.log('🎯 Two-stage LLM system enabled:', this.useTwoStage);
        this.initializeElements();
        this.setupEventListeners();
        this.toggleSendButton(); // Инициализируем состояние кнопки

        // Принудительно включаем кнопку для тестирования
        if (this.sendBtn) {
            this.sendBtn.disabled = false;
            console.log('Send button force enabled');
        }

        this.checkAuth();
        this.loadConversations();
        
        // Clear iframe on page load
        this.clearIframe();
        
        // Test iframe functionality
        this.testIframe();
        this.checkUrlParams();
        
        // Restore project content if there's an active conversation
        setTimeout(() => {
            this.restoreProjectContent();
        }, 1000);
    }
    
    clearIframe() {
        if (this.previewIframe) {
            console.log('🧹 Clearing iframe content...');
            this.previewIframe.srcdoc = `
                <!DOCTYPE html>
                <html lang='ru'>
                <head>
                    <meta charset='UTF-8'>
                    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
                    <title>Превью сайта</title>
                    <style>
                        body {
                            margin: 0;
                            padding: 20px;
                            font-family: 'Inter', sans-serif;
                            background: #f8f9fa;
                            color: #333;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100vh;
                            text-align: center;
                        }
                        .placeholder {
                            background: white;
                            padding: 2rem;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                            max-width: 400px;
                        }
                        .placeholder-icon {
                            font-size: 3rem;
                            margin-bottom: 1rem;
                        }
                        .placeholder-title {
                            font-size: 1.5rem;
                            font-weight: 600;
                            margin-bottom: 0.5rem;
                            color: #667eea;
                        }
                        .placeholder-desc {
                            color: #666;
                            line-height: 1.5;
                        }
                    </style>
                </head>
                <body>
                    <div class='placeholder'>
                        <div class='placeholder-icon'>🚀</div>
                        <div class='placeholder-title'>Готов к созданию</div>
                        <div class='placeholder-desc'>
                            Отправьте запрос в чат, чтобы начать создание сайта
                        </div>
                    </div>
                </body>
                </html>
            `;
        }
    }
    
    restoreProjectContent() {
        if (this.currentConversationId && this.previewIframe) {
            console.log('🔄 Restoring project content for conversation:', this.currentConversationId);
            
            // Проверяем, есть ли уже сгенерированный HTML
            if (this.hasGeneratedContent && this.lastGeneratedHtml) {
                console.log('✅ Already has generated content, skipping restore');
                return;
            }
            
            // Получаем последнее сообщение из истории беседы
            if (this.conversationHistory.length > 0) {
                const lastMessage = this.conversationHistory[this.conversationHistory.length - 1];
                if (lastMessage.role === 'assistant' && lastMessage.content) {
                    console.log('🔄 Restoring from conversation history...');
                    // Обновляем превью с последним сгенерированным контентом
                    this.updatePreview(lastMessage.content);
                }
            }
        }
    }
    
    forceRestoreContent() {
        // Принудительно восстанавливаем сгенерированный контент
        if (this.lastGeneratedHtml && this.previewIframe) {
            console.log('🔄 Force restoring generated content...');
            this.previewIframe.srcdoc = this.lastGeneratedHtml;
            // Скрываем кнопку восстановления после успешного восстановления
            if (this.restoreContentBtn) {
                this.restoreContentBtn.style.display = 'none';
            }
        }
    }
    
    showRestoreButton() {
        // Показываем кнопку восстановления
        if (this.restoreContentBtn && this.lastGeneratedHtml) {
            this.restoreContentBtn.style.display = 'inline-block';
        }
    }
    
    hideRestoreButton() {
        // Скрываем кнопку восстановления
        if (this.restoreContentBtn) {
            this.restoreContentBtn.style.display = 'none';
        }
    }
    
    testIframe() {
        // Проверяем, есть ли уже сгенерированный контент
        if (this.previewIframe && !this.currentConversationId && !this.previewIframe.srcdoc) {
            console.log('🧪 Testing iframe functionality...');
            var testHtml = `
                <!DOCTYPE html>
                <html>
                <head><title>Test</title></head>
                <body>
                    <h1>Iframe Test</h1>
                    <p>If you can see this, the iframe is working!</p>
                </body>
                </html>
            `;
            this.previewIframe.srcdoc = testHtml;
            console.log('🧪 Test HTML set in iframe');
            
            // Убираем тестовый контент через 3 секунды, только если нет активного проекта
            setTimeout(() => {
                if (this.previewIframe && this.previewIframe.srcdoc === testHtml && !this.currentConversationId && !this.lastGeneratedHtml) {
                    this.previewIframe.srcdoc = `
                        <!DOCTYPE html>
                        <html lang='ru'>
                        <head>
                            <meta charset='UTF-8'>
                            <meta name='viewport' content='width=device-width, initial-scale=1.0'>
                            <title>WindexsAI - Искусственный интеллект нового поколения</title>
                            <style>
                                body {
                                    margin: 0;
                                    font-family: 'Inter', sans-serif;
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    color: white;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    height: 100vh;
                                    text-align: center;
                                }
                                .container {
                                    max-width: 600px;
                                    padding: 2rem;
                                }
                                .logo {
                                    font-size: 3rem;
                                    font-weight: 700;
                                    margin-bottom: 1rem;
                                    background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
                                    -webkit-background-clip: text;
                                    -webkit-text-fill-color: transparent;
                                    background-clip: text;
                                }
                                .subtitle {
                                    font-size: 1.2rem;
                                    margin-bottom: 2rem;
                                    opacity: 0.9;
                                }
                                .description {
                                    font-size: 1rem;
                                    line-height: 1.6;
                                    opacity: 0.8;
                                    margin-bottom: 2rem;
                                }
                                .features {
                                    display: grid;
                                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                                    gap: 1rem;
                                    margin-top: 2rem;
                                }
                                .feature {
                                    background: rgba(255, 255, 255, 0.1);
                                    padding: 1rem;
                                    border-radius: 10px;
                                    backdrop-filter: blur(10px);
                                }
                                .feature-icon {
                                    font-size: 2rem;
                                    margin-bottom: 0.5rem;
                                }
                                .feature-title {
                                    font-weight: 600;
                                    margin-bottom: 0.5rem;
                                }
                                .feature-desc {
                                    font-size: 0.9rem;
                                    opacity: 0.8;
                                }
                            </style>
                        </head>
                        <body>
                            <div class='container'>
                                <div class='logo'>WindexsAI</div>
                                <div class='subtitle'>Искусственный интеллект нового поколения</div>
                                <div class='description'>
                                    Добро пожаловать в будущее AI-технологий. Создавайте сайты, анализируйте данные, 
                                    генерируйте контент и решайте сложные задачи с помощью передового искусственного интеллекта.
                                </div>
                                <div class='features'>
                                    <div class='feature'>
                                        <div class='feature-icon'>🌐</div>
                                        <div class='feature-title'>Создание сайтов</div>
                                        <div class='feature-desc'>Генерируйте современные веб-сайты с помощью AI</div>
                                    </div>
                                    <div class='feature'>
                                        <div class='feature-icon'>💬</div>
                                        <div class='feature-title'>Умный чат</div>
                                        <div class='feature-desc'>Общайтесь с AI-ассистентами разных специализаций</div>
                                    </div>
                                    <div class='feature'>
                                        <div class='feature-icon'>📊</div>
                                        <div class='feature-title'>Анализ данных</div>
                                        <div class='feature-desc'>Обрабатывайте и анализируйте информацию</div>
                                    </div>
                                </div>
                            </div>
                        </body>
                        </html>
                    `;
                    console.log('🧪 Test content removed, showing WindexsAI default message');
                }
            }, 3000);
        } else {
            console.log('❌ Preview iframe not found!');
        }
    }
    
    // Manual test function for debugging
    testHtmlExtraction() {
        var testContent = `Create a blog HTML_START \`\`\`html
<!DOCTYPE html>
<html>
<head><title>Test Blog</title></head>
<body><h1>Test Blog</h1></body>
</html>
\`\`\` HTML_END`;
        
        console.log('🧪 Testing HTML extraction...');
        console.log('🧪 Test content:', testContent);
        
        var htmlMatch = testContent.match(/HTML_START\s*`{0,3}html\s*([\s\S]*?)\s*`{0,3}\s*HTML_END/);
        console.log('🧪 HTML match result:', htmlMatch);
        
        if (htmlMatch && htmlMatch[1]) {
            var html = htmlMatch[1].trim();
            console.log('🧪 Extracted HTML:', html);
            if (this.previewIframe) {
                this.previewIframe.srcdoc = html;
                console.log('🧪 HTML set in iframe');
            }
        } else {
            console.log('🧪 HTML extraction failed');
        }
    }
    
    tryExtractHtmlFromAnyFormat(content) {
        console.log('🔍 Trying to extract HTML from any format...');
        
        // Различные паттерны для поиска HTML
        var patterns = [
            // Стандартные маркеры
            /HTML_START\s*`{0,3}html\s*([\s\S]*?)\s*`{0,3}\s*HTML_END/,
            /HTML_START\s*```html\s*([\s\S]*?)\s*```\s*HTML_END/,
            /HTML_START\s*```\s*([\s\S]*?)\s*```\s*HTML_END/,
            /HTML_START\s*([\s\S]*?)\s*HTML_END/,
            
            // Обычные code blocks
            /```html\s*([\s\S]*?)\s*```/,
            /```\s*([\s\S]*?)\s*```/,
            
            // Поиск HTML тегов напрямую
            /<!DOCTYPE html>[\s\S]*?<\/html>/i,
            /<html[\s\S]*?<\/html>/i,
            
            // Поиск HTML без DOCTYPE
            /<html[\s\S]*?<\/html>/i
        ];
        
        for (var i = 0; i < patterns.length; i++) {
            var match = content.match(patterns[i]);
            if (match && match[1]) {
                var html = match[1].trim();
                // Проверяем, что это действительно HTML
                if (html.includes('<html') || html.includes('<!DOCTYPE')) {
                    console.log('✅ HTML найден с паттерном', i, 'длина:', html.length);
                    console.log('✅ Первые 200 символов:', html.substring(0, 200));
                    return html;
                }
            }
        }
        
        console.log('❌ HTML не найден ни одним паттерном');
        return null;
    }

    initializeElements() {
        // Получаем элементы DOM
        this.chatInput = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-chat-btn');
        this.chatMessages = document.getElementById('chat-messages');
        
        // Mode selector elements
        this.liteModeBtn = document.getElementById('lite-mode-btn');
        this.proModeBtn = document.getElementById('pro-mode-btn');
        this.twoStageToggle = document.getElementById('two-stage-toggle');

        // Отладочная информация
        console.log('Editor elements initialized:', {
            chatInput: !!this.chatInput,
            sendBtn: !!this.sendBtn,
            chatMessages: !!this.chatMessages
        });
        this.previewIframe = document.getElementById('preview');
        if (this.previewIframe) {
            console.log('✅ Preview iframe found');
            
            // Добавляем обработчик для восстановления контента при кликах
            this.previewIframe.addEventListener('load', () => {
                console.log('🔄 Iframe loaded, checking content...');
                // Если iframe загрузился с дефолтным контентом, но у нас есть сгенерированный контент
                if (this.lastGeneratedHtml && this.previewIframe.srcdoc && this.previewIframe.srcdoc.includes('WindexsAI')) {
                    console.log('🔄 Showing restore button...');
                    this.showRestoreButton();
                } else if (this.lastGeneratedHtml && this.previewIframe.srcdoc && !this.previewIframe.srcdoc.includes('WindexsAI')) {
                    // Контент восстановлен, скрываем кнопку
                    this.hideRestoreButton();
                }
            });
            
            // Предотвращаем навигацию в iframe, которая может привести к потере контента
            this.previewIframe.addEventListener('beforeunload', (e) => {
                console.log('🔄 Iframe beforeunload event');
                // Если у нас есть сгенерированный контент, предотвращаем навигацию
                if (this.lastGeneratedHtml) {
                    e.preventDefault();
                    e.returnValue = '';
                    return '';
                }
            });
        } else {
            console.log('❌ Preview iframe not found');
        }
        this.typingIndicator = document.getElementById('typing-indicator');
        this.errorContainer = document.getElementById('error-container');
        this.statusText = document.getElementById('status-text');
        this.copyBtn = document.getElementById('copy-html-btn');
        this.downloadBtn = document.getElementById('download-html-btn');
        this.deployBtn = document.getElementById('deploy-btn');
        this.editModeBtn = document.getElementById('edit-mode-btn');
        this.restoreContentBtn = document.getElementById('restore-content-btn');
        this.userNameSpan = document.getElementById('user-name');
        this.userAvatar = document.getElementById('user-avatar');
        this.userName = document.getElementById('user-name');
        this.profileModal = document.getElementById('profile-modal');
        this.closeProfileBtn = document.querySelector('.close-profile');

        // History elements
        this.conversationsList = document.getElementById('conversations-list');
        this.newProjectBtn = document.getElementById('new-project-btn');

        // Edit mode state
        this.editMode = false;
        this.selectedElement = null;
        this.editableElements = [];

        // Resizable panels state
        this.panelDivider = document.getElementById('panel-divider');
        this.chatPanel = document.querySelector('.chat-panel');
        this.previewPanel = document.querySelector('.preview-panel');
        this.isDragging = false;
        this.startX = 0;
        this.startChatWidth = 0;
        this.containerWidth = 0;

        // Отладочная информация
        console.log('AIEditor initialized:', {
            chatInput: !!this.chatInput,
            sendBtn: !!this.sendBtn,
            chatMessages: !!this.chatMessages
        });

        // Bind methods for event listeners
        this.boundOnDrag = this.onDrag.bind(this);
        this.boundStopDrag = this.stopDrag.bind(this);

        // Modal elements
        this.deployModal = document.getElementById('deploy-modal');
        this.deployTitle = document.getElementById('deploy-title');
        this.deployDescription = document.getElementById('deploy-description');
        this.deployStatus = document.getElementById('deploy-status');
        this.deployActions = document.getElementById('deploy-actions');
        this.viewSiteBtn = document.getElementById('view-site-btn');
        this.copyUrlBtn = document.getElementById('copy-url-btn');
        this.confirmDeployBtn = document.getElementById('confirm-deploy');
        this.cancelDeployBtn = document.getElementById('cancel-deploy');
        this.closeModalBtn = document.querySelector('.close');
        this.projectsBtn = document.getElementById('projects-btn');
        this.dashboardBtn = document.getElementById('dashboard-btn');

        // Store deployment result
        this.lastDeploymentResult = null;

    }

    setupEventListeners() {
        // Обработчик отправки
        console.log('Setting up event listeners, sendBtn:', this.sendBtn);
        if (this.sendBtn) {
            console.log('Setting up send button event listener');
            this.sendBtn.addEventListener('click', () => {
                console.log('Send button clicked');
                this.sendMessage();
            });
        } else {
            console.error('Send button not found! Element ID: send-chat-btn');
        }

        // Обработчик Enter в поле ввода
        if (this.chatInput) {
            this.chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            this.chatInput.addEventListener('input', () => {
                this.autoResizeInput();
                this.toggleSendButton();
            });
        }

        // Mode selector event listeners
        if (this.liteModeBtn) {
            this.liteModeBtn.addEventListener('click', () => {
                this.setMode('lite');
            });
        }
        
        if (this.proModeBtn) {
            this.proModeBtn.addEventListener('click', () => {
                this.setMode('pro');
            });
        }
        
        // Two-stage toggle event listener
        if (this.twoStageToggle) {
            this.twoStageToggle.addEventListener('change', (e) => {
                this.useTwoStage = e.target.checked;
                console.log('🎯 Two-stage LLM system:', this.useTwoStage ? 'enabled' : 'disabled');
            });
        }

        // Кнопки копирования и скачивания
        if (this.copyBtn) {
            this.copyBtn.addEventListener('click', () => this.copyHtml());
        }

        if (this.downloadBtn) {
            this.downloadBtn.addEventListener('click', () => this.downloadHtml());
        }

        if (this.deployBtn) {
            this.deployBtn.addEventListener('click', () => this.showDeployModal());
        }

        if (this.editModeBtn) {
            this.editModeBtn.addEventListener('click', () => this.toggleEditMode());
        }

        // Resizable panels event listeners
        if (this.panelDivider) {
            this.panelDivider.addEventListener('mousedown', (e) => this.startDrag(e));
        }

        // Modal event listeners
        if (this.confirmDeployBtn) {
            this.confirmDeployBtn.addEventListener('click', () => this.deployWebsite());
        }
        if (this.cancelDeployBtn) {
            this.cancelDeployBtn.addEventListener('click', () => this.hideDeployModal());
        }
        if (this.closeModalBtn) {
            this.closeModalBtn.addEventListener('click', () => this.hideDeployModal());
        }
        if (this.viewSiteBtn) {
            this.viewSiteBtn.addEventListener('click', () => this.openDeployedSite());
        }
        if (this.copyUrlBtn) {
            this.copyUrlBtn.addEventListener('click', () => this.copyDeploymentUrl());
        }
        if (this.deployModal) {
            this.deployModal.addEventListener('click', (e) => {
                if (e.target === this.deployModal) {
                    this.hideDeployModal();
                }
            });
        }

        // Кнопка выхода

        // История чатов
        if (this.newProjectBtn) {
            this.newProjectBtn.addEventListener('click', () => this.createNewProject());
        }

        // Обработчик кнопки "Мои проекты"
        if (this.projectsBtn) {
            this.projectsBtn.addEventListener('click', () => {
                window.location.href = '/static/projects.html';
            });
        }

        // Обработчик кнопки "Личный кабинет"
        if (this.dashboardBtn) {
            this.dashboardBtn.addEventListener('click', () => {
                window.location.href = '/static/dashboard.html';
            });
        }

        // Load saved panel sizes
        this.loadPanelSizes();

        // User info click handlers - navigate to profile page
        if (this.userAvatar) {
            this.userAvatar.addEventListener('click', () => {
                this.openUserProfile();
            });
        }

        if (this.userName) {
            this.userName.addEventListener('click', () => {
                this.openUserProfile();
            });
        }
        
        // Also add click handler to the entire user-info container
        const userInfo = document.querySelector('.user-info');
        if (userInfo) {
            userInfo.addEventListener('click', () => {
                this.openUserProfile();
            });
        }

        // Close profile modal
        if (this.closeProfileBtn) {
            this.closeProfileBtn.addEventListener('click', () => {
                this.hideProfileModal();
            });
        }

        // Restore content button
        if (this.restoreContentBtn) {
            this.restoreContentBtn.addEventListener('click', () => {
                this.forceRestoreContent();
            });
        }

    }

    async checkAuth() {
        try {
            var token = localStorage.getItem('windexai_token');
            console.log('Auth token:', token ? 'present' : 'missing');
            if (!token) {
                console.log('No auth token, redirecting to home');
                window.location.href = '/';
                return;
            }

            var response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                localStorage.removeItem('windexai_token');
                window.location.href = '/';
                return;
            }

            var user = await response.json();
            if (this.userNameSpan) {
                this.userNameSpan.textContent = user.username;
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            window.location.href = '/';
        }
    }

    setMode(mode) {
        this.currentMode = mode;
        
        // Update button states
        if (this.liteModeBtn && this.proModeBtn) {
            this.liteModeBtn.classList.toggle('active', mode === 'lite');
            this.proModeBtn.classList.toggle('active', mode === 'pro');
        }
        
        // Update placeholder text based on mode
        if (this.chatInput) {
            if (mode === 'lite') {
                this.chatInput.placeholder = 'Опишите сайт для создания (один HTML файл)...';
            } else {
                this.chatInput.placeholder = 'Опишите изменения для сайта...';
            }
        }
        
        console.log('🎯 Mode changed to:', mode);
        console.log('🎯 Current mode value:', this.currentMode);
    }

    processLiteModeContent(content) {
        console.log('🚀 Обработка Lite режима - извлечение HTML...');
        console.log('🔍 Содержимое для поиска:', content.substring(0, 200) + '...');
        console.log('🔍 Preview iframe exists:', !!this.previewIframe);
        
        // Извлекаем HTML из ответа - более гибкий паттерн
        var htmlMatch = content.match(/HTML_START\s*`{0,3}html\s*([\s\S]*?)\s*`{0,3}\s*HTML_END/);
        
        console.log('🔍 Результат regex:', htmlMatch);
        
        if (htmlMatch && htmlMatch[1]) {
            var htmlContent = htmlMatch[1].trim();
            console.log('✅ HTML извлечен, длина:', htmlContent.length);
            console.log('✅ Первые 100 символов HTML:', htmlContent.substring(0, 100));
            
            // Обновляем превью с HTML контентом
            console.log('🔄 Вызываем updatePreview...');
            this.previewIframe.srcdoc = htmlContent;
            console.log('✅ HTML content set directly in iframe');
            
            // Сохраняем HTML для деплоя
            this.lastGeneratedHtml = htmlContent;
            
            // Устанавливаем флаг, что контент был сгенерирован
            this.hasGeneratedContent = true;
            
            this.updateStatus('HTML сайт создан');
        } else {
            console.log('❌ HTML не найден в ответе');
            console.log('❌ Попробуем альтернативный паттерн...');
            
            // Попробуем альтернативный паттерн
            var altMatch = content.match(/HTML_START\s*`{0,3}html\s*([\s\S]*?)\s*`{0,3}\s*HTML_END/);
            if (altMatch && altMatch[1]) {
                console.log('✅ HTML найден альтернативным паттерном');
                var htmlContent = altMatch[1].trim();
                this.previewIframe.srcdoc = htmlContent;
                this.lastGeneratedHtml = htmlContent;
                this.hasGeneratedContent = true;
                this.updateStatus('HTML сайт создан');
            } else {
                console.log('❌ Альтернативный паттерн тоже не сработал');
                this.updatePreview(content);
            }
        }
    }

    async sendMessage() {
        console.log('sendMessage called');
        var message = this.chatInput?.value?.trim();
        console.log('Message:', message);
        if (!message) {
            console.log('No message, returning');
            return;
        }


        // Проверяем, находимся ли мы в режиме редактирования
        if (this.editMode && this.selectedElement) {
            await this.editSelectedElement(message);
            this.chatInput.value = '';
            this.autoResizeInput();
            this.toggleSendButton();
            return;
        }

        // Добавляем сообщение пользователя
        this.addChatMessage('user', message);
        this.conversationHistory.push({role: 'user', content: message});

        // Очищаем поле ввода
        this.chatInput.value = '';
        this.autoResizeInput();
        this.toggleSendButton();

        // Показываем индикатор загрузки
        this.startGeneration();

        try {
            var token = localStorage.getItem('windexai_token');
            if (!token) {
                throw new Error('Токен авторизации не найден');
            }

            // Создаем AbortController для контроля таймаута
            var controller = new AbortController();
            var timeoutId = setTimeout(() => controller.abort(), 300000); // 5 минут
            
            // Replace fetch handling with streaming reader
            console.log('🚀 Sending streaming request with mode:', this.currentMode);
            var response = await fetch('/api/ai-editor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    messages: this.conversationHistory,
                    model: 'gpt-4o-mini',
                    mode: this.currentMode,
                    conversation_id: this.currentConversationId,
                    use_two_stage: this.useTwoStage
                }),
                signal: controller.signal,
                keepalive: true
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Read streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let result = '';
            console.log('🟢 Начало чтения потоковых данных');
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                console.log('🔹 Chunk from server:', chunk);
                result += chunk;
            }
            console.log('✅ Поток завершен, итоговый ответ:', result);
            // Попытаться распарсить результат как JSON, чтобы получить поля content и conversation_id
            let data;
            try {
                data = JSON.parse(result);
                console.log('🔍 Parsed JSON data:', data);
            } catch (e) {
                console.warn('⚠️ Не удалось распарсить JSON, используем текст как content');
                data = { content: result, conversation_id: null };
            }
            var content = data.content || 'Ответ получен без содержания';

            // Сохраняем conversation_id
            if (data.conversation_id) {
                this.currentConversationId = data.conversation_id;
            }

            // Добавляем ответ AI
            this.conversationHistory.push({role: 'assistant', content: content});

            // Извлекаем описание для чата
            var description = this.extractDescription(content);
            this.addChatMessage('assistant', description, data.conversation_id);
            
            // Проверяем, есть ли информация о запущенном проекте
            if (description.includes('🚀 **Проект запущен!**')) {
                this.showProjectLaunchInfo(description);
            }

        // Обрабатываем контент в зависимости от режима
        console.log('🔍 Проверяем контент:', content);
        console.log('🔍 Conversation ID:', data.conversation_id);
        console.log('🔍 Текущий режим:', this.currentMode);
        console.log('🔍 Содержит HTML_START:', content.includes('HTML_START'));
        console.log('🔍 Содержит PACKAGE_JSON_START:', content.includes('PACKAGE_JSON_START'));
        
        if (this.currentMode === 'lite' && content.includes('HTML_START')) {
            console.log('🎯 Обнаружен HTML файл (Lite режим), обрабатываем...');
            console.log('🔍 Full content for debugging:', content);
            this.processLiteModeContent(content);
        } else if (this.currentMode === 'pro' && data.conversation_id && (content.includes('PACKAGE_JSON_START') || content.includes('LAYOUT_TSX_START') || content.includes('PAGE_TSX_START'))) {
            console.log('🎯 Обнаружен Next.js проект (Pro режим), запускаем превью...');
            this.generateWebsitePreview(data.conversation_id, this.previewIframe);
        } else {
            console.log('📄 Обычный контент, используем стандартный превью');
            console.log('🔍 Content does not contain HTML_START, full content:', content);
            
            // Попробуем найти HTML в любом формате для Lite режима
            if (this.currentMode === 'lite') {
                console.log('🔍 Lite режим: пытаемся найти HTML в любом формате...');
                var htmlFound = this.tryExtractHtmlFromAnyFormat(content);
                if (htmlFound) {
                    console.log('✅ HTML найден в альтернативном формате');
                    this.previewIframe.srcdoc = htmlFound;
                    this.lastGeneratedHtml = htmlFound;
                    this.updateStatus('HTML сайт создан');
                    return;
                }
            }
            
            this.updatePreview(content);
        }

            // Обновляем список разговоров
            this.loadConversations();

            this.updateStatus('Сайт успешно создан');

        } catch (error) {
            console.error('Generation error:', error);
            if (error.name === 'AbortError') {
                this.showError('Генерация заняла слишком много времени и была прервана. Попробуйте создать более простой сайт или уменьшить количество функций.');
            } else if (error.message.includes('Load failed') || error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                this.showError('Потеряно соединение с сервером. Проверьте подключение к интернету и попробуйте снова.');
            } else {
                this.showError(`Ошибка: ${error.message}`);
            }
        } finally {
            this.stopGeneration();
        }
    }

    addChatMessage(role, content, projectId = null) {
        if (!this.chatMessages) return;

        var safeContent = String(content || 'Пустое сообщение');

        var messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;

        var avatar = document.createElement('div');
        avatar.className = 'chat-avatar';
        avatar.textContent = role === 'user' ? '👤' : '';

        var bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role === 'user' ? 'user-bubble' : 'ai-bubble'}`;

        // Обрабатываем контент с мыслями LLM
        this.processLLMContent(bubble, safeContent, role);

        // Добавляем превью если нужно
        this.addPreviewIfNeeded(bubble, role, projectId, safeContent);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(bubble);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    processLLMContent(container, content, role) {
        if (role === 'user') {
            // Для пользователя просто добавляем текст
            var text = document.createElement('div');
            text.className = 'chat-text';
            text.textContent = content;
            container.appendChild(text);
            return;
        }

        // Для AI обрабатываем мысли и контент
        var lines = content.split('\n');
        var currentSection = null;
        var currentContent = [];

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            
            // Определяем тип секции
            if (line.includes('🏗️') && line.includes('Planning') || line.includes('Анализирую запрос')) {
                this.finishCurrentSection(container, currentSection, currentContent);
                currentSection = 'planning';
                currentContent = [line];
            } else if (line.includes('👨‍💻') && line.includes('Processing') || line.includes('Генерирую')) {
                this.finishCurrentSection(container, currentSection, currentContent);
                currentSection = 'generating';
                currentContent = [line];
            } else if (line.includes('📋') && line.includes('ПЛАН') || line.includes('План разработки')) {
                this.finishCurrentSection(container, currentSection, currentContent);
                currentSection = 'plan';
                currentContent = [line];
            } else if (line.includes('✅') && line.includes('ВЫПОЛНЕННЫЕ') || line.includes('Выполненные этапы')) {
                this.finishCurrentSection(container, currentSection, currentContent);
                currentSection = 'completed';
                currentContent = [line];
            } else if (line.includes('HTML_START') || line.includes('```html')) {
                this.finishCurrentSection(container, currentSection, currentContent);
                currentSection = 'code';
                currentContent = [line];
            } else if (line.startsWith('💭') || line.startsWith('🤔') || line.startsWith('⚡')) {
                this.finishCurrentSection(container, currentSection, currentContent);
                currentSection = 'thinking';
                currentContent = [line];
            } else {
                currentContent.push(line);
            }
        }

        // Завершаем последнюю секцию
        this.finishCurrentSection(container, currentSection, currentContent);
    }

    finishCurrentSection(container, sectionType, content) {
        if (!content || content.length === 0) return;

        var text = content.join('\n').trim();
        if (!text) return;

        var element = document.createElement('div');
        
        switch (sectionType) {
            case 'thinking':
                element.className = 'llm-thinking';
                element.textContent = text;
                break;
            case 'planning':
                element.className = 'llm-planning';
                element.textContent = text;
                break;
            case 'generating':
                element.className = 'llm-generating';
                element.textContent = text;
                break;
            case 'plan':
            case 'completed':
                element.className = 'chat-text';
                element.innerHTML = text.replace(/\n/g, '<br>');
                break;
            case 'code':
                element.className = 'chat-text';
                element.innerHTML = text.replace(/\n/g, '<br>');
                break;
            default:
                element.className = 'chat-text';
                element.textContent = text;
        }

        container.appendChild(element);
    }

    addPreviewIfNeeded(container, role, projectId, content) {
        // Добавляем превью сайта, если это ответ AI с проектом
        if (role === 'assistant' && projectId && content.includes('Проект успешно создан')) {
            var previewContainer = document.createElement('div');
            previewContainer.className = 'website-preview-container';
            previewContainer.style.cssText = `
                margin-top: 15px;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                overflow: hidden;
                background: white;
            `;

            var previewHeader = document.createElement('div');
            previewHeader.style.cssText = `
                background: #f9fafb;
                padding: 12px 16px;
                border-bottom: 1px solid #e5e7eb;
                font-weight: 600;
                color: #374151;
                display: flex;
                align-items: center;
                gap: 8px;
            `;
            previewHeader.innerHTML = '🌐 <span>Превью сайта</span>';

            var previewFrame = document.createElement('iframe');
            previewFrame.style.cssText = `
                width: 100%;
                height: 400px;
                border: none;
                background: white;
            `;

            // Генерируем HTML из проекта
            this.generateWebsitePreview(projectId, previewFrame);

            previewContainer.appendChild(previewHeader);
            previewContainer.appendChild(previewFrame);
            container.appendChild(previewContainer);
        }

        // Добавляем кнопку скачивания, если есть project_id
        if (role === 'assistant' && projectId && content.includes('Проект успешно создан')) {
            var downloadBtn = document.createElement('button');
            downloadBtn.className = 'download-project-btn';
            downloadBtn.innerHTML = '📦 Скачать проект';
            downloadBtn.style.cssText = `
                margin-top: 10px;
                padding: 8px 16px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: background 0.3s;
            `;
            downloadBtn.addEventListener('click', () => {
                window.open(`/api/ai-editor/download/${projectId}`, '_blank');
            });
            downloadBtn.addEventListener('mouseenter', () => {
                downloadBtn.style.background = '#45a049';
            });
            downloadBtn.addEventListener('mouseleave', () => {
                downloadBtn.style.background = '#4CAF50';
            });
            container.appendChild(downloadBtn);
        }
    }

    generateWebsitePreview(projectId, iframe) {
        console.log('🚀 Запуск Next.js превью для проекта:', projectId);
        // Загружаем live-превью Next.js проекта
        var authToken = localStorage.getItem('windexai_token');
        console.log('🔑 Токен авторизации:', authToken ? 'присутствует' : 'отсутствует');
        
        // Проверяем наличие токена
        if (!authToken) {
            console.error('❌ Токен авторизации отсутствует');
            iframe.srcdoc = `<div style="padding:20px;text-align:center;color:#666;">
                <h3>❌ Ошибка авторизации</h3>
                <p>Требуется войти в систему для просмотра превью</p>
                <button onclick="window.location.href='/'">Войти</button>
            </div>`;
            return;
        }
        
        // Добавляем sandbox атрибуты для предотвращения проблем с навигацией
        iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox');
        iframe.setAttribute('loading', 'lazy');
        
        fetch(`/api/ai-editor/project/${projectId}/preview`, {
            headers: { 'Authorization': 'Bearer ' + authToken }
        })
        .then(res => {
            console.log('📡 Статус ответа:', res.status);
            if (res.status === 401) {
                // Токен недействителен, перенаправляем на страницу входа
                console.error('❌ Токен недействителен, перенаправляем на страницу входа');
                localStorage.removeItem('windexai_token');
                window.location.href = '/';
                return;
            }
            if (!res.ok) {
                throw new Error(`Preview API error: ${res.status}`);
            }
            return res.json();
        })
        .then(data => {
            if (!data) return; // Если произошло перенаправление
            console.log('📡 Ответ от preview API:', data);
            if (data.url) {
                console.log('✅ Получен URL для превью:', data.url);
                // Отображаем live-сайт в iframe
                iframe.src = data.url;
                iframe.style.border = 'none';
                // Убираем srcdoc, чтобы загрузить реальный URL
                iframe.removeAttribute('srcdoc');
                
                // Добавляем обработчик для предотвращения дублирования при навигации
                iframe.onload = function() {
                    console.log('🔄 Iframe загружен, предотвращаем дублирование навигации');
                    try {
                        // Блокируем навигацию, которая может вызвать дублирование
                        var iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                        if (iframeDoc) {
                            // Предотвращаем множественные загрузки
                            iframeDoc.addEventListener('DOMContentLoaded', function() {
                                console.log('🔄 DOM загружен в iframe');
                            }, { once: true });
                        }
                    } catch (e) {
                        console.log('⚠️ Не удалось получить доступ к содержимому iframe (CORS)');
                    }
                };
            } else {
                throw new Error('Preview URL not returned');
            }
        })
        .catch(err => {
            console.error('Preview error:', err);
            // Показываем сообщение об ошибке в iframe
            iframe.srcdoc = `<div style="padding:20px;text-align:center;color:#666;">
                <h3>❌ Ошибка превью</h3>
                <p>${err.message}</p>
                <button onclick="location.reload()">Попробовать снова</button>
            </div>`;
            iframe.style.border = 'none';
        });
    }

    extractDescription(fullText) {
        // Проверяем, есть ли информация о двухэтапном процессе
        if (fullText.includes('📋 ПЛАН РАЗРАБОТКИ:') || fullText.includes('✅ ВЫПОЛНЕННЫЕ ЭТАПЫ:')) {
            return this.extractTwoStageDescription(fullText);
        }

        // Проверяем, это Lite режим с HTML
        if (this.currentMode === 'lite' && fullText.includes('HTML_START')) {
            return this.generateLiteDescription(fullText);
        }

        // Ищем первую строку до маркеров для Pro режима
        var lines = fullText.split('\n');
        var description = '';

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            if (line.includes('PACKAGE_JSON_START') || line.includes('LAYOUT_TSX_START') || line.includes('PAGE_TSX_START')) {
                break;
            }
            if (line.trim()) {
                description += line.trim() + ' ';
            }
        }

        return description.trim() || '✅ Проект Next.js успешно создан и готов к запуску командой "npm run dev".';
    }

    extractTwoStageDescription(fullText) {
        // Извлекаем информацию о двухэтапном процессе
        var lines = fullText.split('\n');
        var description = '';
        var inArchitecturalPlan = false;
        var inCompletedTasks = false;
        var inFinalStructure = false;
        var planSteps = [];
        
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            
            if (line.includes('📋 ПЛАН РАЗРАБОТКИ:')) {
                inArchitecturalPlan = true;
                inCompletedTasks = false;
                inFinalStructure = false;
                description += '📋 **ПЛАН РАЗРАБОТКИ:**\n';
                continue;
            }
            
            if (line.includes('✅ ВЫПОЛНЕННЫЕ ЭТАПЫ:')) {
                inArchitecturalPlan = false;
                inCompletedTasks = true;
                inFinalStructure = false;
                description += '\n✅ **ВЫПОЛНЕННЫЕ ЭТАПЫ:**\n';
                continue;
            }
            
            if (line.includes('🔧 ИТОГОВАЯ СТРУКТУРА:')) {
                inArchitecturalPlan = false;
                inCompletedTasks = false;
                inFinalStructure = true;
                description += '\n🔧 **ИТОГОВАЯ СТРУКТУРА:**\n';
                continue;
            }
            
            if (line.includes('HTML_START') || line.includes('PACKAGE_JSON_START')) {
                // Достигли кода, останавливаемся
                break;
            }
            
            if (inArchitecturalPlan) {
                if (line && line.match(/^\d+\./)) {
                    // Это пункт плана
                    planSteps.push(line);
                    description += line + '\n';
                }
            } else if (inCompletedTasks || inFinalStructure) {
                if (line) {
                    description += line + '\n';
                }
            }
        }
        
        // Если есть план, показываем его в кратком описании
        if (planSteps.length > 0) {
            var shortDescription = '📋 **ПЛАН РАЗРАБОТКИ:**\n';
            shortDescription += planSteps.slice(0, 3).join('\n'); // Показываем первые 3 пункта
            if (planSteps.length > 3) {
                shortDescription += `\n... и еще ${planSteps.length - 3} этапов`;
            }
            shortDescription += '\n\n✅ **РЕЗУЛЬТАТ:** Сайт успешно создан!';
            return shortDescription;
        }
        
        // Добавляем информацию о результате
        if (fullText.includes('HTML_START')) {
            description += '\n✅ **РЕЗУЛЬТАТ:** HTML сайт успешно создан и готов к просмотру!';
        } else if (fullText.includes('PACKAGE_JSON_START')) {
            description += '\n✅ **РЕЗУЛЬТАТ:** Next.js проект успешно создан и готов к запуску!';
        }
        
        return description.trim();
    }

    generateLiteDescription(fullText) {
        // Извлекаем HTML для анализа
        var htmlMatch = fullText.match(/HTML_START\s*`{0,3}html\s*([\s\S]*?)\s*`{0,3}\s*HTML_END/);
        if (!htmlMatch || !htmlMatch[1]) {
            return '✅ HTML сайт успешно создан и готов к просмотру.';
        }

        var html = htmlMatch[1];
        
        // Извлекаем заголовок
        var titleMatch = html.match(/<title>(.*?)<\/title>/i);
        var title = titleMatch ? titleMatch[1].trim() : 'Веб-сайт';
        
        // Извлекаем основной заголовок
        var h1Match = html.match(/<h1[^>]*>(.*?)<\/h1>/i);
        var mainHeading = h1Match ? h1Match[1].trim() : '';
        
        // Определяем тип сайта по содержимому
        var siteType = this.detectSiteType(html);
        
        // Генерируем описание
        var description = `✅ Создан ${siteType} "${title}"`;
        
        if (mainHeading && mainHeading !== title) {
            description += ` с заголовком "${mainHeading}"`;
        }
        
        description += '. Сайт включает современный дизайн с адаптивной версткой, интерактивные элементы и готов к использованию.';
        
        return description;
    }

    detectSiteType(html) {
        var lowerHtml = html.toLowerCase();
        
        if (lowerHtml.includes('магазин') || lowerHtml.includes('store') || lowerHtml.includes('купить') || lowerHtml.includes('товар') || lowerHtml.includes('цена')) {
            return 'интернет-магазин';
        } else if (lowerHtml.includes('компания') || lowerHtml.includes('company') || lowerHtml.includes('корпоративный') || lowerHtml.includes('бизнес')) {
            return 'корпоративный сайт';
        } else if (lowerHtml.includes('портфолио') || lowerHtml.includes('portfolio') || lowerHtml.includes('работы') || lowerHtml.includes('проекты')) {
            return 'сайт-портфолио';
        } else if (lowerHtml.includes('блог') || lowerHtml.includes('blog') || lowerHtml.includes('статьи') || lowerHtml.includes('новости')) {
            return 'блог';
        } else if (lowerHtml.includes('лендинг') || lowerHtml.includes('landing') || lowerHtml.includes('продажа') || lowerHtml.includes('услуги')) {
            return 'лендинг-страница';
        } else if (lowerHtml.includes('ресторан') || lowerHtml.includes('кафе') || lowerHtml.includes('меню') || lowerHtml.includes('еда')) {
            return 'сайт ресторана';
        } else if (lowerHtml.includes('отель') || lowerHtml.includes('hotel') || lowerHtml.includes('бронирование') || lowerHtml.includes('номер')) {
            return 'сайт отеля';
        } else {
            return 'веб-сайт';
        }
    }

    updatePreview(content) {
        console.log('🔄 updatePreview called with content length:', content ? content.length : 0);
        console.log('🔄 Preview iframe exists:', !!this.previewIframe);
        if (!content || !this.previewIframe) {
            console.log('❌ updatePreview: missing content or iframe');
            return;
        }

        // Проверяем, есть ли Next.js проект
        if (content.includes('PACKAGE_JSON_START')) {
            // Для Next.js проектов используем живой сервер
            if (this.currentConversationId) {
                this.generateWebsitePreview(this.currentConversationId, this.previewIframe);
            }
            return;
        }

        // Проверяем, есть ли HTML_START (Lite mode)
        if (content.includes('HTML_START')) {
            console.log('🎯 Found HTML_START, extracting HTML...');
            var htmlMatch = content.match(/HTML_START\s*`{0,3}html\s*([\s\S]*?)\s*`{0,3}\s*HTML_END/);
            console.log('🔍 HTML match result:', htmlMatch);
            if (htmlMatch && htmlMatch[1]) {
                var html = htmlMatch[1].trim();
                console.log('✅ HTML extracted, setting iframe content, length:', html.length);
                console.log('✅ First 200 chars of HTML:', html.substring(0, 200));
                this.previewIframe.srcdoc = html;
                this.lastGeneratedHtml = html; // Сохраняем HTML для восстановления
                this.hideRestoreButton(); // Скрываем кнопку восстановления
                console.log('✅ Iframe content set successfully');
                return;
            } else {
                console.log('❌ HTML extraction failed, trying alternative patterns...');
                
                // Попробуем другие паттерны
                var altPatterns = [
                    /HTML_START\s*```html\s*([\s\S]*?)\s*```\s*HTML_END/,
                    /HTML_START\s*```\s*([\s\S]*?)\s*```\s*HTML_END/,
                    /HTML_START\s*([\s\S]*?)\s*HTML_END/,
                    /```html\s*([\s\S]*?)\s*```/
                ];
                
                for (var i = 0; i < altPatterns.length; i++) {
                    var match = content.match(altPatterns[i]);
                    if (match && match[1]) {
                        var html = match[1].trim();
                        console.log('✅ HTML found with pattern', i, 'length:', html.length);
                        this.previewIframe.srcdoc = html;
                        this.lastGeneratedHtml = html; // Сохраняем HTML для восстановления
                        this.hideRestoreButton(); // Скрываем кнопку восстановления
                        return;
                    }
                }
                
                console.log('❌ All HTML extraction patterns failed');
            }
        }

        // Проверяем, есть ли файловая структура в ответе
        var hasFileStructure = content.includes('FILE_STRUCTURE_START');

        if (hasFileStructure) {
            this.displayFileStructure(content);
        } else {
            // Старый формат - извлекаем HTML между маркерами
        var htmlMatch = content.match(/NEW_PAGE_START([\s\S]*?)NEW_PAGE_END/);
        if (htmlMatch) {
            var html = htmlMatch[1].trim();
            this.previewIframe.srcdoc = html;
            this.lastGeneratedHtml = html; // Сохраняем HTML для восстановления
            this.hideRestoreButton(); // Скрываем кнопку восстановления
        } else {
            // Пробуем найти HTML код без маркеров (fallback)
            var htmlCodeMatch = content.match(/```html([\s\S]*?)```/);
            if (htmlCodeMatch) {
                var html = htmlCodeMatch[1].trim();
                this.previewIframe.srcdoc = html;
                this.lastGeneratedHtml = html; // Сохраняем HTML для восстановления
                this.hideRestoreButton(); // Скрываем кнопку восстановления
                }
            }
        }
    }

    displayFileStructure(content) {
        // Извлекаем файловую структуру
        var structureMatch = content.match(/FILE_STRUCTURE_START([\s\S]*?)FILE_STRUCTURE_END/);

        // Извлекаем содержимое файлов - поддерживаем как старые, так и новые форматы
        // Старые форматы (HTML/CSS/JS)
        var htmlMatch = content.match(/HTML_START([\s\S]*?)HTML_END/);
        var mainCssMatch = content.match(/MAIN_CSS_START([\s\S]*?)MAIN_CSS_END/);
        var componentsCssMatch = content.match(/COMPONENTS_CSS_START([\s\S]*?)COMPONENTS_CSS_END/);
        var responsiveCssMatch = content.match(/RESPONSIVE_CSS_START([\s\S]*?)RESPONSIVE_CSS_END/);
        var mainJsMatch = content.match(/MAIN_JS_START([\s\S]*?)MAIN_JS_END/);
        var componentsJsMatch = content.match(/COMPONENTS_JS_START([\s\S]*?)COMPONENTS_JS_END/);
        var utilsJsMatch = content.match(/UTILS_JS_START([\s\S]*?)UTILS_JS_END/);

        // Новые форматы (Next.js)
        var packageJsonMatch = content.match(/PACKAGE_JSON_START([\s\S]*?)PACKAGE_JSON_END/);
        var tsconfigMatch = content.match(/TSCONFIG_START([\s\S]*?)TSCONFIG_END/);
        var tailwindConfigMatch = content.match(/TAILWIND_CONFIG_START([\s\S]*?)TAILWIND_CONFIG_END/);
        var nextConfigMatch = content.match(/NEXT_CONFIG_START([\s\S]*?)NEXT_CONFIG_END/);
        var layoutTsxMatch = content.match(/LAYOUT_TSX_START([\s\S]*?)LAYOUT_TSX_END/);
        var pageTsxMatch = content.match(/PAGE_TSX_START([\s\S]*?)PAGE_TSX_END/);
        var globalsCssMatch = content.match(/GLOBALS_CSS_START([\s\S]*?)GLOBALS_CSS_END/);

        // Поиск компонентов
        var heroComponentMatch = content.match(/HERO_COMPONENT_START([\s\S]*?)HERO_COMPONENT_END/);
        var featuresComponentMatch = content.match(/FEATURES_COMPONENT_START([\s\S]*?)FEATURES_COMPONENT_END/);
        var footerComponentMatch = content.match(/FOOTER_COMPONENT_START([\s\S]*?)FOOTER_COMPONENT_END/);
        var buttonComponentMatch = content.match(/BUTTON_COMPONENT_START([\s\S]*?)BUTTON_COMPONENT_END/);
        var cardComponentMatch = content.match(/CARD_COMPONENT_START([\s\S]*?)CARD_COMPONENT_END/);
        var containerComponentMatch = content.match(/CONTAINER_COMPONENT_START([\s\S]*?)CONTAINER_COMPONENT_END/);

        // Создаем объект с файлами - поддерживаем оба формата
        this.projectFiles = {};

        // Старые файлы (если есть)
        if (htmlMatch) this.projectFiles['index.html'] = htmlMatch[1].trim();
        if (mainCssMatch) this.projectFiles['styles/main.css'] = mainCssMatch[1].trim();
        if (componentsCssMatch) this.projectFiles['styles/components.css'] = componentsCssMatch[1].trim();
        if (responsiveCssMatch) this.projectFiles['styles/responsive.css'] = responsiveCssMatch[1].trim();
        if (mainJsMatch) this.projectFiles['scripts/main.js'] = mainJsMatch[1].trim();
        if (componentsJsMatch) this.projectFiles['scripts/components.js'] = componentsJsMatch[1].trim();
        if (utilsJsMatch) this.projectFiles['scripts/utils.js'] = utilsJsMatch[1].trim();

        // Новые файлы Next.js (если есть)
        if (packageJsonMatch) this.projectFiles['package.json'] = packageJsonMatch[1].trim();
        if (tsconfigMatch) this.projectFiles['tsconfig.json'] = tsconfigMatch[1].trim();
        if (tailwindConfigMatch) this.projectFiles['tailwind.config.js'] = tailwindConfigMatch[1].trim();
        if (nextConfigMatch) this.projectFiles['next.config.js'] = nextConfigMatch[1].trim();
        if (layoutTsxMatch) this.projectFiles['app/layout.tsx'] = layoutTsxMatch[1].trim();
        if (pageTsxMatch) this.projectFiles['app/page.tsx'] = pageTsxMatch[1].trim();
        if (globalsCssMatch) this.projectFiles['app/globals.css'] = globalsCssMatch[1].trim();

        // Компоненты
        if (heroComponentMatch) this.projectFiles['app/components/sections/Hero.tsx'] = heroComponentMatch[1].trim();
        if (featuresComponentMatch) this.projectFiles['app/components/sections/Features.tsx'] = featuresComponentMatch[1].trim();
        if (footerComponentMatch) this.projectFiles['app/components/sections/Footer.tsx'] = footerComponentMatch[1].trim();
        if (buttonComponentMatch) this.projectFiles['app/components/ui/Button.tsx'] = buttonComponentMatch[1].trim();
        if (cardComponentMatch) this.projectFiles['app/components/ui/Card.tsx'] = cardComponentMatch[1].trim();
        if (containerComponentMatch) this.projectFiles['app/components/ui/Container.tsx'] = containerComponentMatch[1].trim();

        // Для Next.js проектов показываем структуру, для обычных - превью
        var isNextjsProject = packageJsonMatch || layoutTsxMatch;

        if (isNextjsProject) {
            // Для Next.js проектов показываем инструкции по запуску
            this.showNextjsInstructions();
        } else if (this.projectFiles['index.html']) {
            // Для обычных проектов объединяем HTML с CSS и JS для превью
            var fullHtml = this.combineFilesForPreview();
            this.previewIframe.srcdoc = fullHtml;
        }

        // Показываем файловую структуру
        this.showFileExplorer();
    }

    combineFilesForPreview() {
        var html = this.projectFiles['index.html'];
        var mainCss = this.projectFiles['styles/main.css'];
        var componentsCss = this.projectFiles['styles/components.css'];
        var responsiveCss = this.projectFiles['styles/responsive.css'];
        var mainJs = this.projectFiles['scripts/main.js'];
        var componentsJs = this.projectFiles['scripts/components.js'];
        var utilsJs = this.projectFiles['scripts/utils.js'];

        // Заменяем ссылки на стили и скрипты на inline версии
        var combinedHtml = html;

        // Заменяем CSS ссылки
        if (mainCss) {
            combinedHtml = combinedHtml.replace(
                '<link rel="stylesheet" href="styles/main.css">',
                `<style>${mainCss}</style>`
            );
        }
        if (componentsCss) {
            combinedHtml = combinedHtml.replace(
                '<link rel="stylesheet" href="styles/components.css">',
                `<style>${componentsCss}</style>`
            );
        }
        if (responsiveCss) {
            combinedHtml = combinedHtml.replace(
                '<link rel="stylesheet" href="styles/responsive.css">',
                `<style>${responsiveCss}</style>`
            );
        }

        // Заменяем JS ссылки
        if (utilsJs) {
            combinedHtml = combinedHtml.replace(
                '<script src="scripts/utils.js"></script>',
                `<script>${utilsJs}</script>`
            );
        }
        if (componentsJs) {
            combinedHtml = combinedHtml.replace(
                '<script src="scripts/components.js"></script>',
                `<script>${componentsJs}</script>`
            );
        }
        if (mainJs) {
            combinedHtml = combinedHtml.replace(
                '<script src="scripts/main.js"></script>',
                `<script>${mainJs}</script>`
            );
        }

        return combinedHtml;
    }

    showFileExplorer() {
        // Создаем или обновляем файловый проводник
        var fileExplorer = document.getElementById('file-explorer');
        if (!fileExplorer) {
            fileExplorer = document.createElement('div');
            fileExplorer.id = 'file-explorer';
            fileExplorer.className = 'file-explorer';

            // Добавляем после панели превью
            var previewPanel = document.querySelector('.preview-panel');
            if (previewPanel) {
                previewPanel.insertAdjacentElement('afterend', fileExplorer);
            }
        }

        // Создаем HTML для файлового проводника
        var explorerHtml = `
            <div class="file-explorer-header">
                <h3>📁 Файлы проекта</h3>
                <button class="download-project-btn" onclick="aiEditor.downloadProject()">
                    💾 Скачать проект
                </button>
            </div>
            <div class="file-list">
        `;

        // Добавляем файлы в список
        Object.keys(this.projectFiles).forEach(filePath => {
            if (this.projectFiles[filePath]) {
                var fileName = filePath.split('/').pop();
                var fileIcon = this.getFileIcon(fileName);
                explorerHtml += `
                    <div class="file-item" onclick="aiEditor.showFileContent('${filePath}')">
                        <span class="file-icon">${fileIcon}</span>
                        <span class="file-name">${filePath}</span>
                        <button class="download-file-btn" onclick="event.stopPropagation(); aiEditor.downloadFile('${filePath}')">
                            ⬇️
                        </button>
                    </div>
                `;
            }
        });

        explorerHtml += '</div>';
        fileExplorer.innerHTML = explorerHtml;
    }

    getFileIcon(fileName) {
        if (fileName.endsWith('.html')) return '🌐';
        if (fileName.endsWith('.css')) return '🎨';
        if (fileName.endsWith('.js')) return '⚡';
        if (fileName.endsWith('.tsx') || fileName.endsWith('.ts')) return '⚛️';
        if (fileName.endsWith('.json')) return '📋';
        if (fileName === 'package.json') return '📦';
        if (fileName.includes('config')) return '⚙️';
        if (fileName.includes('tailwind')) return '🎨';
        return '📄';
    }

    showNextjsInstructions() {
        // Показываем инструкции по запуску Next.js проекта в области превью
        if (this.previewIframe) {
            var instructionsHtml = `
                <!DOCTYPE html>
                <html lang="ru">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Инструкции по запуску Next.js проекта</title>
                    <style>
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
                            line-height: 1.6;
                            color: #374151;
                            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                            margin: 0;
                            padding: 2rem;
                        }
                        .container {
                            max-width: 800px;
                            margin: 0 auto;
                            background: white;
                            border-radius: 16px;
                            padding: 2rem;
                            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                        }
                        h1 {
                            color: #1f2937;
                            margin-bottom: 1.5rem;
                            font-size: 2rem;
                            font-weight: 700;
                        }
                        h2 {
                            color: #374151;
                            margin-top: 2rem;
                            margin-bottom: 1rem;
                            font-size: 1.25rem;
                            font-weight: 600;
                        }
                        .step {
                            background: #f9fafb;
                            border: 1px solid #e5e7eb;
                            border-radius: 8px;
                            padding: 1rem;
                            margin: 1rem 0;
                        }
                        .command {
                            background: #1f2937;
                            color: #e5e7eb;
                            padding: 0.75rem 1rem;
                            border-radius: 6px;
                            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                            font-size: 0.875rem;
                            margin: 0.5rem 0;
                            overflow-x: auto;
                        }
                        .note {
                            background: #dbeafe;
                            border-left: 4px solid #3b82f6;
                            padding: 1rem;
                            margin: 1rem 0;
                            border-radius: 0 8px 8px 0;
                        }
                        .success {
                            background: #d1fae5;
                            border-left: 4px solid #10b981;
                            padding: 1rem;
                            margin: 1rem 0;
                            border-radius: 0 8px 8px 0;
                        }
                        .icon {
                            font-size: 1.5rem;
                            margin-right: 0.5rem;
                        }
                        ul {
                            padding-left: 1.5rem;
                        }
                        li {
                            margin-bottom: 0.5rem;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1><span class="icon">⚛️</span>Next.js проект создан!</h1>

                        <div class="success">
                            <strong>🎉 Поздравляем!</strong> Ваш Next.js проект с TypeScript и Tailwind CSS готов к использованию.
                        </div>

                        <h2>📋 Как запустить проект:</h2>

                        <div class="step">
                            <strong>1. Установите зависимости:</strong>
                            <div class="command">npm install</div>
                            <em>или</em>
                            <div class="command">yarn install</div>
                        </div>

                        <div class="step">
                            <strong>2. Запустите dev сервер:</strong>
                            <div class="command">npm run dev</div>
                            <em>или</em>
                            <div class="command">yarn dev</div>
                        </div>

                        <div class="step">
                            <strong>3. Откройте в браузере:</strong>
                            <div class="command">http://localhost:3000</div>
                        </div>

                        <h2>🛠️ Что включено в проект:</h2>
                        <ul>
                            <li><strong>Next.js 14+</strong> с App Router</li>
                            <li><strong>TypeScript</strong> для типизации</li>
                            <li><strong>Tailwind CSS</strong> для стилизации</li>
                            <li><strong>Модульная архитектура</strong> компонентов</li>
                            <li><strong>Responsive дизайн</strong> (Mobile-first)</li>
                            <li><strong>Оптимизация изображений</strong> с next/image</li>
                        </ul>

                        <div class="note">
                            <strong>💡 Совет:</strong> Используйте файловый проводник справа для просмотра и скачивания отдельных файлов проекта.
                        </div>

                        <h2>📁 Структура проекта:</h2>
                        <div class="command">
project-name/
├── 📦 package.json          # Зависимости и скрипты
├── ⚙️ tsconfig.json         # Конфигурация TypeScript
├── 🎨 tailwind.config.js    # Конфигурация Tailwind CSS
├── ⚙️ next.config.js        # Конфигурация Next.js
├── app/
│   ├── ⚛️ layout.tsx         # Основной layout
│   ├── ⚛️ page.tsx           # Главная страница
│   ├── 🎨 globals.css        # Глобальные стили
│   └── components/
│       ├── ui/              # UI компоненты
│       ├── sections/        # Секции страниц
│       └── layout/          # Layout компоненты
└── lib/
    ├── ⚛️ types.ts           # TypeScript типы
    └── ⚛️ utils.ts           # Утилиты
                        </div>

                        <div class="success">
                            <strong>Готово к разработке!</strong> Ваш современный Next.js проект настроен и готов к использованию.
                        </div>
                    </div>
                </body>
                </html>
            `;
            this.previewIframe.srcdoc = instructionsHtml;
        }
    }

    showFileContent(filePath) {
        var content = this.projectFiles[filePath];
        if (!content) return;

        // Создаем модальное окно для отображения содержимого файла
        var modal = document.createElement('div');
        modal.className = 'file-modal';
        modal.innerHTML = `
            <div class="file-modal-content">
                <div class="file-modal-header">
                    <h3>${filePath}</h3>
                    <button class="close-file-modal" onclick="this.closest('.file-modal').remove()">×</button>
                </div>
                <div class="file-modal-body">
                    <pre><code>${content}</code></pre>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    downloadFile(filePath) {
        var content = this.projectFiles[filePath];
        if (!content) return;

        var blob = new Blob([content], { type: 'text/plain' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = filePath.split('/').pop();
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    downloadProject() {
        if (!this.projectFiles) return;

        // Создаем ZIP файл (простая реализация)
        var zip = new Map();

        Object.keys(this.projectFiles).forEach(filePath => {
            if (this.projectFiles[filePath]) {
                zip.set(filePath, this.projectFiles[filePath]);
            }
        });

        // Простое решение - скачиваем файлы по отдельности
        // В будущем можно добавить библиотеку для создания ZIP
        Object.keys(this.projectFiles).forEach(filePath => {
            if (this.projectFiles[filePath]) {
                setTimeout(() => {
                    this.downloadFile(filePath);
                }, 100);
            }
        });
    }

    startGeneration() {
        if (this.sendBtn) {
            this.sendBtn.disabled = true;
            this.sendBtn.innerHTML = '<div class="loading-spinner"></div>';
        }

        if (this.typingIndicator) {
            this.typingIndicator.classList.remove('hidden');
            this.startThinkingAnimation();
        }

        this.updateStatus('Генерация сайта...');
    }

    stopGeneration() {
        if (this.sendBtn) {
            this.sendBtn.disabled = false;
            this.sendBtn.innerHTML = '<span id="send-btn-text">📤</span>';
        }

        if (this.typingIndicator) {
            this.typingIndicator.classList.add('hidden');
            this.stopThinkingAnimation();
        }
    }
    
    startThinkingAnimation() {
        // Очищаем историю мыслей
        const historyContainer = this.typingIndicator.querySelector('.thinking-history');
        if (historyContainer) {
            historyContainer.innerHTML = '';
        }
        
        // Устанавливаем начальную мысль
        this.updateCurrentThought('💭', 'Начинаю анализ...');
        
        // Начинаем получение реальных мыслей LLM
        this.startRealThinkingPolling();
    }
    
    nextThinkingThought() {
        const thoughts = [
            { icon: '💭', text: 'Анализирую запрос пользователя...' },
            { icon: '🏗️', text: 'Создаю архитектурный план разработки...' },
            { icon: '📋', text: 'Разрабатываю пошаговый план...' },
            { icon: '🎨', text: 'Продумываю дизайн и структуру...' },
            { icon: '👨‍💻', text: 'Генерирую HTML код...' },
            { icon: '🎯', text: 'Добавляю CSS стили и анимации...' },
            { icon: '⚡', text: 'Создаю интерактивность...' },
            { icon: '📱', text: 'Обеспечиваю адаптивность...' },
            { icon: '✨', text: 'Завершаю создание сайта...' },
            { icon: '🔍', text: 'Проверяю качество кода...' },
            { icon: '🚀', text: 'Подготавливаю финальный результат...' }
        ];
        
        // Перемещаем текущую мысль в историю
        this.moveCurrentToHistory();
        
        // Устанавливаем новую мысль
        const thought = thoughts[this.thinkingStep % thoughts.length];
        this.updateCurrentThought(thought.icon, thought.text);
        
        this.thinkingStep++;
    }
    
    updateCurrentThought(icon, text) {
        const currentContainer = this.typingIndicator.querySelector('.thinking-current');
        if (currentContainer) {
            const iconElement = currentContainer.querySelector('.thinking-icon');
            const textElement = currentContainer.querySelector('.thinking-text');
            
            if (iconElement) iconElement.textContent = icon;
            if (textElement) textElement.textContent = text;
        }
    }
    
    moveCurrentToHistory() {
        const currentContainer = this.typingIndicator.querySelector('.thinking-current');
        const historyContainer = this.typingIndicator.querySelector('.thinking-history');
        
        if (currentContainer && historyContainer) {
            const icon = currentContainer.querySelector('.thinking-icon').textContent;
            const text = currentContainer.querySelector('.thinking-text').textContent;
            
            // Создаем элемент истории
            const historyItem = document.createElement('div');
            historyItem.className = 'thinking-item';
            historyItem.innerHTML = `
                <div class="thinking-icon">${icon}</div>
                <div class="thinking-text">${text}</div>
            `;
            
            // Добавляем в историю
            historyContainer.appendChild(historyItem);
            
            // Ограничиваем количество элементов в истории
            const items = historyContainer.querySelectorAll('.thinking-item');
            if (items.length > 5) {
                items[0].remove();
            }
            
            // Прокручиваем вниз
            historyContainer.scrollTop = historyContainer.scrollHeight;
        }
    }
    
    stopThinkingAnimation() {
        if (this.thinkingInterval) {
            clearInterval(this.thinkingInterval);
            this.thinkingInterval = null;
        }
        
        // Останавливаем polling реальных мыслей
        this.stopRealThinkingPolling();
        
        // Очищаем контейнеры
        const historyContainer = this.typingIndicator.querySelector('.thinking-history');
        if (historyContainer) {
            historyContainer.innerHTML = '';
        }
        
        this.thinkingStep = 0;
    }
    
    startRealThinkingPolling() {
        if (!this.currentConversationId) return;
        
        this.thinkingPollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/ai-editor/thoughts/${this.currentConversationId}`, {
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const thoughts = data.thoughts || [];
                    
                    if (thoughts.length > 0) {
                        // Показываем последнюю мысль как текущую
                        const lastThought = thoughts[thoughts.length - 1];
                        this.updateCurrentThought(lastThought.icon, lastThought.text);
                        
                        // Показываем предыдущие мысли в истории
                        this.updateThinkingHistory(thoughts.slice(0, -1));
                    }
                }
            } catch (error) {
                console.error('Error fetching LLM thoughts:', error);
            }
        }, 1000); // Проверяем каждую секунду
    }
    
    updateThinkingHistory(thoughts) {
        const historyContainer = this.typingIndicator.querySelector('.thinking-history');
        if (!historyContainer) return;
        
        // Очищаем историю
        historyContainer.innerHTML = '';
        
        // Добавляем мысли в историю (показываем последние 5)
        const recentThoughts = thoughts.slice(-5);
        recentThoughts.forEach(thought => {
            const historyItem = document.createElement('div');
            historyItem.className = 'thinking-item';
            historyItem.innerHTML = `
                <div class="thinking-icon">${thought.icon}</div>
                <div class="thinking-text">${thought.text}</div>
            `;
            historyContainer.appendChild(historyItem);
        });
        
        // Прокручиваем вниз
        historyContainer.scrollTop = historyContainer.scrollHeight;
    }
    
    stopRealThinkingPolling() {
        if (this.thinkingPollingInterval) {
            clearInterval(this.thinkingPollingInterval);
            this.thinkingPollingInterval = null;
        }
    }
    
    showError(message) {
        if (!this.errorContainer) return;

        this.errorContainer.innerHTML = `
            <div class="error-message">
                ❌ ${message}
            </div>
        `;

        setTimeout(() => {
            this.errorContainer.innerHTML = '';
        }, 5000);

        this.updateStatus('Ошибка генерации');
    }

    updateStatus(status) {
        if (this.statusText) {
            this.statusText.textContent = status;
        }
    }

    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }

    autoResizeInput() {
        if (!this.chatInput) return;

        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
    }

    toggleSendButton() {
        if (!this.sendBtn || !this.chatInput) {
            console.log('toggleSendButton: missing elements', {
                sendBtn: !!this.sendBtn,
                chatInput: !!this.chatInput
            });
            return;
        }

        var hasText = this.chatInput.value.trim().length > 0;
        this.sendBtn.disabled = !hasText;

        // Дополнительная отладочная информация
        console.log('toggleSendButton:', {
            hasText,
            disabled: this.sendBtn.disabled,
            inputValue: this.chatInput.value,
            inputLength: this.chatInput.value.length
        });

        // Проверяем, что кнопка действительно разблокирована
        if (hasText && this.sendBtn.disabled) {
            console.error('Button should be enabled but is still disabled!');
        }
    }

    async copyHtml() {
        var iframe = this.previewIframe;
        if (!iframe || !iframe.srcdoc) {
            this.showError('Нет HTML для копирования');
            return;
        }

        try {
            await navigator.clipboard.writeText(iframe.srcdoc);
            this.updateStatus('HTML скопирован в буфер обмена');
        } catch (error) {
            console.error('Copy failed:', error);
            this.showError('Не удалось скопировать HTML');
        }
    }

    downloadHtml() {
        var iframe = this.previewIframe;
        if (!iframe || !iframe.srcdoc) {
            this.showError('Нет HTML для скачивания');
            return;
        }

        var blob = new Blob([iframe.srcdoc], { type: 'text/html' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'website.html';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.updateStatus('HTML файл скачан');
    }


    showDeployModal() {
        if (!this.previewIframe || !this.previewIframe.srcdoc) {
            this.showError('Нет HTML для деплоя');
            return;
        }

        this.deployModal.style.display = 'flex';
        this.deployTitle.value = '';
        this.deployDescription.value = '';
        this.hideDeployStatus();
    }

    hideDeployModal() {
        this.deployModal.style.display = 'none';
        this.hideDeployStatus();

        // Reset form and state
        this.deployTitle.value = '';
        this.deployDescription.value = '';
        this.confirmDeployBtn.style.display = 'block';
        this.lastDeploymentResult = null;
    }

    showDeployStatus(message, type = 'loading') {
        this.deployStatus.style.display = 'block';
        this.deployStatus.className = `deploy-status ${type}`;
        this.deployStatus.querySelector('.status-message').textContent = message;
    }

    hideDeployStatus() {
        this.deployStatus.style.display = 'none';
        this.deployActions.style.display = 'none';
    }

    async deployWebsite() {
        var title = this.deployTitle.value.trim();
        if (!title) {
            this.showError('Введите название сайта');
            return;
        }

        if (!this.previewIframe || !this.previewIframe.srcdoc) {
            this.showError('Нет HTML для деплоя');
            return;
        }

        var token = localStorage.getItem('windexai_token');
        if (!token) {
            this.showError('Необходима авторизация');
            return;
        }

        this.showDeployStatus('Деплой в процессе...', 'loading');
        this.confirmDeployBtn.disabled = true;

        try {
            // Extract HTML content
            var htmlContent = this.previewIframe.srcdoc;

            // Create deployment data
            var deploymentData = {
                title: title,
                description: this.deployDescription.value.trim() || null,
                html_content: htmlContent,
                css_content: null, // We'll extract CSS from HTML if needed
                js_content: null   // We'll extract JS from HTML if needed
            };

            var response = await fetch('/api/deploy/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(deploymentData)
            });

            if (!response.ok) {
                var errorMessage = 'Ошибка при деплое';
                try {
                    var errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (e) {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }

            var result = await response.json();

            // Store deployment result
            this.lastDeploymentResult = result;

            this.showDeployStatus(
                `✅ Сайт "${result.title}" успешно задеплоен!`,
                'success'
            );

            // Show action buttons
            this.deployActions.style.display = 'flex';

            // Hide deploy button and show success state
            this.confirmDeployBtn.style.display = 'none';

        } catch (error) {
            console.error('Deploy error:', error);
            var errorMessage = error.message || 'Неизвестная ошибка при деплое';
            this.showDeployStatus(`❌ Ошибка: ${errorMessage}`, 'error');
        } finally {
            this.confirmDeployBtn.disabled = false;
        }
    }

    openDeployedSite() {
        if (this.lastDeploymentResult && this.lastDeploymentResult.full_url) {
            window.open(this.lastDeploymentResult.full_url, '_blank');
        }
    }

    async copyDeploymentUrl() {
        if (this.lastDeploymentResult && this.lastDeploymentResult.full_url) {
            try {
                await navigator.clipboard.writeText(this.lastDeploymentResult.full_url);
                this.showDeployStatus('📋 URL скопирован в буфер обмена!', 'success');
                setTimeout(() => {
                    this.hideDeployStatus();
                }, 2000);
            } catch (error) {
                console.error('Copy failed:', error);
                this.showDeployStatus('❌ Не удалось скопировать URL', 'error');
            }
        }
    }

    toggleEditMode() {
        this.editMode = !this.editMode;

        if (this.editMode) {
            this.enterEditMode();
        } else {
            this.exitEditMode();
        }
    }

    enterEditMode() {
        this.editModeBtn.textContent = '✅ Выйти из редактирования';
        this.editModeBtn.classList.add('edit-mode-active');

        // Add edit mode instructions
        this.addEditModeInstructions();

        // Make elements editable
        this.makeElementsEditable();

        this.updateStatus('Режим редактирования активен. Кликните на элемент для редактирования.');
    }

    exitEditMode() {
        this.editModeBtn.textContent = '✏️ Редактировать';
        this.editModeBtn.classList.remove('edit-mode-active');

        // Remove edit mode instructions
        this.removeEditModeInstructions();

        // Remove editable classes
        this.removeEditableClasses();

        // Remove edit prompt messages
        var existingEditPrompts = this.chatMessages.querySelectorAll('.edit-prompt-message');
        existingEditPrompts.forEach(prompt => prompt.remove());

        this.selectedElement = null;
        this.updateStatus('Режим редактирования отключен.');
    }

    addEditModeInstructions() {
        var iframe = this.previewIframe;
        if (!iframe || !iframe.contentDocument) return;

        var instructions = iframe.contentDocument.createElement('div');
        instructions.className = 'edit-mode-instructions';
        instructions.textContent = '✏️ Режим редактирования: кликните на элемент для редактирования';
        iframe.contentDocument.body.appendChild(instructions);
    }

    removeEditModeInstructions() {
        var iframe = this.previewIframe;
        if (!iframe || !iframe.contentDocument) return;

        var instructions = iframe.contentDocument.querySelector('.edit-mode-instructions');
        if (instructions) {
            instructions.remove();
        }
    }

    makeElementsEditable() {
        var iframe = this.previewIframe;
        if (!iframe || !iframe.contentDocument) return;

        var doc = iframe.contentDocument;

        // Find editable elements (headings, paragraphs, buttons, etc.)
        var editableSelectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'span', 'div[class*="title"]', 'div[class*="subtitle"]',
            'button', 'a', 'li', 'td', 'th'
        ];

        this.editableElements = [];

        editableSelectors.forEach(selector => {
            var elements = doc.querySelectorAll(selector);
            elements.forEach((element, index) => {
                if (element.textContent.trim() && !element.querySelector('script')) {
                    element.classList.add('editable-element');
                    element.setAttribute('data-element-id', `${selector}-${index}`);
                    element.setAttribute('data-element-type', selector);

                    // Add click handler
                    element.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.selectElement(element);
                    });

                    this.editableElements.push(element);
                }
            });
        });
    }

    getElementLabel(element) {
        var tagName = element.tagName.toLowerCase();

        var labels = {
            'h1': 'Заголовок',
            'h2': 'Подзаголовок',
            'h3': 'Заголовок 3',
            'h4': 'Заголовок 4',
            'h5': 'Заголовок 5',
            'h6': 'Заголовок 6',
            'p': 'Текст',
            'button': 'Кнопка',
            'a': 'Ссылка',
            'li': 'Элемент списка',
            'td': 'Ячейка таблицы',
            'th': 'Заголовок таблицы'
        };

        return labels[tagName] || 'Элемент';
    }

    selectElement(element) {
        // Remove previous selection
        if (this.selectedElement) {
            this.selectedElement.classList.remove('selected');
        }

        // Select new element
        this.selectedElement = element;
        element.classList.add('selected');

        // Show edit prompt in chat
        this.showElementEditPrompt(element);
    }

    showElementEditPrompt(element) {
        var elementType = this.getElementLabel(element);
        var currentText = element.textContent.trim();

        // Remove previous edit prompts
        var existingEditPrompts = this.chatMessages.querySelectorAll('.edit-prompt-message');
        existingEditPrompts.forEach(prompt => prompt.remove());

        // Add message to chat
        var messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message edit-prompt-message';
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-text">
                    ✏️ <strong>Редактирование элемента:</strong> ${elementType}<br>
                    <em>Текущий текст:</em> "${currentText}"<br><br>
                    Опишите, как вы хотите изменить этот элемент. Например:<br>
                    • "Измени текст на 'Добро пожаловать'"<br>
                    • "Сделай заголовок больше"<br>
                    • "Измени цвет на синий"
                </div>
            </div>
        `;

        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;

        // Focus on input
        this.chatInput.focus();
    }

    removeEditableClasses() {
        var iframe = this.previewIframe;
        if (!iframe || !iframe.contentDocument) return;

        // Remove all editable classes
        this.editableElements.forEach(element => {
            element.classList.remove('editable-element', 'selected');
            element.removeAttribute('data-element-id');
            element.removeAttribute('data-element-type');
        });

        this.editableElements = [];
    }

    // Resizable panels methods
    startDrag(e) {
        // Prevent default to avoid text selection
        e.preventDefault();
        e.stopPropagation();

        this.isDragging = true;
        this.startX = e.clientX;

        // Get current widths more reliably
        var containerRect = this.chatPanel.parentElement.getBoundingClientRect();
        var chatRect = this.chatPanel.getBoundingClientRect();

        this.startChatWidth = chatRect.width;
        this.containerWidth = containerRect.width;

        this.panelDivider.classList.add('dragging');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';

        // Add event listeners with passive: false for better control
        document.addEventListener('mousemove', this.boundOnDrag, { passive: false });
        document.addEventListener('mouseup', this.boundStopDrag, { passive: false });
    }

    onDrag(e) {
        if (!this.isDragging) return;

        e.preventDefault();

        var deltaX = e.clientX - this.startX;
        var newChatWidth = this.startChatWidth + deltaX;

        // Calculate percentage
        var chatPercentage = (newChatWidth / this.containerWidth) * 100;
        var previewPercentage = 100 - chatPercentage;

        // Apply constraints
        var minChatPercentage = 25; // Minimum 25% for chat
        var maxChatPercentage = 75; // Maximum 75% for chat

        if (chatPercentage >= minChatPercentage && chatPercentage <= maxChatPercentage) {
            // Use more stable CSS custom properties
            this.chatPanel.style.setProperty('--chat-width', `${chatPercentage}%`);
            this.previewPanel.style.setProperty('--preview-width', `${previewPercentage}%`);

            // Apply flex values
            this.chatPanel.style.flex = `0 0 ${chatPercentage}%`;
            this.previewPanel.style.flex = `0 0 ${previewPercentage}%`;
        }
    }

    stopDrag() {
        if (!this.isDragging) return;

        this.isDragging = false;
        this.panelDivider.classList.remove('dragging');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';

        // Remove event listeners
        document.removeEventListener('mousemove', this.boundOnDrag);
        document.removeEventListener('mouseup', this.boundStopDrag);

        // Save panel sizes
        this.savePanelSizes();
    }

    savePanelSizes() {
        var chatPercentage = (this.chatPanel.offsetWidth / this.chatPanel.parentElement.offsetWidth) * 100;
        localStorage.setItem('windexai_chat_panel_size', chatPercentage.toString());
    }

    loadPanelSizes() {
        var savedSize = localStorage.getItem('windexai_chat_panel_size');
        if (savedSize) {
            var chatPercentage = parseFloat(savedSize);
            var previewPercentage = 100 - chatPercentage;

            // Apply constraints
            var minChatPercentage = 25;
            var maxChatPercentage = 75;

            if (chatPercentage >= minChatPercentage && chatPercentage <= maxChatPercentage) {
                this.chatPanel.style.flex = `0 0 ${chatPercentage}%`;
                this.previewPanel.style.flex = `0 0 ${previewPercentage}%`;
            }
        }
    }

    async editSelectedElement(editInstruction) {
        if (!this.selectedElement) {
            this.showError('Сначала выберите элемент для редактирования');
            return;
        }

        var element = this.selectedElement;
        var elementType = element.getAttribute('data-element-type');
        var currentText = element.textContent.trim();

        // Add user message to chat
        this.addChatMessage('user', editInstruction);

        // Create edit request
        var editRequest = {
            element_type: elementType,
            current_text: currentText,
            edit_instruction: editInstruction,
            html_content: this.previewIframe.srcdoc
        };

        try {
            var token = localStorage.getItem('windexai_token');
            if (!token) {
                this.showError('Необходима авторизация');
                return;
            }

            this.startGeneration();

            var response = await fetch('/api/ai-editor/edit-element', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(editRequest)
            });

            if (!response.ok) {
                var errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка при редактировании элемента');
            }

            var result = await response.json();

            // Add assistant response to chat
            this.addChatMessage('assistant', result.response);

            // Update preview with edited content
            this.updatePreview(result.html_content);

            // Exit edit mode
            this.exitEditMode();

            this.updateStatus('Элемент успешно отредактирован!');

        } catch (error) {
            console.error('Edit element error:', error);
            this.showError(`Ошибка при редактировании: ${error.message}`);
        } finally {
            this.stopGeneration();
        }
    }

    // Методы для работы с историей чатов
    async loadConversations() {
        try {
            var token = localStorage.getItem('windexai_token');
            if (!token) return;

            var response = await fetch('/api/ai-editor/conversations', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                var data = await response.json();
                this.renderConversations(data.conversations);
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
        }
    }

    renderConversations(conversations) {
        if (!this.conversationsList) return;

        this.conversationsList.innerHTML = '';

        if (conversations.length === 0) {
            this.conversationsList.innerHTML = `
                <div style="padding: 2rem; text-align: center; color: #6b7280;">
                    <p>Нет сохраненных проектов</p>
                    <p style="font-size: 0.8rem;">Создайте новый проект, чтобы начать работу</p>
                </div>
            `;
            return;
        }

        conversations.forEach(conv => {
            var convElement = document.createElement('div');
            convElement.className = 'conversation-item';
            if (conv.id === this.currentConversationId) {
                convElement.classList.add('active');
            }

            var date = new Date(conv.date).toLocaleDateString('ru-RU', {
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });

            convElement.innerHTML = `
                <div class="conversation-title">${conv.title}</div>
                <div class="conversation-preview">${conv.preview}</div>
                <div class="conversation-meta">
                    <span class="conversation-date">${date}</span>
                    <span class="conversation-count">${conv.message_count}</span>
                </div>
                <div class="conversation-actions">
                    <button class="conversation-delete" onclick="event.stopPropagation(); aiEditor.deleteConversation(${conv.id})">🗑️</button>
                </div>
            `;

            convElement.addEventListener('click', () => {
                this.loadConversation(conv.id);
            });

            this.conversationsList.appendChild(convElement);
        });
    }

    async loadConversation(conversationId) {
        try {
            var token = localStorage.getItem('windexai_token');
            if (!token) return;

            var response = await fetch(`/api/ai-editor/conversations/${conversationId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                var data = await response.json();
                this.currentConversationId = conversationId;
                this.displayConversation(data.conversation);
                this.loadConversations(); // Обновляем список для показа активного
            }
        } catch (error) {
            console.error('Error loading conversation:', error);
        }
    }

    displayConversation(conversation) {
        // Очищаем чат
        this.chatMessages.innerHTML = '';

        // Добавляем сообщения из истории
        conversation.messages.forEach(msg => {
            this.addChatMessage(msg.role, msg.content);
        });

        // Прокручиваем вниз
        this.scrollToBottom();
    }

    async createNewProject() {
        try {
            var token = localStorage.getItem('windexai_token');
            if (!token) return;

            var response = await fetch('/api/ai-editor/conversations', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                var data = await response.json();
                this.currentConversationId = data.conversation_id;

                // Очищаем чат
                this.chatMessages.innerHTML = '';

                // Добавляем приветственное сообщение
                this.addChatMessage('assistant', 'Привет! Я AI-помощник для создания веб-сайтов. Просто опишите, какой сайт вы хотите создать, и я сгенерирую его для вас!');

                // Обновляем список разговоров
                this.loadConversations();

                this.updateStatus('Новый проект создан');
            }
        } catch (error) {
            console.error('Error creating new project:', error);
            this.showError('Ошибка при создании нового проекта');
        }
    }

    async deleteConversation(conversationId) {
        if (!confirm('Вы уверены, что хотите удалить этот проект?')) {
            return;
        }

        try {
            var token = localStorage.getItem('windexai_token');
            if (!token) return;

            var response = await fetch(`/api/ai-editor/conversations/${conversationId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                // Если удаляем текущий разговор, создаем новый
                if (conversationId === this.currentConversationId) {
                    this.currentConversationId = null;
                    this.chatMessages.innerHTML = '';
                    this.addChatMessage('assistant', 'Привет! Я AI-помощник для создания веб-сайтов. Просто опишите, какой сайт вы хотите создать, и я сгенерирую его для вас!');
                }

                this.loadConversations();
                this.updateStatus('Проект удален');
            }
        } catch (error) {
            console.error('Error deleting conversation:', error);
            this.showError('Ошибка при удалении проекта');
        }
    }

    checkUrlParams() {
        // Проверяем URL параметры для открытия конкретного проекта
        var urlParams = new URLSearchParams(window.location.search);
        var projectId = urlParams.get('project');
        var returnToChat = urlParams.get('returnToChat');

        if (projectId) {
            // Загружаем конкретный проект
            this.loadConversation(parseInt(projectId));
            
            // Если это возврат к чату, фокусируемся на чате
            if (returnToChat === 'true') {
                this.focusOnChat();
            }
            
            // Очищаем URL от параметров
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    focusOnChat() {
        // Фокусируемся на чате при возврате к проекту
        setTimeout(() => {
            // Прокручиваем к последнему сообщению в чате
            if (this.chatMessages) {
                this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
            }
            
            // Фокусируемся на поле ввода
            if (this.chatInput) {
                this.chatInput.focus();
            }
            
            // Показываем уведомление
            this.showSuccess('Проект загружен! Вы можете продолжить работу в чате.');
        }, 1000);
    }

    openUserProfile() {
        // Navigate to the user's profile/dashboard page
        window.location.href = '/profile';
    }

    showProfileModal() {
        if (this.profileModal) {
            // Populate profile data
            var usernameSpan = document.getElementById('profile-username');
            var emailSpan = document.getElementById('profile-email');
            if (this.user) {
                if (usernameSpan) usernameSpan.textContent = this.user.username;
                if (emailSpan) emailSpan.textContent = this.user.email;
            }
            this.profileModal.classList.remove('hidden');
        }
    }

    hideProfileModal() {
        if (this.profileModal) {
            this.profileModal.classList.add('hidden');
        }
    }
    
    showProjectLaunchInfo(content) {
        console.log('🚀 Showing project launch info');
        
        // Извлекаем URL проекта из контента
        var urlMatch = content.match(/\*\*URL для просмотра:\*\* (http:\/\/localhost:\d+)/);
        if (urlMatch) {
            var projectUrl = urlMatch[1];
            console.log('🔗 Project URL found:', projectUrl);
            
            // Создаем кнопку для открытия проекта
            var launchButton = document.createElement('button');
            launchButton.className = 'project-launch-btn';
            launchButton.innerHTML = '🚀 Открыть проект';
            launchButton.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #22c55e;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
                z-index: 1000;
                transition: all 0.3s ease;
            `;
            
            launchButton.addEventListener('click', () => {
                window.open(projectUrl, '_blank');
            });
            
            launchButton.addEventListener('mouseenter', () => {
                launchButton.style.transform = 'translateY(-2px)';
                launchButton.style.boxShadow = '0 6px 16px rgba(34, 197, 94, 0.4)';
            });
            
            launchButton.addEventListener('mouseleave', () => {
                launchButton.style.transform = 'translateY(0)';
                launchButton.style.boxShadow = '0 4px 12px rgba(34, 197, 94, 0.3)';
            });
            
            // Добавляем кнопку на страницу
            document.body.appendChild(launchButton);
            
            // Автоматически удаляем кнопку через 30 секунд
            setTimeout(() => {
                if (launchButton.parentNode) {
                    launchButton.parentNode.removeChild(launchButton);
                }
            }, 30000);
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.aiEditor = new AIEditor();
});
