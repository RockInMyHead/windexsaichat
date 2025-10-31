class DashboardManager {
    constructor() {
        this.currentUser = null;
        this.profileData = null;
        this.statsData = null;
        this.activityChart = null;
        this.init();
    }

    async init() {
        this.setupEventListeners();

        // Проверяем, была ли активирована подписка
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('subscription_activated') === 'pro') {
            // Очищаем URL параметр
            window.history.replaceState(null, null, window.location.pathname);
            // Показываем уведомление об успешной активации
            this.showSuccess('Pro подписка успешно активирована!');
        }

        await this.loadUserData();
        await this.loadProfileData();
        await this.loadStatsData();
        await this.loadRecentActivity();
        await this.loadDeployedSites();
        this.initializeChart();
        this.setupQuickActions();
    }

    setupEventListeners() {
        // Edit profile button
        document.getElementById('edit-profile-btn').addEventListener('click', () => {
            this.openEditModal();
        });

        // Profile settings form
        document.getElementById('profile-settings-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateProfile();
        });

        // Password settings form
        document.getElementById('password-settings-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.changePassword();
        });

        // Delete account button
        document.getElementById('delete-account-btn').addEventListener('click', () => {
            this.openDeleteModal();
        });

        // Quick action buttons
        document.getElementById('quick-chat-btn').addEventListener('click', () => {
            window.location.href = '/';
        });

        document.getElementById('create-project-btn').addEventListener('click', () => {
            window.location.href = '/editor.html';
        });

        // Chart period buttons
        document.querySelectorAll('.chart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchChartPeriod(e.target.dataset.period);
            });
        });

        // Modal events
        this.setupModalEvents();

        // Logout button
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.logout();
        });
    }

    setupModalEvents() {
        // Edit profile modal
        document.getElementById('close-edit-modal').addEventListener('click', () => {
            this.closeModal('edit-profile-modal');
        });

        document.getElementById('cancel-edit').addEventListener('click', () => {
            this.closeModal('edit-profile-modal');
        });

        document.getElementById('save-edit').addEventListener('click', () => {
            this.saveProfileChanges();
        });

        // Delete confirmation modal
        document.getElementById('close-delete-modal').addEventListener('click', () => {
            this.closeModal('delete-confirm-modal');
        });

        document.getElementById('cancel-delete').addEventListener('click', () => {
            this.closeModal('delete-confirm-modal');
        });

        document.getElementById('confirm-delete').addEventListener('input', (e) => {
            const confirmBtn = document.getElementById('confirm-delete-btn');
            confirmBtn.disabled = e.target.value !== 'УДАЛИТЬ';
        });

        document.getElementById('confirm-delete-btn').addEventListener('click', () => {
            this.deleteAccount();
        });

        // Close modals on outside click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }

    setupQuickActions() {
        // Quick action buttons
        document.getElementById('new-chat-action').addEventListener('click', () => {
            window.location.href = '/';
        });

        document.getElementById('upload-doc-action').addEventListener('click', () => {
            // TODO: Implement document upload
            this.showInfo('Функция загрузки документов будет добавлена в следующем обновлении');
        });

        document.getElementById('create-project-action').addEventListener('click', () => {
            window.location.href = '/editor.html';
        });

        document.getElementById('view-analytics-action').addEventListener('click', () => {
            this.scrollToElement('.analytics-card');
        });

        // Upgrade button
        document.getElementById('upgrade-btn').addEventListener('click', () => {
            this.showInfo('Функция обновления подписки будет добавлена в следующем обновлении');
        });

        // Site action buttons (event delegation)
        document.getElementById('sites-grid').addEventListener('click', (e) => {
            const button = e.target.closest('.site-btn');
            if (!button) return;

            e.preventDefault();

            if (button.classList.contains('site-btn-outline') && button.textContent.includes('Открыть')) {
                const url = button.getAttribute('onclick').match(/'([^']+)'/)[1];
                window.open(url, '_blank');
            } else if (button.classList.contains('site-btn-primary')) {
                // Edit button
                const siteId = parseInt(button.getAttribute('onclick').match(/this\.editSite\((\d+)\)/)[1]);
                this.editSite(siteId);
            } else if (button.classList.contains('site-btn-danger')) {
                // Delete button
                const siteId = parseInt(button.getAttribute('onclick').match(/this\.deleteSite\((\d+)\)/)[1]);
                this.deleteSite(siteId);
            }
        });
    }

    async loadUserData() {
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

            if (response.ok) {
                this.currentUser = await response.json();
                this.updateUserInfo();
            } else {
                localStorage.removeItem('windexai_token');
                window.location.href = '/';
            }
        } catch (error) {
            console.error('Error loading user data:', error);
            this.showError('Ошибка загрузки данных пользователя');
        }
    }

    async loadProfileData() {
        try {
            const token = localStorage.getItem('windexai_token');
            const response = await fetch('/api/profile/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                this.profileData = await response.json();
                this.updateProfileInfo();
                this.updateUsageStats();
            }
        } catch (error) {
            console.error('Error loading profile data:', error);
        }
    }

    async loadStatsData() {
        try {
            const token = localStorage.getItem('windexai_token');
            const response = await fetch('/api/profile/stats', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                this.statsData = await response.json();
                this.updateStats();
            }
        } catch (error) {
            console.error('Error loading stats data:', error);
        }
    }

    async loadRecentActivity() {
        try {
            const token = localStorage.getItem('windexai_token');
            const response = await fetch('/api/profile/recent-activity', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const activityData = await response.json();
                this.updateActivityTimeline(activityData);
            }
        } catch (error) {
            console.error('Error loading recent activity:', error);
        }
    }

    async loadDeployedSites() {
        try {
            const token = localStorage.getItem('windexai_token');
            const response = await fetch('/api/deploy/', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const sitesData = await response.json();
                this.updateSitesGrid(sitesData);
            } else {
                this.updateSitesGrid([]);
            }
        } catch (error) {
            console.error('Error loading deployed sites:', error);
            this.updateSitesGrid([]);
        }
    }

    updateUserInfo() {
        if (this.currentUser) {
            document.getElementById('user-name').textContent = this.currentUser.username;
            document.getElementById('profile-name').textContent = this.currentUser.username;
            document.getElementById('profile-email').textContent = this.currentUser.email;
            
            // Update avatar
            const avatar = document.getElementById('user-avatar');
            avatar.innerHTML = `<i class="fas fa-user"></i>`;
        }
    }

    updateProfileInfo() {
        if (this.profileData) {
            // Update stats cards
            document.getElementById('total-conversations').textContent = this.profileData.total_conversations;
            document.getElementById('total-messages').textContent = this.profileData.total_messages;
            document.getElementById('total-documents').textContent = this.profileData.total_documents;
            document.getElementById('total-deployments').textContent = this.profileData.total_deployments;

            // Update subscription badge
            const badge = document.getElementById('subscription-badge');
            badge.textContent = this.profileData.subscription_plan === 'pro' ? 'Pro' : 'Free';
            badge.className = `badge ${this.profileData.subscription_plan === 'pro' ? 'badge-pro' : 'badge-free'}`;

            // Update member since
            const memberSince = document.getElementById('member-since');
            const joinDate = new Date(this.profileData.created_at);
            memberSince.textContent = `Участник с ${joinDate.getFullYear()}`;

            // Update last activity
            const lastActivity = document.getElementById('last-activity');
            if (this.profileData.last_activity) {
                const activityDate = new Date(this.profileData.last_activity);
                lastActivity.textContent = this.formatDate(activityDate);
            } else {
                lastActivity.textContent = 'Никогда';
            }

            // Update join date
            const joinDateElement = document.getElementById('join-date');
            joinDateElement.textContent = this.formatDate(joinDate);

            // Update subscription info
            this.updateSubscriptionInfo();
        }
    }

    updateStats() {
        if (this.statsData) {
            // Update monthly stats
            document.getElementById('messages-this-month').textContent = this.statsData.messages_this_month;
            document.getElementById('conversations-this-month').textContent = this.statsData.conversations_this_month;

            // Update usage stats
            this.updateUsageStats();
        }
    }

    updateUsageStats() {
        if (this.profileData && this.statsData) {
            // Messages usage
            const messagesUsage = Math.min((this.statsData.messages_this_month / 1000) * 100, 100);
            document.getElementById('messages-usage').style.width = `${messagesUsage}%`;
            document.getElementById('messages-usage-text').textContent = 
                `${this.statsData.messages_this_month} / 1000`;

            // Documents usage
            const documentsUsage = Math.min((this.profileData.total_documents / 10) * 100, 100);
            document.getElementById('documents-usage').style.width = `${documentsUsage}%`;
            document.getElementById('documents-usage-text').textContent = 
                `${this.profileData.total_documents} / 10`;

            // Deployments usage
            const deploymentsUsage = Math.min((this.profileData.total_deployments / 5) * 100, 100);
            document.getElementById('deployments-usage').style.width = `${deploymentsUsage}%`;
            document.getElementById('deployments-usage-text').textContent = 
                `${this.profileData.total_deployments} / 5`;
        }
    }

    updateSubscriptionInfo() {
        if (this.profileData) {
            const statusElement = document.getElementById('subscription-status');
            const planNameElement = document.getElementById('current-plan-name');
            const planDescriptionElement = document.getElementById('plan-description');

            if (this.profileData.subscription_plan === 'pro') {
                statusElement.textContent = 'Pro';
                statusElement.className = 'subscription-status pro';
                planNameElement.textContent = 'Pro Plan';
                planDescriptionElement.textContent = 'Расширенные возможности для профессионалов';
            } else {
                statusElement.textContent = 'Free';
                statusElement.className = 'subscription-status free';
                planNameElement.textContent = 'Free Plan';
                planDescriptionElement.textContent = 'Базовые возможности для начала работы';
            }
        }
    }

    updateActivityTimeline(activityData) {
        const timelineContainer = document.getElementById('activity-timeline');
        const activities = [];

        // Add recent conversations
        activityData.recent_conversations.slice(0, 3).forEach(conv => {
            activities.push({
                type: 'conversation',
                title: conv.title,
                description: `${conv.message_count} сообщений`,
                time: conv.updated_at,
                icon: 'fas fa-comments'
            });
        });

        // Add recent documents
        activityData.recent_documents.slice(0, 2).forEach(doc => {
            activities.push({
                type: 'document',
                title: doc.filename,
                description: `${doc.file_type.toUpperCase()} • ${this.formatFileSize(doc.file_size)}`,
                time: doc.upload_date,
                icon: 'fas fa-file-alt'
            });
        });

        // Add recent deployments
        activityData.recent_deployments.slice(0, 2).forEach(dep => {
            activities.push({
                type: 'deployment',
                title: dep.name,
                description: `Статус: ${dep.status}`,
                time: dep.created_at,
                icon: 'fas fa-rocket'
            });
        });

        // Sort by time
        activities.sort((a, b) => new Date(b.time) - new Date(a.time));

        if (activities.length > 0) {
            timelineContainer.innerHTML = activities.map(activity => `
                <div class="timeline-item">
                    <div class="timeline-icon">
                        <i class="${activity.icon}"></i>
                    </div>
                    <div class="timeline-content">
                        <h5>${activity.title}</h5>
                        <p>${activity.description}</p>
                        <span class="timeline-time">${this.formatDate(new Date(activity.time))}</span>
                    </div>
                </div>
            `).join('');
        } else {
            timelineContainer.innerHTML = '<div class="no-activity">Нет недавней активности</div>';
        }
    }

    updateSitesGrid(sitesData) {
        const sitesGrid = document.getElementById('sites-grid');

        if (!sitesData || sitesData.length === 0) {
            sitesGrid.innerHTML = `
                <div class="no-sites">
                    <i class="fas fa-globe"></i>
                    <h3>У вас пока нет созданных сайтов</h3>
                    <p>Создайте свой первый сайт в AI редакторе</p>
                    <button class="create-site-btn" onclick="window.location.href='/editor.html'">
                        <i class="fas fa-plus"></i>
                        Создать сайт
                    </button>
                </div>
            `;
            return;
        }

        sitesGrid.innerHTML = sitesData.map(site => `
            <div class="site-card">
                <div class="site-header">
                    <h3>${site.title}</h3>
                    <span class="site-status ${site.is_active ? 'active' : 'inactive'}">
                        ${site.is_active ? 'Активен' : 'Неактивен'}
                    </span>
                </div>
                <div class="site-preview">
                    <iframe src="/deploy/${site.deploy_url}" onload="this.style.opacity='1'" style="opacity: 0; transition: opacity 0.3s;"></iframe>
                </div>
                <div class="site-content">
                    <div class="site-description">
                        ${site.description || 'Описание не указано'}
                    </div>
                    <div class="site-meta">
                        <span>Создан: ${this.formatDate(new Date(site.created_at))}</span>
                        <a href="/deploy/${site.deploy_url}" target="_blank" class="site-url">
                            ${site.deploy_url}
                        </a>
                    </div>
                    <div class="site-actions">
                        <button class="site-btn site-btn-outline" onclick="window.open('/deploy/${site.deploy_url}', '_blank')">
                            <i class="fas fa-external-link-alt"></i>
                            Открыть
                        </button>
                        <button class="site-btn site-btn-primary" onclick="this.editSite(${site.id})">
                            <i class="fas fa-edit"></i>
                            Редактировать
                        </button>
                        <button class="site-btn site-btn-danger" onclick="this.deleteSite(${site.id})">
                            <i class="fas fa-trash"></i>
                            Удалить
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    initializeChart() {
        const ctx = document.getElementById('activity-chart').getContext('2d');
        
        // Generate sample data for the last 7 days
        const labels = [];
        const messagesData = [];
        const conversationsData = [];

        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('ru-RU', { weekday: 'short' }));
            
            // Generate random data (in real app, this would come from API)
            messagesData.push(Math.floor(Math.random() * 50) + 10);
            conversationsData.push(Math.floor(Math.random() * 10) + 1);
        }

        this.activityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Сообщения',
                    data: messagesData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true
                }, {
                    label: 'Разговоры',
                    data: conversationsData,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    switchChartPeriod(period) {
        // Update active button
        document.querySelectorAll('.chart-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-period="${period}"]`).classList.add('active');

        // Update chart data
        const labels = [];
        const messagesData = [];
        const conversationsData = [];
        
        for (let i = period - 1; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('ru-RU', { 
                month: 'short', 
                day: 'numeric' 
            }));
            
            // Generate random data
            messagesData.push(Math.floor(Math.random() * 50) + 10);
            conversationsData.push(Math.floor(Math.random() * 10) + 1);
        }

        this.activityChart.data.labels = labels;
        this.activityChart.data.datasets[0].data = messagesData;
        this.activityChart.data.datasets[1].data = conversationsData;
        this.activityChart.update();
    }

    openEditModal() {
        if (this.profileData) {
            document.getElementById('edit-username').value = this.profileData.username;
            document.getElementById('edit-email').value = this.profileData.email;
        }
        this.openModal('edit-profile-modal');
    }

    async saveProfileChanges() {
        try {
            const username = document.getElementById('edit-username').value;
            const email = document.getElementById('edit-email').value;

            const token = localStorage.getItem('windexai_token');
            const response = await fetch('/api/profile/update', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ username, email })
            });

            if (response.ok) {
                this.showSuccess('Профиль обновлен успешно');
                this.closeModal('edit-profile-modal');
                await this.loadProfileData();
                await this.loadUserData();
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Ошибка обновления профиля');
            }
        } catch (error) {
            console.error('Error updating profile:', error);
            this.showError('Ошибка обновления профиля');
        }
    }

    async updateProfile() {
        // This is handled by the form in settings section
        await this.saveProfileChanges();
    }

    async changePassword() {
        try {
            const currentPassword = document.getElementById('current-password').value;
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;

            if (newPassword !== confirmPassword) {
                this.showError('Новые пароли не совпадают');
                return;
            }

            const token = localStorage.getItem('windexai_token');
            const response = await fetch('/api/profile/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });

            if (response.ok) {
                this.showSuccess('Пароль изменен успешно');
                document.getElementById('password-settings-form').reset();
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Ошибка изменения пароля');
            }
        } catch (error) {
            console.error('Error changing password:', error);
            this.showError('Ошибка изменения пароля');
        }
    }

    openDeleteModal() {
        this.openModal('delete-confirm-modal');
    }

    async deleteAccount() {
        try {
            const token = localStorage.getItem('windexai_token');
            const response = await fetch('/api/profile/account', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                this.showSuccess('Аккаунт удален успешно');
                localStorage.removeItem('windexai_token');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Ошибка удаления аккаунта');
            }
        } catch (error) {
            console.error('Error deleting account:', error);
            this.showError('Ошибка удаления аккаунта');
        }
    }

    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
        document.body.style.overflow = '';
    }

    scrollToElement(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    }

    async logout() {
        localStorage.removeItem('windexai_token');
        window.location.href = '/';
    }

    formatDate(date) {
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        
        if (days === 0) {
            return 'Сегодня';
        } else if (days === 1) {
            return 'Вчера';
        } else if (days < 7) {
            return `${days} дней назад`;
        } else {
            return date.toLocaleDateString('ru-RU');
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;

        const icon = type === 'success' ? 'fa-check-circle' :
                    type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';

        notification.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, type === 'error' ? 5000 : 3000);
    }

    async editSite(siteId) {
        // For now, redirect to editor with site data
        // In future, this could open a modal with site editing form
        this.showInfo('Функция редактирования сайта будет добавлена в следующем обновлении');
    }

    async deleteSite(siteId) {
        if (!confirm('Вы уверены, что хотите удалить этот сайт? Это действие нельзя отменить.')) {
            return;
        }

        try {
            const token = localStorage.getItem('windexai_token');
            const response = await fetch(`/api/deploy/${siteId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                this.showSuccess('Сайт успешно удален');
                await this.loadDeployedSites(); // Reload the sites grid
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Ошибка при удалении сайта');
            }
        } catch (error) {
            console.error('Error deleting site:', error);
            this.showError('Ошибка при удалении сайта');
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DashboardManager();
});