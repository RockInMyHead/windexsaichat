class AIEditor {
    constructor() {
        this.conversationHistory = [];
        this.currentGeneration = null;
        this.currentConversationId = null;
        this.authToken = localStorage.getItem('windexai_token');
        this.initializeElements();
        this.setupEventListeners();
        this.checkAuth();
        this.loadConversations();
    }

    initializeElements() {
        // Получаем элементы DOM
        this.chatInput = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-chat-btn');
        this.chatMessages = document.getElementById('chat-messages');
        this.previewIframe = document.getElementById('preview');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.errorContainer = document.getElementById('error-container');
        this.statusText = document.getElementById('status-text');
        this.copyBtn = document.getElementById('copy-html-btn');
        this.downloadBtn = document.getElementById('download-html-btn');
        this.deployBtn = document.getElementById('deploy-btn');
        this.editModeBtn = document.getElementById('edit-mode-btn');
        this.logoutBtn = document.getElementById('logout-btn');
        this.userNameSpan = document.getElementById('user-name');
        
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
        
        // Store deployment result
        this.lastDeploymentResult = null;

    }

    setupEventListeners() {
        // Обработчик отправки
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
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
        if (this.logoutBtn) {
            this.logoutBtn.addEventListener('click', () => this.logout());
        }
        
        // История чатов
        if (this.newProjectBtn) {
            this.newProjectBtn.addEventListener('click', () => this.createNewProject());
        }
        
        // Load saved panel sizes
        this.loadPanelSizes();

    }

    async checkAuth() {
        try {
            const token = localStorage.getItem('windexai_token');
            if (!token) {
                window.location.href = '/';
                return;
            }

            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                localStorage.removeItem('windexai_token');
                window.location.href = '/';
                return;
            }

            const user = await response.json();
            if (this.userNameSpan) {
                this.userNameSpan.textContent = user.username;
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            window.location.href = '/';
        }
    }

    async sendMessage() {
        const message = this.chatInput?.value?.trim();
        if (!message) return;


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
            const token = localStorage.getItem('windexai_token');
            if (!token) {
                throw new Error('Токен авторизации не найден');
            }

            const response = await fetch('/api/ai-editor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    messages: this.conversationHistory,
                    model: 'gpt-4o-mini',
                    conversation_id: this.currentConversationId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            const content = data.content || 'Ответ получен без содержания';
            
            // Сохраняем conversation_id
            if (data.conversation_id) {
                this.currentConversationId = data.conversation_id;
            }
            
            // Добавляем ответ AI
            this.conversationHistory.push({role: 'assistant', content: content});
            
            // Извлекаем описание для чата
            const description = this.extractDescription(content);
            this.addChatMessage('assistant', description);
            
            // Обновляем превью
            this.updatePreview(content);
            
            // Обновляем список разговоров
            this.loadConversations();
            
            this.updateStatus('Сайт успешно создан');

        } catch (error) {
            console.error('Generation error:', error);
            this.showError(`Ошибка: ${error.message}`);
        } finally {
            this.stopGeneration();
        }
    }

    addChatMessage(role, content) {
        if (!this.chatMessages) return;
        
        const safeContent = String(content || 'Пустое сообщение');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'chat-avatar';
        avatar.textContent = role === 'user' ? '👤' : '🤖';
        
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role === 'user' ? 'user-bubble' : 'ai-bubble'}`;
        
        const text = document.createElement('div');
        text.className = 'chat-text';
        text.textContent = safeContent;
        
        bubble.appendChild(text);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(bubble);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    extractDescription(fullText) {
        if (!fullText || typeof fullText !== 'string') {
            return 'Сайт создан успешно!';
        }
        
        // Ищем первую строку до маркеров
        const lines = fullText.split('\n');
        let description = '';
        
        for (let line of lines) {
            if (line.includes('NEW_PAGE_START') || line.includes('TITLE_PAGE_START')) {
                break;
            }
            if (line.trim()) {
                description += line.trim() + ' ';
            }
        }
        
        return description.trim() || 'Сайт создан успешно!';
    }

    updatePreview(content) {
        if (!content || !this.previewIframe) return;
        
        // Проверяем, есть ли файловая структура в ответе
        const hasFileStructure = content.includes('FILE_STRUCTURE_START') || content.includes('HTML_START');
        
        if (hasFileStructure) {
            this.displayFileStructure(content);
        } else {
            // Старый формат - извлекаем HTML между маркерами
        const htmlMatch = content.match(/NEW_PAGE_START([\s\S]*?)NEW_PAGE_END/);
        if (htmlMatch) {
            const html = htmlMatch[1].trim();
            this.previewIframe.srcdoc = html;
        } else {
            // Пробуем найти HTML код без маркеров (fallback)
            const htmlCodeMatch = content.match(/```html([\s\S]*?)```/);
            if (htmlCodeMatch) {
                const html = htmlCodeMatch[1].trim();
                this.previewIframe.srcdoc = html;
                }
            }
        }
    }

    displayFileStructure(content) {
        // Извлекаем файловую структуру
        const structureMatch = content.match(/FILE_STRUCTURE_START([\s\S]*?)FILE_STRUCTURE_END/);
        
        // Извлекаем содержимое файлов - поддерживаем как старые, так и новые форматы
        // Старые форматы (HTML/CSS/JS)
        const htmlMatch = content.match(/HTML_START([\s\S]*?)HTML_END/);
        const mainCssMatch = content.match(/MAIN_CSS_START([\s\S]*?)MAIN_CSS_END/);
        const componentsCssMatch = content.match(/COMPONENTS_CSS_START([\s\S]*?)COMPONENTS_CSS_END/);
        const responsiveCssMatch = content.match(/RESPONSIVE_CSS_START([\s\S]*?)RESPONSIVE_CSS_END/);
        const mainJsMatch = content.match(/MAIN_JS_START([\s\S]*?)MAIN_JS_END/);
        const componentsJsMatch = content.match(/COMPONENTS_JS_START([\s\S]*?)COMPONENTS_JS_END/);
        const utilsJsMatch = content.match(/UTILS_JS_START([\s\S]*?)UTILS_JS_END/);

        // Новые форматы (Next.js)
        const packageJsonMatch = content.match(/PACKAGE_JSON_START([\s\S]*?)PACKAGE_JSON_END/);
        const tsconfigMatch = content.match(/TSCONFIG_START([\s\S]*?)TSCONFIG_END/);
        const tailwindConfigMatch = content.match(/TAILWIND_CONFIG_START([\s\S]*?)TAILWIND_CONFIG_END/);
        const nextConfigMatch = content.match(/NEXT_CONFIG_START([\s\S]*?)NEXT_CONFIG_END/);
        const layoutTsxMatch = content.match(/LAYOUT_TSX_START([\s\S]*?)LAYOUT_TSX_END/);
        const pageTsxMatch = content.match(/PAGE_TSX_START([\s\S]*?)PAGE_TSX_END/);
        const globalsCssMatch = content.match(/GLOBALS_CSS_START([\s\S]*?)GLOBALS_CSS_END/);

        // Поиск компонентов
        const heroComponentMatch = content.match(/HERO_COMPONENT_START([\s\S]*?)HERO_COMPONENT_END/);
        const featuresComponentMatch = content.match(/FEATURES_COMPONENT_START([\s\S]*?)FEATURES_COMPONENT_END/);
        const footerComponentMatch = content.match(/FOOTER_COMPONENT_START([\s\S]*?)FOOTER_COMPONENT_END/);
        const buttonComponentMatch = content.match(/BUTTON_COMPONENT_START([\s\S]*?)BUTTON_COMPONENT_END/);
        const cardComponentMatch = content.match(/CARD_COMPONENT_START([\s\S]*?)CARD_COMPONENT_END/);
        const containerComponentMatch = content.match(/CONTAINER_COMPONENT_START([\s\S]*?)CONTAINER_COMPONENT_END/);

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
        const isNextjsProject = packageJsonMatch || layoutTsxMatch;
        
        if (isNextjsProject) {
            // Для Next.js проектов показываем инструкции по запуску
            this.showNextjsInstructions();
        } else if (this.projectFiles['index.html']) {
            // Для обычных проектов объединяем HTML с CSS и JS для превью
            const fullHtml = this.combineFilesForPreview();
            this.previewIframe.srcdoc = fullHtml;
        }

        // Показываем файловую структуру
        this.showFileExplorer();
    }

    combineFilesForPreview() {
        const html = this.projectFiles['index.html'];
        const mainCss = this.projectFiles['styles/main.css'];
        const componentsCss = this.projectFiles['styles/components.css'];
        const responsiveCss = this.projectFiles['styles/responsive.css'];
        const mainJs = this.projectFiles['scripts/main.js'];
        const componentsJs = this.projectFiles['scripts/components.js'];
        const utilsJs = this.projectFiles['scripts/utils.js'];

        // Заменяем ссылки на стили и скрипты на inline версии
        let combinedHtml = html;

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
        let fileExplorer = document.getElementById('file-explorer');
        if (!fileExplorer) {
            fileExplorer = document.createElement('div');
            fileExplorer.id = 'file-explorer';
            fileExplorer.className = 'file-explorer';
            
            // Добавляем после панели превью
            const previewPanel = document.querySelector('.preview-panel');
            if (previewPanel) {
                previewPanel.insertAdjacentElement('afterend', fileExplorer);
            }
        }

        // Создаем HTML для файлового проводника
        let explorerHtml = `
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
                const fileName = filePath.split('/').pop();
                const fileIcon = this.getFileIcon(fileName);
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
            const instructionsHtml = `
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
                            <strong>🚀 Готово к разработке!</strong> Ваш современный Next.js проект настроен и готов к использованию.
                        </div>
                    </div>
                </body>
                </html>
            `;
            this.previewIframe.srcdoc = instructionsHtml;
        }
    }

    showFileContent(filePath) {
        const content = this.projectFiles[filePath];
        if (!content) return;

        // Создаем модальное окно для отображения содержимого файла
        const modal = document.createElement('div');
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
        const content = this.projectFiles[filePath];
        if (!content) return;

        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
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
        const zip = new Map();
        
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
        }
        
        this.updateStatus('Генерация сайта...');
    }

    stopGeneration() {
        if (this.sendBtn) {
            this.sendBtn.disabled = false;
            this.sendBtn.innerHTML = '📤';
        }
        
        if (this.typingIndicator) {
            this.typingIndicator.classList.add('hidden');
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
        if (!this.sendBtn || !this.chatInput) return;
        
        this.sendBtn.disabled = !this.chatInput.value.trim();
    }

    async copyHtml() {
        const iframe = this.previewIframe;
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
        const iframe = this.previewIframe;
        if (!iframe || !iframe.srcdoc) {
            this.showError('Нет HTML для скачивания');
            return;
        }

        const blob = new Blob([iframe.srcdoc], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'website.html';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.updateStatus('HTML файл скачан');
    }

    logout() {
        localStorage.removeItem('windexai_token');
        window.location.href = '/';
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
        const title = this.deployTitle.value.trim();
        if (!title) {
            this.showError('Введите название сайта');
            return;
        }
        
        if (!this.previewIframe || !this.previewIframe.srcdoc) {
            this.showError('Нет HTML для деплоя');
            return;
        }
        
        const token = localStorage.getItem('windexai_token');
        if (!token) {
            this.showError('Необходима авторизация');
            return;
        }
        
        this.showDeployStatus('Деплой в процессе...', 'loading');
        this.confirmDeployBtn.disabled = true;
        
        try {
            // Extract HTML content
            const htmlContent = this.previewIframe.srcdoc;
            
            // Create deployment data
            const deploymentData = {
                title: title,
                description: this.deployDescription.value.trim() || null,
                html_content: htmlContent,
                css_content: null, // We'll extract CSS from HTML if needed
                js_content: null   // We'll extract JS from HTML if needed
            };
            
            const response = await fetch('/api/deploy/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(deploymentData)
            });
            
            if (!response.ok) {
                let errorMessage = 'Ошибка при деплое';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (e) {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            
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
            const errorMessage = error.message || 'Неизвестная ошибка при деплое';
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
        const existingEditPrompts = this.chatMessages.querySelectorAll('.edit-prompt-message');
        existingEditPrompts.forEach(prompt => prompt.remove());
        
        this.selectedElement = null;
        this.updateStatus('Режим редактирования отключен.');
    }
    
    addEditModeInstructions() {
        const iframe = this.previewIframe;
        if (!iframe || !iframe.contentDocument) return;
        
        const instructions = iframe.contentDocument.createElement('div');
        instructions.className = 'edit-mode-instructions';
        instructions.textContent = '✏️ Режим редактирования: кликните на элемент для редактирования';
        iframe.contentDocument.body.appendChild(instructions);
    }
    
    removeEditModeInstructions() {
        const iframe = this.previewIframe;
        if (!iframe || !iframe.contentDocument) return;
        
        const instructions = iframe.contentDocument.querySelector('.edit-mode-instructions');
        if (instructions) {
            instructions.remove();
        }
    }
    
    makeElementsEditable() {
        const iframe = this.previewIframe;
        if (!iframe || !iframe.contentDocument) return;
        
        const doc = iframe.contentDocument;
        
        // Find editable elements (headings, paragraphs, buttons, etc.)
        const editableSelectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'span', 'div[class*="title"]', 'div[class*="subtitle"]',
            'button', 'a', 'li', 'td', 'th'
        ];
        
        this.editableElements = [];
        
        editableSelectors.forEach(selector => {
            const elements = doc.querySelectorAll(selector);
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
        const tagName = element.tagName.toLowerCase();
        
        const labels = {
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
        const elementType = this.getElementLabel(element);
        const currentText = element.textContent.trim();
        
        // Remove previous edit prompts
        const existingEditPrompts = this.chatMessages.querySelectorAll('.edit-prompt-message');
        existingEditPrompts.forEach(prompt => prompt.remove());
        
        // Add message to chat
        const messageDiv = document.createElement('div');
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
        const iframe = this.previewIframe;
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
        const containerRect = this.chatPanel.parentElement.getBoundingClientRect();
        const chatRect = this.chatPanel.getBoundingClientRect();
        
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
        
        const deltaX = e.clientX - this.startX;
        const newChatWidth = this.startChatWidth + deltaX;
        
        // Calculate percentage
        const chatPercentage = (newChatWidth / this.containerWidth) * 100;
        const previewPercentage = 100 - chatPercentage;
        
        // Apply constraints
        const minChatPercentage = 25; // Minimum 25% for chat
        const maxChatPercentage = 75; // Maximum 75% for chat
        
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
        const chatPercentage = (this.chatPanel.offsetWidth / this.chatPanel.parentElement.offsetWidth) * 100;
        localStorage.setItem('windexai_chat_panel_size', chatPercentage.toString());
    }
    
    loadPanelSizes() {
        const savedSize = localStorage.getItem('windexai_chat_panel_size');
        if (savedSize) {
            const chatPercentage = parseFloat(savedSize);
            const previewPercentage = 100 - chatPercentage;
            
            // Apply constraints
            const minChatPercentage = 25;
            const maxChatPercentage = 75;
            
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
        
        const element = this.selectedElement;
        const elementType = element.getAttribute('data-element-type');
        const currentText = element.textContent.trim();
        
        // Add user message to chat
        this.addChatMessage('user', editInstruction);
        
        // Create edit request
        const editRequest = {
            element_type: elementType,
            current_text: currentText,
            edit_instruction: editInstruction,
            html_content: this.previewIframe.srcdoc
        };
        
        try {
            const token = localStorage.getItem('windexai_token');
            if (!token) {
                this.showError('Необходима авторизация');
                return;
            }
            
            this.startGeneration();
            
            const response = await fetch('/api/ai-editor/edit-element', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(editRequest)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка при редактировании элемента');
            }
            
            const result = await response.json();
            
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
            const token = localStorage.getItem('windexai_token');
            if (!token) return;

            const response = await fetch('/api/ai-editor/conversations', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
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
            const convElement = document.createElement('div');
            convElement.className = 'conversation-item';
            if (conv.id === this.currentConversationId) {
                convElement.classList.add('active');
            }

            const date = new Date(conv.date).toLocaleDateString('ru-RU', {
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
            const token = localStorage.getItem('windexai_token');
            if (!token) return;

            const response = await fetch(`/api/ai-editor/conversations/${conversationId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
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
            const token = localStorage.getItem('windexai_token');
            if (!token) return;

            const response = await fetch('/api/ai-editor/conversations', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
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
            const token = localStorage.getItem('windexai_token');
            if (!token) return;

            const response = await fetch(`/api/ai-editor/conversations/${conversationId}`, {
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
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.aiEditor = new AIEditor();
});