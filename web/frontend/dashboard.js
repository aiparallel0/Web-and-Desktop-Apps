/**
 * Dashboard JavaScript
 * Handles all dashboard interactions, navigation, and data management
 */

// =============================================================================
// STATE MANAGEMENT
// =============================================================================

const DashboardState = {
    currentSection: 'overview',
    user: {
        name: 'John Doe',
        email: 'john@example.com',
        plan: 'Pro',
        avatar: 'JD'
    },
    stats: {
        totalExtractions: 1247,
        successRate: 97.3,
        avgProcessingTime: 2.3,
        apiCalls: 3429
    },
    recentExtractions: [],
    apiKeys: [],
    templates: [],
    batchJobs: []
};

// =============================================================================
// NAVIGATION
// =============================================================================

class DashboardNavigation {
    constructor() {
        this.setupSidebarLinks();
        this.setupMobileMenu();
    }

    setupSidebarLinks() {
        const links = document.querySelectorAll('.sidebar-link');
        links.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
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

    navigateToSection(sectionId) {
        // Update sidebar
        document.querySelectorAll('.sidebar-link').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.section === sectionId) {
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
            DashboardState.currentSection = sectionId;
            
            // Update URL
            history.pushState(null, null, `#${sectionId}`);
            
            // Load section data
            this.loadSectionData(sectionId);
        }
    }

    loadSectionData(sectionId) {
        switch (sectionId) {
            case 'overview':
                Dashboard.loadOverview();
                break;
            case 'extractions':
                Dashboard.loadExtractions();
                break;
            case 'batch':
                Dashboard.loadBatchJobs();
                break;
            case 'api':
                Dashboard.loadApiKeys();
                break;
            case 'templates':
                Dashboard.loadTemplates();
                break;
            case 'analytics':
                Dashboard.loadAnalytics();
                break;
        }
    }

    setupMobileMenu() {
        // Add mobile menu toggle if needed
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'mobile-menu-toggle btn btn-ghost btn-sm';
        toggleBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>';
        
        // Add to nav on mobile
        if (window.innerWidth <= 768) {
            const navContainer = document.querySelector('.nav-container');
            navContainer.insertBefore(toggleBtn, navContainer.firstChild);
            
            toggleBtn.addEventListener('click', () => {
                const sidebar = document.querySelector('.dashboard-sidebar');
                sidebar.classList.toggle('open');
            });
        }
    }
}

// =============================================================================
// DASHBOARD CORE
// =============================================================================

