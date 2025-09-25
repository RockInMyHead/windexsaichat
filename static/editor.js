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
        this.logoutBtn = document.getElementById('logout-btn');
        this.userNameSpan = document.getElementById('user-name');
        
        // Modal elements
        this.deployModal = document.getElementById('deploy-modal');
        this.deployTitle = document.getElementById('deploy-title');
        this.deployDescription = document.getElementById('deploy-description');
        this.deployStatus = document.getElementById('deploy-status');
        this.confirmDeployBtn = document.getElementById('confirm-deploy');
        this.cancelDeployBtn = document.getElementById('cancel-deploy');
        this.closeModalBtn = document.querySelector('.close');

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
    }
    
    showDeployStatus(message, type = 'loading') {
        this.deployStatus.style.display = 'block';
        this.deployStatus.className = `deploy-status ${type}`;
        this.deployStatus.querySelector('.status-message').textContent = message;
    }
    
    hideDeployStatus() {
        this.deployStatus.style.display = 'none';
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
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка при деплое');
            }
            
            const result = await response.json();
            
            this.showDeployStatus(
                `✅ Сайт успешно задеплоен!\nURL: ${result.full_url}`,
                'success'
            );
            
            // Show success message with link
            setTimeout(() => {
                const openLink = confirm(
                    `Сайт "${result.title}" успешно задеплоен!\n\n` +
                    `URL: ${result.full_url}\n\n` +
                    `Открыть сайт в новой вкладке?`
                );
                
                if (openLink) {
                    window.open(result.full_url, '_blank');
                }
                
                this.hideDeployModal();
            }, 2000);
            
        } catch (error) {
            console.error('Deploy error:', error);
            this.showDeployStatus(`❌ Ошибка: ${error.message}`, 'error');
        } finally {
            this.confirmDeployBtn.disabled = false;
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing AI Editor');
    new AIEditor();
});