class ProfileManager {
    constructor() {
        this.currentUser = null;
        this.profileData = null;
        this.statsData = null;
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadUserData();
        await this.loadProfileData();
        await this.loadStatsData();
        await this.loadRecentActivity();
        this.setupTabs();
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Edit profile button
        document.getElementById('edit-profile-btn').addEventListener('click', () => {
            this.openEditModal();
        });

        // Profile form
        document.getElementById('profile-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateProfile();
        });

        // Password form
        document.getElementById('password-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.changePassword();
        });

        // Delete account button
        document.getElementById('delete-account-btn').addEventListener('click', () => {
            this.openDeleteModal();
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
                this.updateRecentActivity(activityData);
            }
        } catch (error) {
            console.error('Error loading recent activity:', error);
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
        }
    }

    updateStats() {
        if (this.statsData) {
            // Monthly stats
            document.getElementById('messages-this-month').textContent = this.statsData.messages_this_month;
            document.getElementById('conversations-this-month').textContent = this.statsData.conversations_this_month;

            // Most active day
            const mostActiveDay = document.getElementById('most-active-day');
            if (this.statsData.most_active_day) {
                const date = new Date(this.statsData.most_active_day);
                mostActiveDay.textContent = this.formatDate(date);
            } else {
                mostActiveDay.textContent = 'Неизвестно';
            }

            // Average messages
            document.getElementById('avg-messages').textContent = this.statsData.average_messages_per_conversation;
        }
    }

    updateRecentActivity(activityData) {
        // Recent conversations
        const conversationsContainer = document.getElementById('recent-conversations');
        if (activityData.recent_conversations.length > 0) {
            conversationsContainer.innerHTML = activityData.recent_conversations.map(conv => `
                <div class="activity-item">
                    <div class="activity-icon">
                        <i class="fas fa-comments"></i>
                    </div>
                    <div class="activity-content">
                        <h4>${conv.title}</h4>
                        <p>${conv.message_count} сообщений • ${this.formatDate(new Date(conv.updated_at))}</p>
                    </div>
                </div>
            `).join('');
        } else {
            conversationsContainer.innerHTML = '<div class="no-activity">Нет недавних разговоров</div>';
        }

        // Recent documents
        const documentsContainer = document.getElementById('recent-documents');
        if (activityData.recent_documents.length > 0) {
            documentsContainer.innerHTML = activityData.recent_documents.map(doc => `
                <div class="activity-item">
                    <div class="activity-icon">
                        <i class="fas fa-file-alt"></i>
                    </div>
                    <div class="activity-content">
                        <h4>${doc.filename}</h4>
                        <p>${doc.file_type.toUpperCase()} • ${this.formatFileSize(doc.file_size)} • ${this.formatDate(new Date(doc.upload_date))}</p>
                    </div>
                </div>
            `).join('');
        } else {
            documentsContainer.innerHTML = '<div class="no-activity">Нет загруженных документов</div>';
        }

        // Recent deployments
        const deploymentsContainer = document.getElementById('recent-deployments');
        if (activityData.recent_deployments.length > 0) {
            deploymentsContainer.innerHTML = activityData.recent_deployments.map(dep => `
                <div class="activity-item">
                    <div class="activity-icon">
                        <i class="fas fa-rocket"></i>
                    </div>
                    <div class="activity-content">
                        <h4>${dep.name}</h4>
                        <p>Статус: ${dep.status} • ${this.formatDate(new Date(dep.created_at))}</p>
                    </div>
                </div>
            `).join('');
        } else {
            deploymentsContainer.innerHTML = '<div class="no-activity">Нет деплоев</div>';
        }
    }

    setupTabs() {
        // Set initial tab
        this.switchTab('overview');
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
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
        // This is handled by the form in settings tab
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
                document.getElementById('password-form').reset();
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
        // Create success notification
        const notification = document.createElement('div');
        notification.className = 'notification notification-success';
        notification.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span>${message}</span>
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    showError(message) {
        // Create error notification
        const notification = document.createElement('div');
        notification.className = 'notification notification-error';
        notification.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize profile manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ProfileManager();
});

