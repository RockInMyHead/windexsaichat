class AIEditor {
    constructor() {
        this.conversationHistory = [];
        this.currentGeneration = null;
        this.initializeElements();
        this.setupEventListeners();
        this.checkAuth();
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

        console.log('Elements initialized');
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
        
        // Load saved panel sizes
        this.loadPanelSizes();

        console.log('Event listeners set up');
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

        console.log('Sending message:', message);

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
                    model: 'gpt-4o-mini'
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Response data:', data);

            if (data.error) {
                throw new Error(data.error);
            }

            const content = data.content || 'Ответ получен без содержания';
            
            // Добавляем ответ AI
            this.conversationHistory.push({role: 'assistant', content: content});
            
            // Извлекаем описание для чата
            const description = this.extractDescription(content);
            this.addChatMessage('assistant', description);
            
            // Обновляем превью
            this.updatePreview(content);
            
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
        
        console.log('Updating preview with content:', content.substring(0, 200) + '...');
        
        // Извлекаем HTML между маркерами
        const htmlMatch = content.match(/NEW_PAGE_START([\s\S]*?)NEW_PAGE_END/);
        if (htmlMatch) {
            const html = htmlMatch[1].trim();
            this.previewIframe.srcdoc = html;
            console.log('Preview updated with HTML:', html.substring(0, 200) + '...');
        } else {
            // Пробуем найти HTML код без маркеров (fallback)
            const htmlCodeMatch = content.match(/```html([\s\S]*?)```/);
            if (htmlCodeMatch) {
                const html = htmlCodeMatch[1].trim();
                this.previewIframe.srcdoc = html;
                console.log('Preview updated with fallback HTML');
            } else {
                console.log('No HTML found in content');
            }
        }
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
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing AI Editor');
    new AIEditor();
});