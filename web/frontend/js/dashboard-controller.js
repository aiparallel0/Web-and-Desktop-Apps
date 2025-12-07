/**
 * Dashboard Controller
 * Manages all dashboard functionality and interactions
 * @version 2.0.0
 */

(function(window) {
    'use strict';

    class DashboardController {
        constructor() {
            this.currentSection = 'overview';
            this.charts = {};
            this.listeners = new Map();
            this.mockData = this.generateMockData();
            
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.init());
            } else {
                this.init();
            }
        }

        /**
         * Initialize dashboard
         */
        init() {
            console.log('[Dashboard] Initializing...');
            
            // Setup navigation
            this.setupNavigation();
            
            // Setup sections
            this.setupSections();
            
            // Load initial data
            this.loadOverviewData();
            
            // Setup event listeners
            this.setupEventListeners();
            
            console.log('[Dashboard] Initialization complete');
        }

        /**
         * Setup navigation
         */
        setupNavigation() {
            const sidebarLinks = document.querySelectorAll('.sidebar-link');
            
            sidebarLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const section = link.getAttribute('data-section');
                    this.navigateToSection(section);
                });
            });

            // Handle hash navigation
            window.addEventListener('hashchange', () => {
                const hash = window.location.hash.substring(1);
                if (hash) {
                    this.navigateToSection(hash);
                }
            });

            // Initial navigation
            const initialHash = window.location.hash.substring(1);
            if (initialHash) {
                this.navigateToSection(initialHash);
            }
        }

        /**
         * Navigate to section
         */
        navigateToSection(sectionId) {
            // Update sidebar
            document.querySelectorAll('.sidebar-link').forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('data-section') === sectionId) {
                    link.classList.add('active');
                }
            });

            // Update sections
            document.querySelectorAll('.dashboard-section').forEach(section => {
                section.classList.remove('active');
            });

            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.classList.add('active');
                this.currentSection = sectionId;
                
                // Update URL
                window.history.pushState(null, null, `#${sectionId}`);
                
                // Load section data
                this.loadSectionData(sectionId);
            }
        }

        /**
         * Setup all sections
         */
        setupSections() {
            this.setupOverviewSection();
            this.setupExtractionsSection();
            this.setupBatchSection();
            this.setupAPISection();
            this.setupTemplatesSection();
            this.setupAnalyticsSection();
            this.setupSettingsSection();
        }

        /**
         * Setup overview section
         */
        setupOverviewSection() {
            const quickExtractBtn = document.getElementById('quickExtractBtn');
            if (quickExtractBtn) {
                quickExtractBtn.addEventListener('click', () => {
                    this.showQuickExtractModal();
                });
            }
        }

        /**
         * Setup extractions section
         */
        setupExtractionsSection() {
            const exportBtn = document.querySelector('#extractions .btn-primary');
            if (exportBtn) {
                exportBtn.addEventListener('click', () => {
                    this.exportExtractions();
                });
            }

            const filterBtn = document.getElementById('filterBtn');
            if (filterBtn) {
                filterBtn.addEventListener('click', () => {
                    this.showFilterModal();
                });
            }

            const searchInput = document.querySelector('#extractions .search-input');
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    this.searchExtractions(e.target.value);
                });
            }
        }

        /**
         * Setup batch section
         */
        setupBatchSection() {
            const newBatchBtn = document.getElementById('newBatchBtn');
            if (newBatchBtn) {
                newBatchBtn.addEventListener('click', () => {
                    this.showNewBatchModal();
                });
            }
        }

        /**
         * Setup API section
         */
        setupAPISection() {
            const createKeyBtn = document.getElementById('createApiKeyBtn');
            if (createKeyBtn) {
                createKeyBtn.addEventListener('click', () => {
                    this.createAPIKey();
                });
            }
        }

        /**
         * Setup templates section
         */
        setupTemplatesSection() {
            const createTemplateBtn = document.getElementById('createTemplateBtn');
            if (createTemplateBtn) {
                createTemplateBtn.addEventListener('click', () => {
                    this.createTemplate();
                });
            }
        }

        /**
         * Setup analytics section
         */
        setupAnalyticsSection() {
            const dateRangeSelect = document.querySelector('#analytics .date-range-select');
            if (dateRangeSelect) {
                dateRangeSelect.addEventListener('change', (e) => {
                    this.loadAnalytics(e.target.value);
                });
            }
        }

        /**
         * Setup settings section
         */
        setupSettingsSection() {
            const settingsTabs = document.querySelectorAll('.settings-tab');
            settingsTabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    this.switchSettingsTab(tab.getAttribute('data-tab'));
                });
            });

            // Setup form submissions
            const forms = document.querySelectorAll('#settings form');
            forms.forEach(form => {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.saveSettings(form);
                });
            });
        }

        /**
         * Load section data
         */
        loadSectionData(sectionId) {
            switch (sectionId) {
                case 'overview':
                    this.loadOverviewData();
                    break;
                case 'extractions':
                    this.loadExtractions();
                    break;
                case 'batch':
                    this.loadBatchJobs();
                    break;
                case 'api':
                    this.loadAPIKeys();
                    break;
                case 'templates':
                    this.loadTemplates();
                    break;
                case 'analytics':
                    this.loadAnalytics();
                    break;
                case 'settings':
                    this.loadSettings();
                    break;
            }
        }

        /**
         * Load overview data
         */
        loadOverviewData() {
            console.log('[Dashboard] Loading overview data...');
            
            // Load recent activity
            this.loadRecentActivity();
            
            // Load charts
            this.loadCharts();
        }

        /**
         * Load recent activity
         */
        loadRecentActivity() {
            const container = document.getElementById('recentActivity');
            if (!container) return;

            const activities = this.mockData.recentExtractions.slice(0, 5);
            
            container.innerHTML = '';
            
            activities.forEach(item => {
                const activityItem = document.createElement('div');
                activityItem.className = 'activity-item';
                activityItem.style.cssText = `
                    display: flex;
                    align-items: center;
                    padding: 16px;
                    border-bottom: 1px solid #e5e7eb;
                    transition: background 0.2s;
                `;
                
                activityItem.addEventListener('mouseenter', () => {
                    activityItem.style.background = '#f9fafb';
                });
                activityItem.addEventListener('mouseleave', () => {
                    activityItem.style.background = 'transparent';
                });

                const icon = document.createElement('div');
                icon.style.cssText = `
                    width: 40px;
                    height: 40px;
                    border-radius: 8px;
                    background: ${item.status === 'success' ? '#d1fae5' : '#fee2e2'};
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 16px;
                    font-size: 20px;
                `;
                icon.textContent = item.status === 'success' ? '✓' : '✕';

                const content = document.createElement('div');
                content.style.cssText = 'flex: 1;';
                
                const title = document.createElement('div');
                title.style.cssText = 'font-weight: 500; color: #111827; margin-bottom: 4px;';
                title.textContent = item.merchant || 'Receipt';
                
                const details = document.createElement('div');
                details.style.cssText = 'font-size: 14px; color: #6b7280;';
                details.textContent = `${item.total} • ${item.date}`;
                
                content.appendChild(title);
                content.appendChild(details);

                const badge = document.createElement('span');
                badge.style.cssText = `
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 500;
                    background: ${item.status === 'success' ? '#d1fae5' : '#fee2e2'};
                    color: ${item.status === 'success' ? '#065f46' : '#991b1b'};
                `;
                badge.textContent = item.status;

                activityItem.appendChild(icon);
                activityItem.appendChild(content);
                activityItem.appendChild(badge);

                container.appendChild(activityItem);
            });
        }

        /**
         * Load charts
         */
        loadCharts() {
            // Activity chart
            this.loadActivityChart();
            
            // Model usage chart
            this.loadModelChart();
        }

        /**
         * Load activity chart
         */
        loadActivityChart() {
            const canvas = document.getElementById('activityChart');
            if (!canvas || !window.Chart) return;

            const data = this.mockData.activityData;
            
            if (this.charts.activityChart) {
                this.charts.activityChart.destroy();
            }

            this.charts.activityChart = new Chart(canvas, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Extractions',
                        data: data.values,
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
                            display: false
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

        /**
         * Load model usage chart
         */
        loadModelChart() {
            const canvas = document.getElementById('modelChart');
            if (!canvas || !window.Chart) return;

            const data = this.mockData.modelUsage;
            
            if (this.charts.modelChart) {
                this.charts.modelChart.destroy();
            }

            this.charts.modelChart = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.values,
                        backgroundColor: [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b',
                            '#ef4444'
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

        /**
         * Load extractions
         */
        loadExtractions() {
            console.log('[Dashboard] Loading extractions...');
            
            const tbody = document.querySelector('#extractionsTable tbody');
            if (!tbody) return;

            tbody.innerHTML = '';
            
            this.mockData.recentExtractions.forEach((item, index) => {
                const tr = document.createElement('tr');
                
                tr.innerHTML = `
                    <td><input type="checkbox" data-id="${item.id}"></td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Crect fill='%23f3f4f6' width='40' height='40'/%3E%3C/svg%3E" 
                                 style="width: 40px; height: 40px; border-radius: 6px;" alt="Receipt">
                            <span>Receipt #${item.id.slice(-6)}</span>
                        </div>
                    </td>
                    <td>${item.merchant || 'N/A'}</td>
                    <td>$${item.total}</td>
                    <td>${item.date}</td>
                    <td><span style="padding: 4px 8px; border-radius: 6px; background: #dbeafe; color: #1e40af; font-size: 12px;">${item.model}</span></td>
                    <td><span class="badge badge-${item.status}">${item.status}</span></td>
                    <td>
                        <button class="btn-icon" onclick="DashboardCtrl.viewExtraction('${item.id}')" title="View">👁️</button>
                        <button class="btn-icon" onclick="DashboardCtrl.downloadExtraction('${item.id}')" title="Download">⬇️</button>
                        <button class="btn-icon" onclick="DashboardCtrl.deleteExtraction('${item.id}')" title="Delete">🗑️</button>
                    </td>
                `;
                
                tbody.appendChild(tr);
            });
        }

        /**
         * Load batch jobs
         */
        loadBatchJobs() {
            console.log('[Dashboard] Loading batch jobs...');
            
            const queueContainer = document.getElementById('batchQueue');
            const historyContainer = document.getElementById('batchHistory');
            
            if (queueContainer) {
                queueContainer.innerHTML = '<p style="color: #6b7280; padding: 20px;">No batches in queue</p>';
            }
            
            if (historyContainer) {
                historyContainer.innerHTML = '';
                
                this.mockData.batchJobs.forEach(job => {
                    const jobCard = this.createBatchJobCard(job);
                    historyContainer.appendChild(jobCard);
                });
            }
        }

        /**
         * Create batch job card
         */
        createBatchJobCard(job) {
            const card = document.createElement('div');
            card.className = 'batch-job-card';
            card.style.cssText = `
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 12px;
            `;

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h4 style="margin: 0; font-size: 16px;">${job.name}</h4>
                    <span style="padding: 4px 12px; border-radius: 12px; background: ${job.status === 'completed' ? '#d1fae5' : '#fee2e2'}; 
                                 color: ${job.status === 'completed' ? '#065f46' : '#991b1b'}; font-size: 12px; font-weight: 500;">
                        ${job.status}
                    </span>
                </div>
                <div style="font-size: 14px; color: #6b7280; margin-bottom: 12px;">
                    ${job.processed} / ${job.total} files processed
                </div>
                <div style="background: #e5e7eb; height: 6px; border-radius: 3px; overflow: hidden;">
                    <div style="background: #3b82f6; height: 100%; width: ${(job.processed / job.total) * 100}%;"></div>
                </div>
                <div style="margin-top: 12px; font-size: 12px; color: #9ca3af;">
                    ${job.date}
                </div>
            `;

            return card;
        }

        /**
         * Load API keys
         */
        loadAPIKeys() {
            console.log('[Dashboard] Loading API keys...');
            
            const container = document.getElementById('apiKeysList');
            if (!container) return;

            container.innerHTML = '';
            
            this.mockData.apiKeys.forEach(key => {
                const keyCard = this.createAPIKeyCard(key);
                container.appendChild(keyCard);
            });
        }

        /**
         * Create API key card
         */
        createAPIKeyCard(key) {
            const card = document.createElement('div');
            card.className = 'api-key-card';
            card.style.cssText = `
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 16px;
            `;

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
                    <div>
                        <h4 style="margin: 0 0 8px 0; font-size: 16px;">${key.name}</h4>
                        <code style="background: #f3f4f6; padding: 6px 12px; border-radius: 6px; font-size: 12px;">
                            ${key.key}
                        </code>
                    </div>
                    <button class="btn-icon" onclick="DashboardCtrl.deleteAPIKey('${key.id}')" title="Delete">🗑️</button>
                </div>
                <div style="display: flex; gap: 20px; font-size: 14px; color: #6b7280;">
                    <div>Created: ${key.created}</div>
                    <div>Last used: ${key.lastUsed}</div>
                    <div>Requests: ${key.requests}</div>
                </div>
            `;

            return card;
        }

        /**
         * Load templates
         */
        loadTemplates() {
            console.log('[Dashboard] Loading templates...');
            
            const container = document.getElementById('templatesGrid');
            if (!container) return;

            container.innerHTML = '';
            container.style.cssText = 'display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px;';
            
            this.mockData.templates.forEach(template => {
                const card = this.createTemplateCard(template);
                container.appendChild(card);
            });
        }

        /**
         * Create template card
         */
        createTemplateCard(template) {
            const card = document.createElement('div');
            card.className = 'template-card';
            card.style.cssText = `
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 20px;
                cursor: pointer;
                transition: all 0.2s;
            `;

            card.classList.add('template-card-hover');

            card.innerHTML = `
                <h4 style="margin: 0 0 12px 0; font-size: 16px;">${template.name}</h4>
                <p style="margin: 0 0 16px 0; color: #6b7280; font-size: 14px;">${template.description}</p>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #9ca3af;">
                    <span>${template.fields} fields</span>
                    <span>${template.used} uses</span>
                </div>
            `;

            return card;
        }

        /**
         * Load analytics
         */
        loadAnalytics(period = 'last-30-days') {
            console.log('[Dashboard] Loading analytics for period:', period);
            
            // Load trends chart
            const trendsCanvas = document.getElementById('trendsChart');
            if (trendsCanvas && window.Chart) {
                if (this.charts.trendsChart) {
                    this.charts.trendsChart.destroy();
                }

                this.charts.trendsChart = new Chart(trendsCanvas, {
                    type: 'line',
                    data: {
                        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                        datasets: [{
                            label: 'Extractions',
                            data: [45, 62, 58, 71],
                            borderColor: '#3b82f6',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }

            // Load confidence chart
            const confidenceCanvas = document.getElementById('confidenceChart');
            if (confidenceCanvas && window.Chart) {
                if (this.charts.confidenceChart) {
                    this.charts.confidenceChart.destroy();
                }

                this.charts.confidenceChart = new Chart(confidenceCanvas, {
                    type: 'bar',
                    data: {
                        labels: ['90-100%', '80-90%', '70-80%', '60-70%'],
                        datasets: [{
                            label: 'Count',
                            data: [120, 45, 15, 5],
                            backgroundColor: '#3b82f6'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }

            // Load top merchants
            const merchantsList = document.getElementById('merchantsList');
            if (merchantsList) {
                merchantsList.innerHTML = '';
                
                const merchants = [
                    { name: 'Walmart', count: 42, total: 1247.50 },
                    { name: 'Amazon', count: 38, total: 982.30 },
                    { name: 'Target', count: 25, total: 675.20 },
                    { name: 'Costco', count: 18, total: 1532.40 },
                    { name: 'Home Depot', count: 15, total: 456.80 }
                ];

                merchants.forEach(merchant => {
                    const item = document.createElement('div');
                    item.style.cssText = `
                        display: flex;
                        justify-content: space-between;
                        padding: 12px 0;
                        border-bottom: 1px solid #e5e7eb;
                    `;
                    item.innerHTML = `
                        <div>
                            <div style="font-weight: 500; color: #111827;">${merchant.name}</div>
                            <div style="font-size: 12px; color: #6b7280;">${merchant.count} receipts</div>
                        </div>
                        <div style="font-weight: 600; color: #111827;">$${merchant.total.toFixed(2)}</div>
                    `;
                    merchantsList.appendChild(item);
                });
            }
        }

        /**
         * Load settings
         */
        loadSettings() {
            console.log('[Dashboard] Loading settings...');
            
            // Load from localStorage or use defaults
            const settings = JSON.parse(localStorage.getItem('user_settings') || '{}');
            
            // Populate form fields
            const inputs = document.querySelectorAll('#settings input, #settings select');
            inputs.forEach(input => {
                if (settings[input.id]) {
                    if (input.type === 'checkbox') {
                        input.checked = settings[input.id];
                    } else {
                        input.value = settings[input.id];
                    }
                }
            });
        }

        /**
         * Switch settings tab
         */
        switchSettingsTab(tabId) {
            // Update tab buttons
            document.querySelectorAll('.settings-tab').forEach(tab => {
                tab.classList.remove('active');
                if (tab.getAttribute('data-tab') === tabId) {
                    tab.classList.add('active');
                }
            });

            // Update panels
            document.querySelectorAll('.settings-panel').forEach(panel => {
                panel.classList.remove('active');
                panel.style.display = 'none';
            });

            const targetPanel = document.getElementById(tabId);
            if (targetPanel) {
                targetPanel.classList.add('active');
                targetPanel.style.display = 'block';
            }
        }

        /**
         * Save settings
         */
        saveSettings(form) {
            const formData = new FormData(form);
            const settings = Object.fromEntries(formData.entries());
            
            // Save to localStorage
            localStorage.setItem('user_settings', JSON.stringify(settings));
            
            // Show success message
            if (window.UIComponents) {
                window.UIComponents.alert('Settings saved successfully!', 'Success', 'success');
            } else {
                alert('Settings saved successfully!');
            }
        }

        /**
         * Setup event listeners
         */
        setupEventListeners() {
            // Handle logout
            const logoutBtns = document.querySelectorAll('[data-action="logout"]');
            logoutBtns.forEach(btn => {
                btn.addEventListener('click', () => this.logout());
            });
        }

        /**
         * Show quick extract modal
         */
        showQuickExtractModal() {
            if (!window.UIComponents) {
                alert('Upload feature coming soon!');
                return;
            }

            const content = document.createElement('div');
            content.innerHTML = `
                <div class="upload-zone" style="border: 2px dashed #cbd5e1; border-radius: 8px; padding: 40px; text-align: center; background: #f9fafb;">
                    <div style="font-size: 48px; margin-bottom: 16px;">📄</div>
                    <h3 style="margin: 0 0 8px 0;">Drop your receipt here</h3>
                    <p style="margin: 0 0 16px 0; color: #6b7280;">or click to browse</p>
                    <input type="file" accept="image/*" style="display: none;" id="quickUploadInput">
                    <button class="btn btn-primary" onclick="document.getElementById('quickUploadInput').click()">Choose File</button>
                </div>
            `;

            window.UIComponents.createModal({
                title: 'Quick Extract',
                content,
                size: 'medium'
            });
        }

        /**
         * Generate mock data
         */
        generateMockData() {
            return {
                recentExtractions: [
                    { id: 'ext_001', merchant: 'Walmart', total: '45.67', date: '2024-12-01', model: 'Tesseract', status: 'success' },
                    { id: 'ext_002', merchant: 'Amazon', total: '129.99', date: '2024-12-02', model: 'EasyOCR', status: 'success' },
                    { id: 'ext_003', merchant: 'Target', total: '78.34', date: '2024-12-03', model: 'Florence-2', status: 'success' },
                    { id: 'ext_004', merchant: 'Costco', total: '234.56', date: '2024-12-04', model: 'Tesseract', status: 'success' },
                    { id: 'ext_005', merchant: 'Home Depot', total: '156.78', date: '2024-12-05', model: 'PaddleOCR', status: 'failed' }
                ],
                activityData: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    values: [12, 19, 15, 25, 22, 18, 20]
                },
                modelUsage: {
                    labels: ['Tesseract', 'EasyOCR', 'Florence-2', 'PaddleOCR'],
                    values: [45, 30, 15, 10]
                },
                apiKeys: [
                    { id: 'key_001', name: 'Production API Key', key: 'sk_live_****************************', created: '2024-01-15', lastUsed: '2024-12-07', requests: 1247 },
                    { id: 'key_002', name: 'Development Key', key: 'sk_test_****************************', created: '2024-03-10', lastUsed: '2024-12-05', requests: 432 }
                ],
                templates: [
                    { id: 'tmp_001', name: 'Standard Receipt', description: 'Basic receipt template for retail stores', fields: 8, used: 145 },
                    { id: 'tmp_002', name: 'Restaurant Bill', description: 'Template for restaurant receipts with tips', fields: 12, used: 89 },
                    { id: 'tmp_003', name: 'Gas Station', description: 'Template for gas station receipts', fields: 6, used: 67 }
                ],
                batchJobs: [
                    { id: 'batch_001', name: 'Monthly Receipts - November', total: 45, processed: 45, status: 'completed', date: '2024-11-30' },
                    { id: 'batch_002', name: 'Q3 Tax Documents', total: 120, processed: 98, status: 'processing', date: '2024-12-01' }
                ]
            };
        }

        /**
         * Action methods (called from HTML)
         */
        viewExtraction(id) {
            console.log('View extraction:', id);
            if (window.UIComponents) {
                window.UIComponents.alert('Viewing extraction details...', 'Extraction Details');
            }
        }

        downloadExtraction(id) {
            console.log('Download extraction:', id);
            if (window.UIComponents) {
                window.UIComponents.alert('Download started!', 'Download', 'success');
            }
        }

        deleteExtraction(id) {
            console.log('Delete extraction:', id);
            if (window.UIComponents) {
                window.UIComponents.confirm('Are you sure you want to delete this extraction?', 'Confirm Delete')
                    .then(confirmed => {
                        if (confirmed) {
                            window.UIComponents.alert('Extraction deleted successfully!', 'Success', 'success');
                        }
                    });
            }
        }

        deleteAPIKey(id) {
            console.log('Delete API key:', id);
            if (window.UIComponents) {
                window.UIComponents.confirm('Are you sure you want to delete this API key? This action cannot be undone.', 'Confirm Delete')
                    .then(confirmed => {
                        if (confirmed) {
                            window.UIComponents.alert('API key deleted successfully!', 'Success', 'success');
                            this.loadAPIKeys();
                        }
                    });
            }
        }

        createAPIKey() {
            console.log('Create API key');
            if (window.UIComponents) {
                const content = document.createElement('div');
                const nameField = window.UIComponents.createFormField({
                    type: 'text',
                    label: 'Key Name',
                    name: 'keyName',
                    placeholder: 'My API Key',
                    required: true
                });
                
                const descField = window.UIComponents.createFormField({
                    type: 'textarea',
                    label: 'Description',
                    name: 'description',
                    placeholder: 'Optional description...'
                });

                content.appendChild(nameField.wrapper);
                content.appendChild(descField.wrapper);

                const footer = document.createElement('div');
                const createBtn = window.UIComponents.createButton('Create Key', 'primary');
                createBtn.addEventListener('click', () => {
                    window.UIComponents.alert('API key created successfully!', 'Success', 'success');
                    this.loadAPIKeys();
                });
                footer.appendChild(createBtn);

                window.UIComponents.createModal({
                    title: 'Create API Key',
                    content,
                    footer,
                    size: 'medium'
                });
            }
        }

        createTemplate() {
            console.log('Create template');
            if (window.UIComponents) {
                window.UIComponents.alert('Template creation coming soon!', 'Info', 'info');
            }
        }

        exportExtractions() {
            console.log('Export extractions');
            if (window.DataManager) {
                window.DataManager.exportData('csv');
            } else {
                alert('Export feature coming soon!');
            }
        }

        searchExtractions(query) {
            console.log('Search:', query);
            if (window.DataManager) {
                window.DataManager.search(query);
            }
        }

        showFilterModal() {
            console.log('Show filter modal');
            if (window.UIComponents) {
                window.UIComponents.alert('Filter feature coming soon!', 'Info', 'info');
            }
        }

        showNewBatchModal() {
            console.log('Show new batch modal');
            if (window.UIComponents) {
                window.UIComponents.alert('Batch upload coming soon!', 'Info', 'info');
            }
        }

        logout() {
            if (confirm('Are you sure you want to log out?')) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_data');
                window.location.href = 'index.html';
            }
        }
    }

    // Create global instance
    window.DashboardCtrl = new DashboardController();

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = DashboardController;
    }

})(window);
