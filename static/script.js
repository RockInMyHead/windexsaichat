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

    async login(username, password) {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
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
        this.currentModel = 'windexai-lite';
        this.isLoading = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadConversations();
        this.initializeTheme();
        
        // Debug: Check if theme toggle button is found
        console.log('Theme toggle button:', this.themeToggle);
    }

    initializeElements() {
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.chatContainer = document.getElementById('chat-container');
        this.conversationsList = document.getElementById('conversations-list');
        this.newChatBtn = document.getElementById('new-chat-btn');
        this.clearHistoryBtn = document.getElementById('clear-history-btn');
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.charCount = document.querySelector('.char-count');
        this.modelCards = document.querySelectorAll('.model-card');
        this.themeToggle = document.getElementById('theme-toggle');
        
        // Debug: Check if all elements are found
        console.log('Elements found:', {
            messageInput: !!this.messageInput,
            sendBtn: !!this.sendBtn,
            chatContainer: !!this.chatContainer,
            conversationsList: !!this.conversationsList,
            newChatBtn: !!this.newChatBtn,
            clearHistoryBtn: !!this.clearHistoryBtn,
            loadingOverlay: !!this.loadingOverlay,
            charCount: !!this.charCount,
            modelCards: this.modelCards.length,
            themeToggle: !!this.themeToggle
        });
    }

    bindEvents() {
        // Message input
        this.messageInput.addEventListener('input', () => {
            this.updateCharCount();
            this.toggleSendButton();
            this.autoResize();
        });

        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Send button
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        // New chat button
        this.newChatBtn.addEventListener('click', () => {
            this.startNewChat();
        });

        // Clear history button
        this.clearHistoryBtn.addEventListener('click', () => {
            this.clearHistory();
        });

        // Theme toggle button
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', () => {
                console.log('Theme toggle clicked');
                this.toggleTheme();
            });
            console.log('Theme toggle event listener added');
        } else {
            console.error('Theme toggle button not found!');
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;

        this.isLoading = true;
        this.showLoading();

        // Hide welcome message if it's showing
        this.hideWelcomeMessage();

        // Add user message to chat
        this.addMessageToChat('user', message);
        this.messageInput.value = '';
        this.updateCharCount();
        this.toggleSendButton();

        // Show typing indicator
        const typingIndicator = this.showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: this.authManager.getAuthHeaders(),
                body: JSON.stringify({
                    message: message,
                    model: this.currentModel,
                    conversation_id: this.currentConversationId
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
            this.hideTypingIndicator(typingIndicator);
            this.addMessageToChat('assistant', data.response);

            // Update conversations list
            this.loadConversations();

        } catch (error) {
            console.error('Error:', error);
            this.hideTypingIndicator(typingIndicator);
            this.addMessageToChat('assistant', 'Извините, произошла ошибка. Попробуйте еще раз.');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role} fade-in`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? 'Вы' : '🤖';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = content;

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

        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    typeText(text) {
        // Simple text display for now - typing effect can be added later
        return text;
    }

    showTypingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant fade-in';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '🤖';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;

        messageContent.appendChild(typingIndicator);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);

        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        return messageDiv;
    }

    hideTypingIndicator(typingElement) {
        if (typingElement && typingElement.parentElement) {
            typingElement.remove();
        }
    }

    toggleTheme() {
        const body = document.body;
        const isDark = body.classList.contains('dark-theme');
        
        console.log('Current theme:', isDark ? 'dark' : 'light');
        
        if (isDark) {
            body.classList.remove('dark-theme');
            localStorage.setItem('windexai_theme', 'light');
            console.log('Switched to light theme');
        } else {
            body.classList.add('dark-theme');
            localStorage.setItem('windexai_theme', 'dark');
            console.log('Switched to dark theme');
        }
        
        // Update button icon
        this.updateThemeButtonIcon();
    }

    updateThemeButtonIcon() {
        if (!this.themeToggle) return;
        
        const isDark = document.body.classList.contains('dark-theme');
        const icon = this.themeToggle.querySelector('svg');
        
        if (isDark) {
            // Dark theme - show sun icon
            icon.innerHTML = `
                <circle cx="12" cy="12" r="5"></circle>
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"></path>
            `;
        } else {
            // Light theme - show moon icon
            icon.innerHTML = `
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            `;
        }
    }

    initializeTheme() {
        const savedTheme = localStorage.getItem('windexai_theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        console.log('Saved theme:', savedTheme);
        console.log('Prefers dark:', prefersDark);
        
        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
            document.body.classList.add('dark-theme');
            console.log('Applied dark theme');
        } else {
            document.body.classList.remove('dark-theme');
            console.log('Applied light theme');
        }
        
        // Update button icon after theme is set
        setTimeout(() => {
            this.updateThemeButtonIcon();
        }, 100);
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
            if (conv.id === this.currentConversationId) {
                convElement.classList.add('active');
            }

            const title = document.createElement('div');
            title.className = 'conversation-title';
            title.textContent = conv.title || 'Новый чат';

            const date = document.createElement('div');
            date.className = 'conversation-date';
            date.textContent = new Date(conv.timestamp).toLocaleDateString('ru-RU');

            convElement.appendChild(title);
            convElement.appendChild(date);

            convElement.addEventListener('click', () => {
                this.loadConversation(conv.id);
            });

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
        this.chatContainer.innerHTML = '';
        
        if (conversation.messages && conversation.messages.length > 0) {
            conversation.messages.forEach(message => {
                this.addMessageToChat(message.role, message.content);
            });
        } else {
            this.showWelcomeMessage();
        }
        
        this.scrollToBottom();
    }

    startNewChat() {
        this.currentConversationId = null;
        this.chatContainer.innerHTML = '';
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

    showWelcomeMessage() {
        const welcomeMessage = document.createElement('div');
        welcomeMessage.className = 'welcome-message';
        welcomeMessage.innerHTML = `
            <div class="welcome-icon">🚀</div>
            <h2>Добро пожаловать в WIndexAI</h2>
            <p>Выберите модель и начните общение с искусственным интеллектом</p>
            <div class="model-cards">
                <div class="model-card" data-model="windexai-lite">
                    <h3>WIndexAI Lite</h3>
                    <p>Быстрая и эффективная модель для повседневных задач</p>
                    <div class="capabilities">
                        <span class="capability">Текст</span>
                        <span class="capability">Код</span>
                        <span class="capability">Анализ</span>
                        <span class="capability">Перевод</span>
                    </div>
                </div>
                <div class="model-card" data-model="windexai-pro">
                    <h3>WIndexAI Pro</h3>
                    <p>Продвинутая модель с расширенными возможностями</p>
                    <div class="capabilities">
                        <span class="capability">Текст</span>
                        <span class="capability">Код</span>
                        <span class="capability">Анализ</span>
                        <span class="capability">Перевод</span>
                        <span class="capability">Креативность</span>
                        <span class="capability">Логика</span>
                    </div>
                </div>
            </div>
        `;
        this.chatContainer.appendChild(welcomeMessage);

        // Re-bind model card events
        this.modelCards = document.querySelectorAll('.model-card');
        this.modelCards.forEach(card => {
            card.addEventListener('click', () => {
                const model = card.dataset.model;
                this.modelSelect.value = model;
                this.currentModel = model;
                this.updateModelInfo();
                this.hideWelcomeMessage();
            });
        });
    }

    hideWelcomeMessage() {
        const welcomeMessage = this.chatContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
    }


    updateCharCount() {
        const count = this.messageInput.value.length;
        this.charCount.textContent = `${count}/4000`;
        
        if (count > 3500) {
            this.charCount.style.color = 'var(--primary-green)';
        } else {
            this.charCount.style.color = 'var(--gray-500)';
        }
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
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    showLoading() {
        // Simple loading indicator - disable send button and show loading state
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
        // Restore send button
        this.sendBtn.disabled = false;
        this.sendBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22,2 15,22 11,13 2,9 22,2"></polygon>
            </svg>
        `;
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

    // Show register form
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

    // Show login form
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

    // Handle login
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        const submitBtn = loginForm.querySelector('.auth-btn');
        
        // Show loading state
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Вход...';
        
        try {
            await authManager.login(username, password);
        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            // Restore button state
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });

    // Handle registration
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        const submitBtn = registerForm.querySelector('.auth-btn');
        
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

