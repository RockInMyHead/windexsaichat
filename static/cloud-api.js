/**
 * Windexs Cloud API Client
 * Handles all cloud storage operations
 */
class WindexsCloudAPI {
    constructor(credentials, baseURL = 'http://localhost:8080/api') {
        this.credentials = credentials; // {username, password}
        this.baseURL = baseURL;
        this.sessionActive = false;
    }

    /**
     * Login to get session
     */
    async login() {
        const response = await fetch(`${this.baseURL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', // Important for session cookies
            body: JSON.stringify(this.credentials)
        });

        if (!response.ok) {
            throw new Error(`Login failed: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        this.sessionActive = result.success;
        return result;
    }

    /**
     * Make authenticated request to the API
     */
    async request(endpoint, options = {}) {
        // Ensure we're logged in
        if (!this.sessionActive) {
            await this.login();
        }

        const url = `${this.baseURL}${endpoint}`;
        const config = {
            credentials: 'include', // Important for session cookies
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        const response = await fetch(url, config);
        
        if (!response.ok) {
            if (response.status === 401) {
                // Session expired, try to login again
                this.sessionActive = false;
                await this.login();
                // Retry the request
                return this.request(endpoint, options);
            }
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
        }
        
        return response.json();
    }

    /**
     * Get list of files and folders
     */
    async getFiles(path = '/') {
        const endpoint = path === '/' ? '/files' : `/files?path=${encodeURIComponent(path)}`;
        return await this.request(endpoint);
    }

    /**
     * Upload file to cloud
     */
    async uploadFile(file, path = '/', onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (path !== '/') {
            formData.append('path', path);
        }

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            if (onProgress) {
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        onProgress(percentComplete);
                    }
                });
            }
            
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        resolve(JSON.parse(xhr.responseText));
                    } catch (e) {
                        reject(new Error('Invalid response format'));
                    }
                } else {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });
            
            xhr.open('POST', `${this.baseURL}/upload`);
            xhr.setRequestHeader('Authorization', `Bearer ${this.apiKey}`);
            xhr.send(formData);
        });
    }

    /**
     * Download file from cloud
     */
    async downloadFile(fileId) {
        const response = await fetch(`${this.baseURL}/files/${fileId}/download`, {
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });

        if (!response.ok) {
            throw new Error(`Download failed: ${response.statusText}`);
        }

        return response.blob();
    }

    /**
     * Get file URL for viewing
     */
    getFileUrl(fileId) {
        return `${this.baseURL}/files/${fileId}/view?token=${this.apiKey}`;
    }

    /**
     * Get file information
     */
    async getFileInfo(fileId) {
        return await this.request(`/files/${fileId}`);
    }

    /**
     * Create folder
     */
    async createFolder(name, path = '/') {
        return await this.request('/folders', {
            method: 'POST',
            body: JSON.stringify({
                name: name,
                path: path
            })
        });
    }

    /**
     * Rename file or folder
     */
    async renameFile(fileId, newName) {
        return await this.request(`/files/${fileId}`, {
            method: 'PUT',
            body: JSON.stringify({
                name: newName
            })
        });
    }

    /**
     * Delete file or folder
     */
    async deleteFile(fileId) {
        return await this.request(`/files/${fileId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Search files
     */
    async searchFiles(query, type = null, path = null) {
        let endpoint = `/search?q=${encodeURIComponent(query)}`;
        if (type) endpoint += `&type=${type}`;
        if (path) endpoint += `&path=${encodeURIComponent(path)}`;
        
        return await this.request(endpoint);
    }

    /**
     * Test API connection
     */
    async testConnection() {
        try {
            // First try to login
            await this.login();
            
            // Then test the files endpoint
            const result = await this.getFiles();
            
            if (result.success) {
                return { success: true, message: 'Connection successful' };
            } else {
                return { 
                    success: false, 
                    message: `Connection failed: ${result.message}` 
                };
            }
        } catch (error) {
            if (error.message.includes('fetch')) {
                return { 
                    success: false, 
                    message: 'Cannot connect to cloud service. Please ensure the service is running on http://localhost:8080' 
                };
            }
            return { success: false, message: error.message };
        }
    }
}

/**
 * Cloud File Manager UI
 */
class CloudFileManager {
    constructor(api) {
        this.api = api;
        this.currentPath = '/';
        this.selectedFiles = new Set();
    }

    /**
     * Initialize the cloud file manager
     */
    async init() {
        this.createUI();
        await this.loadFiles();
        this.setupEventListeners();
    }

    /**
     * Create the cloud file manager UI
     */
    createUI() {
        const modal = document.createElement('div');
        modal.id = 'cloud-modal';
        modal.className = 'cloud-modal hidden';
        modal.innerHTML = `
            <div class="cloud-modal-content card">
                <div class="card-header">
                    <div class="d-flex align-items-center justify-content-between">
                        <h2 class="mb-0">☁️ Windexs Cloud</h2>
                        <button class="close-cloud btn btn-outline" title="Закрыть">×</button>
                    </div>
                </div>
                <div class="card-body">
                    <!-- Toolbar -->
                    <div class="cloud-toolbar mb-3">
                        <div class="d-flex gap-2 align-items-center">
                            <button id="cloud-upload-btn" class="btn btn-primary btn-sm">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="me-1">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                    <polyline points="7,10 12,15 17,10"></polyline>
                                    <line x1="12" y1="15" x2="12" y2="3"></line>
                                </svg>
                                Загрузить
                            </button>
                            <button id="cloud-new-folder-btn" class="btn btn-outline btn-sm">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="me-1">
                                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                                </svg>
                                Новая папка
                            </button>
                            <button id="cloud-refresh-btn" class="btn btn-outline btn-sm">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="me-1">
                                    <polyline points="23,4 23,10 17,10"></polyline>
                                    <polyline points="1,20 1,14 7,14"></polyline>
                                    <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
                                </svg>
                                Обновить
                            </button>
                        </div>
                        <div class="cloud-path mt-2">
                            <span class="text-muted small">Путь: </span>
                            <span id="cloud-current-path">/</span>
                        </div>
                    </div>

                    <!-- File List -->
                    <div class="cloud-files-container">
                        <div id="cloud-files-list" class="cloud-files-list">
                            <!-- Files will be loaded here -->
                        </div>
                    </div>

                    <!-- Upload Progress -->
                    <div id="cloud-upload-progress" class="cloud-upload-progress hidden">
                        <div class="progress">
                            <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                        </div>
                        <div class="upload-status text-center mt-2">
                            <span id="upload-status-text">Загрузка...</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Close modal
        document.querySelector('.close-cloud').addEventListener('click', () => {
            this.hide();
        });

        // Upload button
        document.getElementById('cloud-upload-btn').addEventListener('click', () => {
            this.showUploadDialog();
        });

        // New folder button
        document.getElementById('cloud-new-folder-btn').addEventListener('click', () => {
            this.showNewFolderDialog();
        });

        // Refresh button
        document.getElementById('cloud-refresh-btn').addEventListener('click', () => {
            this.loadFiles();
        });

        // Click outside to close
        document.getElementById('cloud-modal').addEventListener('click', (e) => {
            if (e.target.id === 'cloud-modal') {
                this.hide();
            }
        });
    }

    /**
     * Show the cloud file manager
     */
    show() {
        document.getElementById('cloud-modal').classList.remove('hidden');
        this.loadFiles();
    }

    /**
     * Hide the cloud file manager
     */
    hide() {
        document.getElementById('cloud-modal').classList.add('hidden');
    }

    /**
     * Load files from current path
     */
    async loadFiles() {
        try {
            const files = await this.api.getFiles(this.currentPath);
            this.renderFiles(files);
            this.updatePathDisplay();
        } catch (error) {
            console.error('Error loading files:', error);
            this.showError('Ошибка загрузки файлов: ' + error.message);
        }
    }

    /**
     * Render files in the UI
     */
    renderFiles(files) {
        const container = document.getElementById('cloud-files-list');
        
        if (files.length === 0) {
            container.innerHTML = '<div class="text-center text-muted py-4">Папка пуста</div>';
            return;
        }

        const filesHtml = files.map(file => {
            const isFolder = file.type === 'folder';
            const icon = isFolder ? '📁' : this.getFileIcon(file.name);
            const size = isFolder ? '' : this.formatFileSize(file.size);
            
            return `
                <div class="cloud-file-item" data-file-id="${file.id}" data-type="${file.type}">
                    <div class="d-flex align-items-center">
                        <div class="cloud-file-icon me-3">${icon}</div>
                        <div class="cloud-file-info flex-grow-1">
                            <div class="cloud-file-name">${file.name}</div>
                            <div class="cloud-file-meta text-muted small">
                                ${size} • ${new Date(file.modifiedAt).toLocaleDateString('ru-RU')}
                            </div>
                        </div>
                        <div class="cloud-file-actions">
                            ${isFolder ? 
                                `<button class="btn btn-sm btn-outline" onclick="cloudManager.openFolder('${file.path}')">Открыть</button>` :
                                `<div class="d-flex gap-1">
                                    <button class="btn btn-sm btn-outline" onclick="cloudManager.viewFile('${file.id}')" title="Просмотр">👁️</button>
                                    <button class="btn btn-sm btn-primary" onclick="cloudManager.downloadFile('${file.id}')" title="Скачать">📥</button>
                                </div>`
                            }
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = filesHtml;
    }

    /**
     * Get file icon based on extension
     */
    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            'pdf': '📄',
            'doc': '📝', 'docx': '📝',
            'xls': '📊', 'xlsx': '📊',
            'ppt': '📽️', 'pptx': '📽️',
            'txt': '📄',
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
            'mp4': '🎥', 'avi': '🎥', 'mov': '🎥',
            'mp3': '🎵', 'wav': '🎵',
            'zip': '📦', 'rar': '📦', '7z': '📦'
        };
        return icons[ext] || '📄';
    }

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Update path display
     */
    updatePathDisplay() {
        document.getElementById('cloud-current-path').textContent = this.currentPath;
    }

    /**
     * Open folder
     */
    openFolder(path) {
        this.currentPath = path;
        this.loadFiles();
    }

    /**
     * Show upload dialog
     */
    showUploadDialog() {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.addEventListener('change', (e) => {
            this.uploadFiles(Array.from(e.target.files));
        });
        input.click();
    }

    /**
     * Upload files
     */
    async uploadFiles(files) {
        const progressContainer = document.getElementById('cloud-upload-progress');
        const progressBar = progressContainer.querySelector('.progress-bar');
        const statusText = document.getElementById('upload-status-text');
        
        progressContainer.classList.remove('hidden');
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            statusText.textContent = `Загрузка ${file.name}...`;
            
            try {
                await this.api.uploadFile(file, this.currentPath, (progress) => {
                    progressBar.style.width = `${progress}%`;
                });
            } catch (error) {
                console.error('Upload error:', error);
                this.showError(`Ошибка загрузки ${file.name}: ${error.message}`);
            }
        }
        
        progressContainer.classList.add('hidden');
        progressBar.style.width = '0%';
        await this.loadFiles();
        this.showSuccess(`Загружено файлов: ${files.length}`);
    }

    /**
     * Download file
     */
    async downloadFile(fileId) {
        try {
            const blob = await this.api.downloadFile(fileId);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'file';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Download error:', error);
            this.showError('Ошибка скачивания: ' + error.message);
        }
    }

    /**
     * View file in new tab
     */
    viewFile(fileId) {
        try {
            const fileUrl = this.api.getFileUrl(fileId);
            window.open(fileUrl, '_blank');
        } catch (error) {
            console.error('View error:', error);
            this.showError('Ошибка просмотра файла: ' + error.message);
        }
    }

    /**
     * Show new folder dialog
     */
    showNewFolderDialog() {
        const name = prompt('Введите название папки:');
        if (name && name.trim()) {
            this.createFolder(name.trim());
        }
    }

    /**
     * Create new folder
     */
    async createFolder(name) {
        try {
            await this.api.createFolder(name, this.currentPath);
            await this.loadFiles();
            this.showSuccess(`Папка "${name}" создана`);
        } catch (error) {
            console.error('Create folder error:', error);
            this.showError('Ошибка создания папки: ' + error.message);
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        showNotification(message, 'success');
    }

    /**
     * Show error message
     */
    showError(message) {
        showNotification(message, 'error');
    }
}

// Global cloud manager instance
let cloudManager = null;
