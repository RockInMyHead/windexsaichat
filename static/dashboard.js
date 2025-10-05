// JavaScript для личного кабинета и аналитики
class Dashboard {
    constructor() {
        this.authToken = localStorage.getItem('windexai_token');
        this.deployments = [];
        this.analyticsChart = null;
        this.init();
    }

    init() {
        this.checkAuth();
        this.bindEvents();
        this.loadDashboardData();
    }

    checkAuth() {
        if (!this.authToken) {
            window.location.href = '/';
            return;
        }
    }

    bindEvents() {
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

        // Кнопка выхода

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

    async loadDashboardData() {
        try {
            // Загружаем общую статистику
            await this.loadOverview();

            // Загружаем деплои
            await this.loadDeployments();

            // Инициализируем график
            this.initChart();

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Не удалось загрузить данные дашборда');
        }
    }

    async loadOverview() {
        try {
            const response = await fetch('/api/dashboard/overview', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateOverviewStats(data);
            } else {
                throw new Error('Ошибка загрузки статистики');
            }
        } catch (error) {
            console.error('Error loading overview:', error);
        }
    }

    updateOverviewStats(data) {
        document.getElementById('total-deployments').textContent = data.total_deployments;
        document.getElementById('recent-deployments').textContent = `+${data.recent_deployments} за неделю`;
        document.getElementById('total-views').textContent = data.total_views.toLocaleString();
        document.getElementById('total-visitors').textContent = data.total_visitors.toLocaleString();
        document.getElementById('success-rate').textContent = `${data.success_rate}%`;

        // Обновляем изменения (демо-данные)
        document.getElementById('views-change').textContent = `+${Math.floor(Math.random() * 20 + 5)}% за неделю`;
        document.getElementById('visitors-change').textContent = `+${Math.floor(Math.random() * 15 + 3)}% за неделю`;
        document.getElementById('success-change').textContent = `+${Math.floor(Math.random() * 5 + 1)}% за неделю`;
    }

    async loadDeployments() {
        try {
            const response = await fetch('/api/dashboard/deployments', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.deployments = data.deployments || [];
                this.renderDeployments();
            } else {
                throw new Error('Ошибка загрузки деплоев');
            }
        } catch (error) {
            console.error('Error loading deployments:', error);
            this.showError('Не удалось загрузить список сайтов');
        }
    }

    renderDeployments() {
        const deploymentsGrid = document.getElementById('deployments-grid');
        const emptyState = document.getElementById('empty-state');

        if (this.deployments.length === 0) {
            deploymentsGrid.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        deploymentsGrid.style.display = 'grid';
        emptyState.style.display = 'none';

        deploymentsGrid.innerHTML = this.deployments.map(deployment => this.createDeploymentCard(deployment)).join('');

        // Привязываем события к карточкам деплоев
        this.bindDeploymentEvents();
    }

    createDeploymentCard(deployment) {
        const createdDate = new Date(deployment.created_at).toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });

        const statusClass = deployment.is_active ? 'active' : 'inactive';
        const statusText = deployment.is_active ? 'Активен' : 'Неактивен';

        return `
            <div class="deployment-card" data-deployment-id="${deployment.id}">
                <div class="deployment-header">
                    <h3 class="deployment-title">${deployment.title}</h3>
                    <span class="deployment-status ${statusClass}">${statusText}</span>
                </div>

                <a href="${deployment.deploy_url}" target="_blank" class="deployment-url">
                    ${deployment.deploy_url}
                </a>

                <div class="deployment-stats">
                    <div class="deployment-stat">
                        <div class="deployment-stat-value">${deployment.analytics.page_views}</div>
                        <div class="deployment-stat-label">Просмотры</div>
                    </div>
                    <div class="deployment-stat">
                        <div class="deployment-stat-value">${deployment.analytics.unique_visitors}</div>
                        <div class="deployment-stat-label">Посетители</div>
                    </div>
                    <div class="deployment-stat">
                        <div class="deployment-stat-value">${deployment.analytics.avg_load_time}с</div>
                        <div class="deployment-stat-label">Загрузка</div>
                    </div>
                    <div class="deployment-stat">
                        <div class="deployment-stat-value">${deployment.analytics.error_count}</div>
                        <div class="deployment-stat-label">Ошибки</div>
                    </div>
                </div>

                <div class="deployment-actions">
                    <a href="${deployment.deploy_url}" target="_blank" class="deployment-btn primary">
                        👁️ Открыть
                    </a>
                    <button class="deployment-btn secondary" onclick="dashboard.viewAnalytics(${deployment.id})">
                        📊 Аналитика
                    </button>
                    <button class="deployment-btn danger" onclick="dashboard.confirmDelete(${deployment.id}, '${deployment.title.replace(/'/g, "\\'")}')">
                        🗑️
                    </button>
                </div>
            </div>
        `;
    }

    bindDeploymentEvents() {
        // События уже привязаны через onclick в HTML
    }

    viewAnalytics(deploymentId) {
        // Открываем детальную аналитику в новом окне
        window.open(`/static/analytics.html?deployment=${deploymentId}`, '_blank');
    }

    confirmDelete(deploymentId, deploymentTitle) {
        const modal = document.getElementById('delete-modal');
        const deploymentNameSpan = document.getElementById('delete-deployment-name');
        const confirmBtn = document.getElementById('confirm-delete');

        deploymentNameSpan.textContent = deploymentTitle;
        modal.style.display = 'flex';

        // Удаляем предыдущие обработчики
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

        // Добавляем новый обработчик
        newConfirmBtn.addEventListener('click', () => {
            this.deleteDeployment(deploymentId);
            modal.style.display = 'none';
        });
    }

    async deleteDeployment(deploymentId) {
        try {
            const response = await fetch(`/api/dashboard/deployments/${deploymentId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                this.showSuccess('Сайт успешно удален');
                this.loadDashboardData(); // Перезагружаем данные
            } else {
                throw new Error('Ошибка удаления сайта');
            }
        } catch (error) {
            console.error('Error deleting deployment:', error);
            this.showError('Не удалось удалить сайт');
        }
    }

    initChart() {
        const ctx = document.getElementById('analytics-chart').getContext('2d');

        // Демо-данные для графика
        const labels = [];
        const viewsData = [];
        const visitorsData = [];

        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }));
            viewsData.push(Math.floor(Math.random() * 100 + 20));
            visitorsData.push(Math.floor(Math.random() * 50 + 10));
        }

        this.analyticsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Просмотры',
                        data: viewsData,
                        borderColor: '#22c55e',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Посетители',
                        data: visitorsData,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
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
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });
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
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new Dashboard();
});