const Dashboard = {
    charts: {},

    init() {
        console.log('Initializing Dashboard...');
        
        // Initialize navigation
        this.navigation = new DashboardNavigation();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load initial data
        this.loadOverview();
        
        // Initialize charts
        this.initializeCharts();
        
        console.log('Dashboard initialized successfully');
    },

    setupEventListeners() {
        // Quick extract button
        const quickExtractBtn = document.getElementById('quickExtractBtn');
        if (quickExtractBtn) {
            quickExtractBtn.addEventListener('click', () => this.openQuickExtractModal());
        }

        // Settings tabs
        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchSettingsTab(tab.dataset.tab);
            });
        });

        // Modal close
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.closest('.modal').classList.remove('active');
            });
        });

        // Dark mode toggle
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (darkModeToggle) {
            darkModeToggle.addEventListener('change', (e) => {
                this.toggleDarkMode(e.target.checked);
            });
        }
    },

    // =============================================================================
    // OVERVIEW SECTION
    // =============================================================================

    loadOverview() {
        this.loadRecentActivity();
        this.updateStats();
    },

    updateStats() {
        // Update stat values with animation
        this.animateValue('Total Extractions', 0, DashboardState.stats.totalExtractions, 1000);
    },

    animateValue(label, start, end, duration) {
        const element = Array.from(document.querySelectorAll('.stat-content h3'))
            .find(el => el.textContent === label);
        
        if (!element) return;
        
        const valueElement = element.nextElementSibling;
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if (current >= end) {
                current = end;
                clearInterval(timer);
            }
            valueElement.textContent = Math.floor(current).toLocaleString();
        }, 16);
    },

    loadRecentActivity() {
        const recentActivity = document.getElementById('recentActivity');
        if (!recentActivity) return;

        const mockData = [
            {
                merchant: 'Whole Foods Market',
                total: 127.45,
                date: '2024-01-15',
                model: 'Florence-2 AI',
                status: 'success'
            },
            {
                merchant: 'Target',
                total: 89.99,
                date: '2024-01-15',
                model: 'Tesseract OCR',
                status: 'success'
            },
            {
                merchant: 'Starbucks',
                total: 12.50,
                date: '2024-01-14',
                model: 'EasyOCR',
                status: 'success'
            },
            {
                merchant: 'Amazon',
                total: 245.00,
                date: '2024-01-14',
                model: 'PaddleOCR',
                status: 'success'
            },
            {
                merchant: 'Best Buy',
                total: 599.99,
                date: '2024-01-13',
                model: 'Florence-2 AI',
                status: 'success'
            }
        ];

        recentActivity.innerHTML = mockData.map(item => `
            <div class="activity-item">
                <div class="activity-thumb">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                </div>
                <div class="activity-details">
                    <div class="activity-merchant">${item.merchant}</div>
                    <div class="activity-meta">${item.date} • ${item.model}</div>
                </div>
                <div class="activity-amount">$${item.total.toFixed(2)}</div>
            </div>
        `).join('');
    },

    // =============================================================================
    // EXTRACTIONS SECTION
    // =============================================================================

    loadExtractions() {
        const tableBody = document.querySelector('#extractionsTable tbody');
        if (!tableBody) return;

        const mockData = [
            {
                id: 1,
                merchant: 'Whole Foods Market',
                total: 127.45,
                date: '2024-01-15',
                model: 'Florence-2',
                status: 'success'
            },
            {
                id: 2,
                merchant: 'Target',
                total: 89.99,
                date: '2024-01-15',
                model: 'Tesseract',
                status: 'success'
            },
            {
                id: 3,
                merchant: 'Starbucks',
                total: 12.50,
                date: '2024-01-14',
                model: 'EasyOCR',
                status: 'success'
            }
        ];

        tableBody.innerHTML = mockData.map(item => `
            <tr>
                <td><input type="checkbox"></td>
                <td>
                    <div class="table-thumb">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                        </svg>
                    </div>
                </td>
                <td>${item.merchant}</td>
                <td>$${item.total.toFixed(2)}</td>
                <td>${item.date}</td>
                <td>${item.model}</td>
                <td><span class="status-badge ${item.status}">${item.status}</span></td>
                <td>
                    <button class="btn btn-ghost btn-sm">View</button>
                    <button class="btn btn-ghost btn-sm">Download</button>
                </td>
            </tr>
        `).join('');
    },

    // =============================================================================
    // BATCH PROCESSING
    // =============================================================================

    loadBatchJobs() {
        const queueList = document.getElementById('batchQueue');
        const historyList = document.getElementById('batchHistory');
        
        if (queueList) {
            queueList.innerHTML = `
                <div class="queue-item">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <strong>Batch #1247</strong>
                        <span>45 / 50 receipts</span>
                    </div>
                    <div class="batch-progress">
                        <div class="batch-progress-bar" style="width: 90%"></div>
                    </div>
                    <div style="font-size: 0.875rem; color: var(--color-gray-500); margin-top: 8px;">
                        Processing... ETA: 2 minutes
                    </div>
                </div>
            `;
        }
        
        if (historyList) {
            historyList.innerHTML = `
                <div class="history-item">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <strong>Batch #1246</strong>
                        <span class="status-badge success">Completed</span>
                    </div>
                    <div style="font-size: 0.875rem; color: var(--color-gray-500);">
                        100 receipts • Completed 2 hours ago
                    </div>
                </div>
            `;
        }
    },

    // =============================================================================
    // API KEYS
    // =============================================================================

    loadApiKeys() {
        const apiKeysList = document.getElementById('apiKeysList');
        if (!apiKeysList) return;

        apiKeysList.innerHTML = `
            <div class="api-key-card">
                <div class="api-key-header">
                    <div>
                        <div class="api-key-name">Production API Key</div>
                        <div class="api-key-meta">Created on Jan 1, 2024</div>
                    </div>
                    <button class="btn btn-ghost btn-sm">Delete</button>
                </div>
                <div class="api-key-value">
                    <code>re_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</code>
                    <button class="btn btn-ghost btn-sm" onclick="copyToClipboard(this.previousElementSibling.textContent)">Copy</button>
                </div>
                <div class="api-key-meta">Last used: 2 hours ago • 1,234 requests this month</div>
            </div>
        `;
    },

    // =============================================================================
    // TEMPLATES
    // =============================================================================

    loadTemplates() {
        const templatesGrid = document.getElementById('templatesGrid');
        if (!templatesGrid) return;

        const templates = [
            { name: 'Grocery Receipt', icon: '🛒', description: 'Optimized for grocery store receipts' },
            { name: 'Restaurant Receipt', icon: '🍽️', description: 'Extracts tips and itemized food items' },
            { name: 'Retail Receipt', icon: '🏪', description: 'For general retail transactions' },
            { name: 'Gas Station', icon: '⛽', description: 'Specialized for fuel receipts' }
        ];

        templatesGrid.innerHTML = templates.map(template => `
            <div class="template-card">
                <div class="template-icon">${template.icon}</div>
                <div class="template-name">${template.name}</div>
                <div class="template-description">${template.description}</div>
            </div>
        `).join('');
    },

    // =============================================================================
    // ANALYTICS
    // =============================================================================

    loadAnalytics() {
        // Load analytics charts and data
        setTimeout(() => {
            this.renderAnalyticsCharts();
        }, 100);
    },

    // =============================================================================
    // CHARTS
    // =============================================================================

    initializeCharts() {
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded');
            return;
        }

        // Activity Chart
        const activityCtx = document.getElementById('activityChart');
        if (activityCtx) {
            this.charts.activity = new Chart(activityCtx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Extractions',
                        data: [12, 19, 15, 25, 22, 18, 24],
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
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Model Usage Chart
        const modelCtx = document.getElementById('modelChart');
        if (modelCtx) {
            this.charts.model = new Chart(modelCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Tesseract', 'EasyOCR', 'PaddleOCR', 'Florence-2'],
                    datasets: [{
                        data: [30, 25, 20, 25],
                        backgroundColor: [
                            '#3B82F6',
                            '#10B981',
                            '#F59E0B',
                            '#EF4444'
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
    },

    renderAnalyticsCharts() {
        // Render additional analytics charts
        console.log('Rendering analytics charts...');
    },

    // =============================================================================
    // SETTINGS
    // =============================================================================

    switchSettingsTab(tabId) {
        // Update tabs
        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.tab === tabId) {
                tab.classList.add('active');
            }
        });

        // Update panels
        document.querySelectorAll('.settings-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        
        const targetPanel = document.getElementById(tabId);
        if (targetPanel) {
            targetPanel.classList.add('active');
        }
    },

    toggleDarkMode(enabled) {
        if (enabled) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('dark_mode', 'true');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('dark_mode', 'false');
        }
    },

    // =============================================================================
    // MODALS
    // =============================================================================

    openQuickExtractModal() {
        const modal = document.getElementById('quickExtractModal');
        if (modal) {
            modal.classList.add('active');
        }
    }
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success');
    });
}

function showNotification(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: ${type === 'success' ? '#10B981' : '#3B82F6'};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// =============================================================================
// INITIALIZATION
// =============================================================================

// Initialize dashboard when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Dashboard.init());
} else {
    Dashboard.init();
}

// Export for debugging
window.Dashboard = Dashboard;
window.DashboardState = DashboardState;
