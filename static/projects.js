// JavaScript для страницы управления проектами
class ProjectsManager {
    constructor() {
        this.authToken = localStorage.getItem('windexai_token');
        this.projects = [];
        this.init();
    }

    init() {
        this.checkAuth();
        this.bindEvents();
        this.loadProjects();
    }

    checkAuth() {
        if (!this.authToken) {
            window.location.href = '/';
            return;
        }
    }

    bindEvents() {
        // Кнопка создания нового проекта
        const newProjectBtns = document.querySelectorAll('#new-project-btn, .new-project-btn');
        newProjectBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                window.location.href = '/static/editor.html';
            });
        });

        // User info click handlers
        const userAvatar = document.getElementById('user-avatar');
        const userName = document.getElementById('user-name');
        const profileModal = document.getElementById('profile-modal');
        const closeProfileBtn = document.querySelector('.close-profile');

        if (userAvatar) {
            userAvatar.addEventListener('click', () => {
                this.showProfileModal();
            });
        }

        if (userName) {
            userName.addEventListener('click', () => {
                this.showProfileModal();
            });
        }

        if (closeProfileBtn) {
            closeProfileBtn.addEventListener('click', () => {
                this.hideProfileModal();
            });
        }

        // Модальное окно удаления
        const deleteModal = document.getElementById('delete-modal');
        const closeModal = deleteModal.querySelector('.close');
        const cancelBtn = deleteModal.querySelector('.btn-outline');
        const confirmDeleteBtn = document.getElementById('confirm-delete');

        closeModal.addEventListener('click', () => {
            deleteModal.style.display = 'none';
        });

        cancelBtn.addEventListener('click', () => {
            deleteModal.style.display = 'none';
        });

        window.addEventListener('click', (e) => {
            if (e.target === deleteModal) {
                deleteModal.style.display = 'none';
            }
        });
    }

    async loadProjects() {
        try {
            const response = await fetch('/api/ai-editor/conversations', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.projects = data.conversations || [];
                this.renderProjects();
            } else {
                throw new Error('Ошибка загрузки проектов');
            }
        } catch (error) {
            console.error('Error loading projects:', error);
            this.showError('Не удалось загрузить проекты');
        }
    }

    renderProjects() {
        const projectsGrid = document.getElementById('projects-grid');
        const emptyState = document.getElementById('empty-state');
        const projectsCount = document.getElementById('projects-count');

        if (this.projects.length === 0) {
            projectsGrid.style.display = 'none';
            emptyState.style.display = 'block';
            projectsCount.textContent = 'Нет проектов';
            return;
        }

        projectsGrid.style.display = 'grid';
        emptyState.style.display = 'none';
        projectsCount.textContent = `Проектов: ${this.projects.length}`;

        projectsGrid.innerHTML = this.projects.map(project => this.createProjectCard(project)).join('');

        // Привязываем события к карточкам проектов
        this.bindProjectEvents();
    }

    createProjectCard(project) {
        const date = new Date(project.date).toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });

        const preview = project.preview.length > 150
            ? project.preview.substring(0, 150) + '...'
            : project.preview;

        return `
            <div class="project-card" data-project-id="${project.id}">
                <div class="project-header">
                    <h3 class="project-title">${project.title}</h3>
                    <span class="project-date">${date}</span>
                </div>
                <div class="project-preview">${preview}</div>
                <div class="project-stats">
                    <span>💬 ${project.message_count} сообщений</span>
                    <span>📁 Next.js проект</span>
                </div>
                <div class="project-actions">
                    <a href="/static/editor.html?project=${project.id}" class="project-btn primary">
                        Открыть
                    </a>
                    <button class="project-btn secondary" onclick="projectsManager.downloadProject(${project.id})">
                        📥 Скачать
                    </button>
                    <button class="project-btn danger" onclick="projectsManager.confirmDelete(${project.id}, '${project.title.replace(/'/g, "\\'")}')">
                        🗑️
                    </button>
                </div>
            </div>
        `;
    }

    bindProjectEvents() {
        // События уже привязаны через onclick в HTML
    }

    confirmDelete(projectId, projectTitle) {
        const modal = document.getElementById('delete-modal');
        const projectNameSpan = document.getElementById('delete-project-name');
        const confirmBtn = document.getElementById('confirm-delete');

        projectNameSpan.textContent = projectTitle;
        modal.style.display = 'flex';

        // Удаляем предыдущие обработчики
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

        // Добавляем новый обработчик
        newConfirmBtn.addEventListener('click', () => {
            this.deleteProject(projectId);
            modal.style.display = 'none';
        });
    }

    async deleteProject(projectId) {
        try {
            const response = await fetch(`/api/ai-editor/conversations/${projectId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                this.showSuccess('Проект успешно удален');
                this.loadProjects(); // Перезагружаем список
            } else {
                throw new Error('Ошибка удаления проекта');
            }
        } catch (error) {
            console.error('Error deleting project:', error);
            this.showError('Не удалось удалить проект');
        }
    }

    async downloadProject(projectId) {
        try {
            const response = await fetch(`/api/ai-editor/conversations/${projectId}`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                const conversation = data.conversation;

                // Находим последнее сообщение AI с проектом
                const aiMessages = conversation.messages.filter(msg => msg.role === 'assistant');
                const lastAiMessage = aiMessages[aiMessages.length - 1];

                if (lastAiMessage && lastAiMessage.content) {
                    this.downloadProjectFiles(lastAiMessage.content, conversation.title);
                } else {
                    this.showError('Не найдены файлы проекта');
                }
            } else {
                throw new Error('Ошибка загрузки проекта');
            }
        } catch (error) {
            console.error('Error downloading project:', error);
            this.showError('Не удалось скачать проект');
        }
    }

    downloadProjectFiles(content, projectTitle) {
        // Парсим файлы из содержимого
        const files = this.parseProjectFiles(content);

        if (Object.keys(files).length === 0) {
            this.showError('Не найдены файлы для скачивания');
            return;
        }

        // Скачиваем каждый файл
        Object.keys(files).forEach((filePath, index) => {
            setTimeout(() => {
                const blob = new Blob([files[filePath]], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filePath.split('/').pop();
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, index * 100);
        });

        this.showSuccess(`Скачивание ${Object.keys(files).length} файлов начато`);
    }

    parseProjectFiles(content) {
        const files = {};

        // Парсим файлы Next.js
        const patterns = [
            { key: 'package.json', regex: /PACKAGE_JSON_START([\s\S]*?)PACKAGE_JSON_END/ },
            { key: 'tsconfig.json', regex: /TSCONFIG_START([\s\S]*?)TSCONFIG_END/ },
            { key: 'tailwind.config.js', regex: /TAILWIND_CONFIG_START([\s\S]*?)TAILWIND_CONFIG_END/ },
            { key: 'next.config.js', regex: /NEXT_CONFIG_START([\s\S]*?)NEXT_CONFIG_END/ },
            { key: 'app/layout.tsx', regex: /LAYOUT_TSX_START([\s\S]*?)LAYOUT_TSX_END/ },
            { key: 'app/page.tsx', regex: /PAGE_TSX_START([\s\S]*?)PAGE_TSX_END/ },
            { key: 'app/globals.css', regex: /GLOBALS_CSS_START([\s\S]*?)GLOBALS_CSS_END/ }
        ];

        patterns.forEach(pattern => {
            const match = content.match(pattern.regex);
            if (match) {
                files[pattern.key] = match[1].trim();
            }
        });

        // Парсим компоненты
        const componentPatterns = [
            { key: 'app/components/sections/Hero.tsx', regex: /HERO_COMPONENT_START([\s\S]*?)HERO_COMPONENT_END/ },
            { key: 'app/components/sections/Features.tsx', regex: /FEATURES_COMPONENT_START([\s\S]*?)FEATURES_COMPONENT_END/ },
            { key: 'app/components/sections/Footer.tsx', regex: /FOOTER_COMPONENT_START([\s\S]*?)FOOTER_COMPONENT_END/ },
            { key: 'app/components/ui/Button.tsx', regex: /BUTTON_COMPONENT_START([\s\S]*?)BUTTON_COMPONENT_END/ },
            { key: 'app/components/ui/Card.tsx', regex: /CARD_COMPONENT_START([\s\S]*?)CARD_COMPONENT_END/ },
            { key: 'app/components/ui/Container.tsx', regex: /CONTAINER_COMPONENT_START([\s\S]*?)CONTAINER_COMPONENT_END/ }
        ];

        componentPatterns.forEach(pattern => {
            const match = content.match(pattern.regex);
            if (match) {
                files[pattern.key] = match[1].trim();
            }
        });

        return files;
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        // Создаем простое уведомление
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 2rem;
            right: 2rem;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            transition: all 0.3s ease;
            ${type === 'success' ? 'background: #10b981;' : 'background: #ef4444;'}
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    showProfileModal() {
        const profileModal = document.getElementById('profile-modal');
        if (profileModal) {
            // Populate profile data
            const usernameSpan = document.getElementById('profile-username');
            const emailSpan = document.getElementById('profile-email');
            if (this.user) {
                if (usernameSpan) usernameSpan.textContent = this.user.username;
                if (emailSpan) emailSpan.textContent = this.user.email;
            }
            profileModal.classList.remove('hidden');
        }
    }

    hideProfileModal() {
        const profileModal = document.getElementById('profile-modal');
        if (profileModal) {
            profileModal.classList.add('hidden');
        }
    }
}

// Инициализация при загрузке страницы
let projectsManager;
document.addEventListener('DOMContentLoaded', () => {
    projectsManager = new ProjectsManager();
});
