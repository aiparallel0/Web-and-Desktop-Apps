/**
 * Dashboard Controller
 * Manages all dashboard functionality, data loading, and UI updates
 */

import stateManager from '../core/state-manager.js';
import apiClient from '../core/api-client.js';

class DashboardController {
    constructor() {
        this.currentSection = 'overview';
        this.refreshInterval = null;
        this.charts = {};
        this.tables = {};
        this.initialized = false;
    }

    async initialize() {
        if (this.initialized) return;

        try {
            this.setupEventListeners();
            await this.loadDashboardData();
            
            this.initializeOverview();
            this.initializeExtractions();
            this.initializeBatchProcessing();
            this.initializeApiKeys();
            this.initializeTemplates();
            this.initializeAnalytics();
            this.initializeSettings();
            
            this.startAutoRefresh();
            
            const activeSection = stateManager.get('ui.activeSection') || 'overview';
            this.navigateToSection(activeSection);
            
            this.initialized = true;
            console.log('✓ Dashboard initialized');
        } catch (error) {
            console.error('Dashboard initialization error:', error);
            this.showError('Failed to initialize dashboard');
        }
    }

    async loadDashboardData() {
        try {
            const profile = await apiClient.getProfile();
            stateManager.set('user', profile);

            const extractions = await apiClient.listExtractions({ limit: 100 });
            stateManager.set('extractions', extractions.data || []);

            const batchJobs = await apiClient.listBatchJobs({ limit: 50 });
            stateManager.set('batchJobs', batchJobs.data || []);

            const apiKeys = await apiClient.listApiKeys();
            stateManager.set('apiKeys', apiKeys.data || []);

            const templates = await apiClient.listTemplates();
            stateManager.set('templates', templates.data || []);

            const analytics = await apiClient.getAnalytics();
            stateManager.set('analytics', analytics);

            const notifications = await apiClient.getNotifications({ limit: 20 });
            stateManager.set('notifications', notifications.data || []);

        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }

    setupEventListeners() {
        document.querySelectorAll('.sidebar-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.getAttribute('data-section');
                this.navigateToSection(section);
            });
        });

        const userMenuBtn = document.getElementById('userMenuBtn');
        if (userMenuBtn) {
            userMenuBtn.addEventListener('click', () => this.toggleUserMenu());
        }

        const notificationsBtn = document.getElementById('notificationsBtn');
        if (notificationsBtn) {
            notificationsBtn.addEventListener('click', () => this.toggleNotifications());
        }

        const quickExtractBtn = document.getElementById('quickExtractBtn');
        if (quickExtractBtn) {
            quickExtractBtn.addEventListener('click', () => this.openQuickExtract());
        }

        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabId = tab.getAttribute('data-tab');
                this.switchSettingsTab(tabId);
            });
        });

        stateManager.subscribe('extractions', () => this.refreshExtractionsTable());
        stateManager.subscribe('batchJobs', () => this.refreshBatchQueue());
        stateManager.subscribe('apiKeys', () => this.refreshApiKeysList());
        stateManager.subscribe('templates', () => this.refreshTemplatesGrid());
        stateManager.subscribe('analytics', () => this.refreshAnalytics());
        stateManager.subscribe('notifications', () => this.updateNotificationBadge());
    }

    navigateToSection(sectionId) {
        document.querySelectorAll('.sidebar-link').forEach(link => {
            link.classList.toggle('active', link.getAttribute('data-section') === sectionId);
        });

        document.querySelectorAll('.dashboard-section').forEach(section => {
            section.classList.remove('active');
        });

        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.add('active');
            this.currentSection = sectionId;
            stateManager.set('ui.activeSection', sectionId);
            this.refreshSection(sectionId);
        }

        window.location.hash = sectionId;
    }

    async refreshSection(sectionId) {
        switch (sectionId) {
            case 'overview':
                await this.refreshOverview();
                break;
            case 'extractions':
                await this.refreshExtractionsTable();
                break;
            case 'batch':
                await this.refreshBatchQueue();
                break;
            case 'api':
                await this.refreshApiKeysList();
                break;
            case 'templates':
                await this.refreshTemplatesGrid();
                break;
            case 'analytics':
                await this.refreshAnalytics();
                break;
        }
    }

    initializeOverview() {
        this.initializeStatsCards();
        this.initializeActivityChart();
        this.initializeModelChart();
        this.initializeRecentActivity();
    }

    initializeStatsCards() {
        const analytics = stateManager.get('analytics');
        
        this.updateStat('totalExtractions', analytics.totalExtractions || 0, '+12%');
        this.updateStat('successRate', `${(analytics.successRate || 0).toFixed(1)}%`, '+2.1%');
        this.updateStat('avgProcessingTime', `${(analytics.avgProcessingTime || 0).toFixed(1)}s`, '+0.2s');
        this.updateStat('apiCalls', analytics.apiCalls || 0, '+24%');
    }

    updateStat(statId, value, change) {
        const statCard = document.querySelector(`[data-stat="${statId}"]`);
        if (!statCard) return;

        const valueEl = statCard.querySelector('.stat-value');
        if (valueEl) valueEl.textContent = value;

        const changeEl = statCard.querySelector('.stat-change');
        if (changeEl) changeEl.textContent = change;
    }

    initializeActivityChart() {
        const canvas = document.getElementById('activityChart');
        if (!canvas || typeof Chart === 'undefined') return;

        const ctx = canvas.getContext('2d');
        const extractions = stateManager.get('extractions') || [];

        const dateCounts = this.groupByDate(extractions, 7);

        this.charts.activity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Object.keys(dateCounts),
                datasets: [{
                    label: 'Extractions',
                    data: Object.values(dateCounts),
                    borderColor: '#3B82F6',
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
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    initializeModelChart() {
        const canvas = document.getElementById('modelChart');
        if (!canvas || typeof Chart === 'undefined') return;

        const ctx = canvas.getContext('2d');
        const extractions = stateManager.get('extractions') || [];

        const modelCounts = {};
        extractions.forEach(e => {
            const model = e.model || 'Unknown';
            modelCounts[model] = (modelCounts[model] || 0) + 1;
        });

        this.charts.models = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(modelCounts),
                datasets: [{
                    data: Object.values(modelCounts),
                    backgroundColor: [
                        '#3B82F6',
                        '#10B981',
                        '#F59E0B',
                        '#EF4444',
                        '#8B5CF6'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    initializeRecentActivity() {
        this.refreshRecentActivity();
    }

    refreshRecentActivity() {
        const container = document.getElementById('recentActivity');
        if (!container) return;

        const extractions = stateManager.get('extractions') || [];
        const recent = extractions.slice(0, 5);

        if (recent.length === 0) {
            container.innerHTML = '<p class="empty-state">No recent extractions</p>';
            return;
        }

        container.innerHTML = recent.map(extraction => `
            <div class="activity-item" data-id="${extraction.id}">
                <div class="activity-icon ${extraction.status}">
                    ${this.getStatusIcon(extraction.status)}
                </div>
                <div class="activity-content">
                    <div class="activity-title">${extraction.merchant || 'Unknown Merchant'}</div>
                    <div class="activity-meta">
                        ${this.formatDate(extraction.created_at)} • ${extraction.model || 'Auto'}
                    </div>
                </div>
                <div class="activity-actions">
                    <span class="activity-amount">${this.formatCurrency(extraction.total)}</span>
                    <button class="btn btn-ghost btn-sm" onclick="dashboardController.viewExtraction('${extraction.id}')">
                        View
                    </button>
                </div>
            </div>
        `).join('');
    }

    async refreshOverview() {
        try {
            const analytics = await apiClient.getAnalytics();
            stateManager.set('analytics', analytics);
            
            this.initializeStatsCards();
            this.refreshRecentActivity();
            
            if (this.charts.activity) {
                const extractions = stateManager.get('extractions') || [];
                const dateCounts = this.groupByDate(extractions, 7);
                this.charts.activity.data.labels = Object.keys(dateCounts);
                this.charts.activity.data.datasets[0].data = Object.values(dateCounts);
                this.charts.activity.update();
            }
        } catch (error) {
            console.error('Error refreshing overview:', error);
        }
    }

    initializeExtractions() {
        this.setupExtractionsTable();
        this.setupExtractionsFilters();
        this.setupExtractionsSearch();
    }

    setupExtractionsTable() {
        this.tables.extractions = {
            currentPage: 1,
            perPage: 20,
            sortBy: 'created_at',
            sortOrder: 'desc',
            filters: {},
            selected: new Set()
        };

        this.refreshExtractionsTable();

        const selectAll = document.getElementById('selectAll');
        if (selectAll) {
            selectAll.addEventListener('change', (e) => {
                this.toggleSelectAllExtractions(e.target.checked);
            });
        }
    }

    refreshExtractionsTable() {
        const tbody = document.querySelector('#extractionsTable tbody');
        if (!tbody) return;

        const extractions = this.getFilteredExtractions();
        const { currentPage, perPage } = this.tables.extractions;
        
        const start = (currentPage - 1) * perPage;
        const end = start + perPage;
        const page = extractions.slice(start, end);

        if (page.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="empty-state">
                        No extractions found
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = page.map(extraction => `
            <tr data-id="${extraction.id}" class="${this.tables.extractions.selected.has(extraction.id) ? 'selected' : ''}">
                <td>
                    <input type="checkbox" ${this.tables.extractions.selected.has(extraction.id) ? 'checked' : ''}
                           onchange="dashboardController.toggleExtractionSelection('${extraction.id}', this.checked)">
                </td>
                <td>
                    <div class="table-thumbnail">
                        ${extraction.thumbnail ? `<img src="${extraction.thumbnail}" alt="Receipt">` : '<div class="thumbnail-placeholder">📄</div>'}
                    </div>
                </td>
                <td>${extraction.merchant || '-'}</td>
                <td>${this.formatCurrency(extraction.total)}</td>
                <td>${this.formatDate(extraction.date)}</td>
                <td><span class="model-badge">${extraction.model || 'Auto'}</span></td>
                <td><span class="status-badge ${extraction.status}">${this.formatStatus(extraction.status)}</span></td>
                <td class="table-actions">
                    <button class="btn btn-ghost btn-sm" onclick="dashboardController.viewExtraction('${extraction.id}')" title="View">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                            <circle cx="12" cy="12" r="3"></circle>
                        </svg>
                    </button>
                    <button class="btn btn-ghost btn-sm" onclick="dashboardController.downloadExtraction('${extraction.id}')" title="Download">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                    </button>
                    <button class="btn btn-ghost btn-sm" onclick="dashboardController.deleteExtraction('${extraction.id}')" title="Delete">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </td>
            </tr>
        `).join('');

        this.updatePagination(extractions.length);
    }

    getFilteredExtractions() {
        let extractions = stateManager.get('extractions') || [];
        const filters = this.tables.extractions.filters;

        if (filters.status) {
            extractions = extractions.filter(e => e.status === filters.status);
        }

        if (filters.model) {
            extractions = extractions.filter(e => e.model === filters.model);
        }

        if (filters.dateFrom) {
            extractions = extractions.filter(e => new Date(e.created_at) >= new Date(filters.dateFrom));
        }

        if (filters.dateTo) {
            extractions = extractions.filter(e => new Date(e.created_at) <= new Date(filters.dateTo));
        }

        if (filters.search) {
            const search = filters.search.toLowerCase();
            extractions = extractions.filter(e => 
                (e.merchant && e.merchant.toLowerCase().includes(search)) ||
                (e.id && e.id.toLowerCase().includes(search))
            );
        }

        const { sortBy, sortOrder } = this.tables.extractions;
        extractions.sort((a, b) => {
            let aVal = a[sortBy];
            let bVal = b[sortBy];

            if (typeof aVal === 'string') aVal = aVal.toLowerCase();
            if (typeof bVal === 'string') bVal = bVal.toLowerCase();

            if (sortOrder === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });

        return extractions;
    }

    setupExtractionsFilters() {
        const filterBtn = document.getElementById('filterBtn');
        if (filterBtn) {
            filterBtn.addEventListener('click', () => this.showFiltersModal());
        }
    }

    setupExtractionsSearch() {
        const searchInput = document.querySelector('#extractions .search-input');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.tables.extractions.filters.search = e.target.value;
                    this.refreshExtractionsTable();
                }, 300);
            });
        }
    }

    toggleExtractionSelection(id, selected) {
        if (selected) {
            this.tables.extractions.selected.add(id);
        } else {
            this.tables.extractions.selected.delete(id);
        }
        this.refreshExtractionsTable();
    }

    toggleSelectAllExtractions(selected) {
        const extractions = this.getFilteredExtractions();
        if (selected) {
            extractions.forEach(e => this.tables.extractions.selected.add(e.id));
        } else {
            this.tables.extractions.selected.clear();
        }
        this.refreshExtractionsTable();
    }

    async viewExtraction(id) {
        try {
            const extraction = await apiClient.getExtraction(id);
            this.showExtractionModal(extraction);
        } catch (error) {
            this.showError('Failed to load extraction');
        }
    }

    async downloadExtraction(id) {
        try {
            const blob = await apiClient.exportData([id], 'json');
            this.downloadBlob(blob, `extraction-${id}.json`);
        } catch (error) {
            this.showError('Failed to download extraction');
        }
    }

    async deleteExtraction(id) {
        if (!confirm('Are you sure you want to delete this extraction?')) return;

        try {
            await apiClient.deleteExtraction(id);
            
            const extractions = stateManager.get('extractions') || [];
            const filtered = extractions.filter(e => e.id !== id);
            stateManager.set('extractions', filtered);
            
            this.showSuccess('Extraction deleted');
        } catch (error) {
            this.showError('Failed to delete extraction');
        }
    }

    initializeBatchProcessing() {
        this.setupBatchQueue();
        this.setupBatchHistory();

        const newBatchBtn = document.getElementById('newBatchBtn');
        if (newBatchBtn) {
            newBatchBtn.addEventListener('click', () => this.openNewBatchModal());
        }
    }

    setupBatchQueue() {
        this.refreshBatchQueue();
    }

    setupBatchHistory() {
        this.refreshBatchHistory();
    }

    refreshBatchQueue() {
        const container = document.getElementById('batchQueue');
        if (!container) return;

        const jobs = stateManager.get('batchJobs') || [];
        const processing = jobs.filter(j => j.status === 'processing' || j.status === 'queued');

        if (processing.length === 0) {
            container.innerHTML = '<p class="empty-state">No active batch jobs</p>';
            return;
        }

        container.innerHTML = processing.map(job => `
            <div class="batch-item" data-id="${job.id}">
                <div class="batch-header">
                    <h4>${job.name || `Batch ${job.id}`}</h4>
                    <span class="status-badge ${job.status}">${job.status}</span>
                </div>
                <div class="batch-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${job.progress || 0}%"></div>
                    </div>
                    <span class="progress-text">${job.completed || 0} / ${job.total || 0} files</span>
                </div>
                <div class="batch-actions">
                    <button class="btn btn-ghost btn-sm" onclick="dashboardController.viewBatchJob('${job.id}')">View</button>
                    <button class="btn btn-ghost btn-sm" onclick="dashboardController.cancelBatchJob('${job.id}')">Cancel</button>
                </div>
            </div>
        `).join('');
    }

    refreshBatchHistory() {
        const container = document.getElementById('batchHistory');
        if (!container) return;

        const jobs = stateManager.get('batchJobs') || [];
        const completed = jobs.filter(j => j.status === 'completed' || j.status === 'failed');

        if (completed.length === 0) {
            container.innerHTML = '<p class="empty-state">No batch history</p>';
            return;
        }

        container.innerHTML = completed.map(job => `
            <div class="batch-history-item" data-id="${job.id}">
                <div class="batch-info">
                    <h4>${job.name || `Batch ${job.id}`}</h4>
                    <p>${job.total || 0} files • ${this.formatDate(job.created_at)}</p>
                </div>
                <div class="batch-status">
                    <span class="status-badge ${job.status}">${job.status}</span>
                </div>
                <div class="batch-actions">
                    <button class="btn btn-ghost btn-sm" onclick="dashboardController.downloadBatchResults('${job.id}')">Download</button>
                    <button class="btn btn-ghost btn-sm" onclick="dashboardController.deleteBatchJob('${job.id}')">Delete</button>
                </div>
            </div>
        `).join('');
    }

    async viewBatchJob(id) {
        try {
            const job = await apiClient.getBatchJob(id);
            this.showBatchJobModal(job);
        } catch (error) {
            this.showError('Failed to load batch job');
        }
    }

    async cancelBatchJob(id) {
        if (!confirm('Are you sure you want to cancel this batch job?')) return;

        try {
            await apiClient.cancelBatchJob(id);
            await this.refreshBatchQueue();
            this.showSuccess('Batch job cancelled');
        } catch (error) {
            this.showError('Failed to cancel batch job');
        }
    }

    async downloadBatchResults(id) {
        try {
            const blob = await apiClient.downloadBatchResults(id, 'csv');
            this.downloadBlob(blob, `batch-${job.id}.csv`);
        } catch (error) {
            this.showError('Failed to download batch results');
        }
    }

    async deleteBatchJob(id) {
        if (!confirm('Are you sure you want to delete this batch job?')) return;

        try {
            await apiClient.deleteBatchJob(id);
            
            const jobs = stateManager.get('batchJobs') || [];
            const filtered = jobs.filter(j => j.id !== id);
            stateManager.set('batchJobs', filtered);
            
            this.showSuccess('Batch job deleted');
        } catch (error) {
            this.showError('Failed to delete batch job');
        }
    }

    initializeApiKeys() {
        this.refreshApiKeysList();
    }

    refreshApiKeysList() {
        const container = document.getElementById('apiKeysList');
        if (!container) return;

        const keys = stateManager.get('apiKeys') || [];

        if (keys.length === 0) {
            container.innerHTML = '<p class="empty-state">No API keys created yet</p>';
            return;
        }

        container.innerHTML = keys.map(key => `
            <div class="api-key-item" data-id="${key.id}">
                <div class="key-info">
                    <h4>${key.name}</h4>
                    <code>${key.key_preview}</code>
                    <p>Created: ${this.formatDate(key.created_at)} • Last used: ${key.last_used ? this.formatDate(key.last_used) : 'Never'}</p>
                </div>
                <div class="key-actions">
                    <button class="btn btn-ghost btn-sm" onclick="dashboardController.copyApiKey('${key.id}')">Copy</button>
                    <button class="btn btn-ghost btn-sm" onclick="dashboardController.revokeApiKey('${key.id}')">Revoke</button>
                </div>
            </div>
        `).join('');
    }

    initializeTemplates() {
        this.refreshTemplatesGrid();
    }

    refreshTemplatesGrid() {
        const container = document.getElementById('templatesGrid');
        if (!container) return;

        const templates = stateManager.get('templates') || [];

        if (templates.length === 0) {
            container.innerHTML = '<p class="empty-state">No templates created yet</p>';
            return;
        }

        container.innerHTML = templates.map(template => `
            <div class="template-card" data-id="${template.id}">
                <h4>${template.name}</h4>
                <p>${template.description || 'No description'}</p>
                <div class="template-meta">
                    <span>${template.field_count || 0} fields</span>
                    <span>Created: ${this.formatDate(template.created_at)}</span>
                </div>
                <div class="template-actions">
                    <button class="btn btn-ghost btn-sm" onclick="dashboardController.editTemplate('${template.id}')">Edit</button>
                    <button class="btn btn-ghost btn-sm" onclick="dashboardController.deleteTemplate('${template.id}')">Delete</button>
                </div>
            </div>
        `).join('');
    }

    initializeAnalytics() {
        this.refreshAnalytics();
    }

    refreshAnalytics() {
        console.log('Refresh analytics');
    }

    initializeSettings() {
        console.log('Initialize settings');
    }

    groupByDate(items, days) {
        const counts = {};
        const now = new Date();

        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            const key = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            counts[key] = 0;
        }

        items.forEach(item => {
            const date = new Date(item.created_at || item.timestamp);
            const key = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            if (key in counts) {
                counts[key]++;
            }
        });

        return counts;
    }

    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatCurrency(amount) {
        if (amount === null || amount === undefined) return '-';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    formatStatus(status) {
        return status.charAt(0).toUpperCase() + status.slice(1);
    }

    getStatusIcon(status) {
        const icons = {
            success: '✓',
            failed: '✗',
            processing: '⟳',
            queued: '⋯'
        };
        return icons[status] || '•';
    }

    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    showSuccess(message) {
        console.log('Success:', message);
    }

    showError(message) {
        console.error('Error:', message);
        alert(message);
    }

    showFiltersModal() {
        console.log('Show filters modal');
    }

    showExtractionModal(extraction) {
        console.log('Show extraction modal:', extraction);
    }

    showBatchJobModal(job) {
        console.log('Show batch job modal:', job);
    }

    openQuickExtract() {
        console.log('Open quick extract');
    }

    openNewBatchModal() {
        console.log('Open new batch modal');
    }

    toggleUserMenu() {
        console.log('Toggle user menu');
    }

    toggleNotifications() {
        console.log('Toggle notifications');
    }

    updateNotificationBadge() {
        const badge = document.querySelector('.notification-badge');
        if (!badge) return;

        const notifications = stateManager.get('notifications') || [];
        const unread = notifications.filter(n => !n.read).length;

        if (unread > 0) {
            badge.textContent = unread > 99 ? '99+' : unread;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }

    switchSettingsTab(tabId) {
        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.classList.toggle('active', tab.getAttribute('data-tab') === tabId);
        });

        document.querySelectorAll('.settings-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === tabId);
        });
    }

    updatePagination(totalItems) {
        console.log('Update pagination for', totalItems, 'items');
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            if (this.currentSection === 'overview' || this.currentSection === 'batch') {
                this.loadDashboardData();
            }
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    destroy() {
        this.stopAutoRefresh();
        
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });

        this.charts = {};
        this.tables = {};
        this.initialized = false;
    }
}

const dashboardController = new DashboardController();

if (typeof window !== 'undefined') {
    window.dashboardController = dashboardController;
    window.DashboardController = DashboardController;
}

export default dashboardController;
