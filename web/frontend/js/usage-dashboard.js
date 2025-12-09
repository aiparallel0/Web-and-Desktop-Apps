/**
 * Usage Dashboard Component
 * 
 * Displays usage statistics, trial countdown, and upgrade CTAs
 */

class UsageDashboard {
    constructor() {
        this.usageData = null;
        this.trialData = null;
        this.init();
    }

    async init() {
        await this.loadUsageData();
        await this.loadTrialData();
        this.render();
        this.setupAutoRefresh();
    }

    async loadUsageData() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            const response = await fetch('/api/usage/stats', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                this.usageData = await response.json();
            }
        } catch (error) {
            console.error('Failed to load usage data:', error);
        }
    }

    async loadTrialData() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            const response = await fetch('/api/auth/trial-status', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.trialData = data.trial;
            }
        } catch (error) {
            console.error('Failed to load trial data:', error);
        }
    }

    render() {
        const container = document.getElementById('usage-dashboard');
        if (!container) return;

        container.innerHTML = this.generateHTML();
        this.attachEventListeners();
    }

    generateHTML() {
        const html = `
            <div class="usage-dashboard-container">
                ${this.renderTrialBanner()}
                ${this.renderUsageStats()}
                ${this.renderUpgradeCTA()}
            </div>
        `;
        return html;
    }

    renderTrialBanner() {
        if (!this.trialData || !this.trialData.is_active) {
            return '';
        }

        const daysRemaining = this.trialData.days_remaining;
        const urgencyClass = daysRemaining <= 3 ? 'urgent' : daysRemaining <= 7 ? 'warning' : 'normal';

        return `
            <div class="trial-banner ${urgencyClass}">
                <div class="trial-icon">🚀</div>
                <div class="trial-content">
                    <h3>Pro Trial Active</h3>
                    <p class="trial-countdown">
                        <strong>${daysRemaining} day${daysRemaining !== 1 ? 's' : ''}</strong> remaining
                    </p>
                    <p class="trial-message">
                        ${daysRemaining <= 3 
                            ? 'Your trial is ending soon! Upgrade now to keep your Pro features.' 
                            : 'Enjoy full access to all premium features.'}
                    </p>
                </div>
                ${daysRemaining <= 7 ? `
                    <button class="btn-upgrade-trial" onclick="window.usageDashboard.handleUpgrade()">
                        Upgrade Now
                    </button>
                ` : ''}
            </div>
        `;
    }

    renderUsageStats() {
        if (!this.usageData) {
            return '<div class="loading">Loading usage data...</div>';
        }

        const receiptsProcessed = this.usageData.receipts_processed || 0;
        const receiptsLimit = this.usageData.receipts_limit || 10;
        const usagePercentage = Math.min(100, Math.round((receiptsProcessed / receiptsLimit) * 100));
        const storageUsed = this.formatBytes(this.usageData.storage_used || 0);
        const storageLimit = this.formatBytes(this.usageData.storage_limit || 104857600); // 100 MB default

        const shouldShowUpgradePrompt = usagePercentage >= 75;
        const urgencyLevel = usagePercentage >= 90 ? 'critical' : usagePercentage >= 75 ? 'warning' : 'normal';

        return `
            <div class="usage-stats-card">
                <h3>Monthly Usage</h3>
                
                <div class="usage-stat">
                    <div class="stat-header">
                        <span class="stat-label">Receipts Processed</span>
                        <span class="stat-value">${receiptsProcessed} / ${receiptsLimit}</span>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar ${urgencyLevel}" style="width: ${usagePercentage}%">
                            <span class="progress-text">${usagePercentage}%</span>
                        </div>
                    </div>
                    ${shouldShowUpgradePrompt ? `
                        <div class="usage-alert ${urgencyLevel}">
                            ${urgencyLevel === 'critical' 
                                ? '⚠️ You\'re almost at your limit! Upgrade to continue processing.' 
                                : '⚡ You\'re using a lot this month. Consider upgrading for more capacity.'}
                        </div>
                    ` : ''}
                </div>

                <div class="usage-stat">
                    <div class="stat-header">
                        <span class="stat-label">Storage Used</span>
                        <span class="stat-value">${storageUsed} / ${storageLimit}</span>
                    </div>
                </div>

                <div class="usage-reset-info">
                    <small>Usage resets on ${this.usageData.reset_date || 'the 1st of next month'}</small>
                </div>

                ${shouldShowUpgradePrompt ? `
                    <button class="btn-upgrade-usage" onclick="window.usageDashboard.handleUpgrade()">
                        View Upgrade Options
                    </button>
                ` : ''}
            </div>
        `;
    }

    renderUpgradeCTA() {
        if (!this.usageData || this.usageData.plan === 'business' || this.usageData.plan === 'enterprise') {
            return ''; // Don't show CTA for high-tier plans
        }

        const currentPlan = this.usageData.plan || 'free';
        const isTrialActive = this.trialData && this.trialData.is_active;

        return `
            <div class="upgrade-cta-card">
                <h3>Unlock More Power</h3>
                <p>Get more receipts, storage, and premium features with Pro.</p>
                
                <div class="plan-features">
                    <div class="feature-item">✓ <strong>500 receipts</strong> per month</div>
                    <div class="feature-item">✓ <strong>5GB</strong> cloud storage</div>
                    <div class="feature-item">✓ All 7 premium OCR models</div>
                    <div class="feature-item">✓ Batch processing & API access</div>
                    <div class="feature-item">✓ Priority email support</div>
                </div>

                <div class="pricing-info">
                    <span class="price">$19<small>/month</small></span>
                </div>

                <button class="btn-upgrade-primary" onclick="window.usageDashboard.handleUpgrade()">
                    ${isTrialActive ? 'Continue with Pro' : 'Upgrade to Pro'}
                </button>

                <p class="upgrade-subtext">
                    ${isTrialActive ? 'Keep your trial features forever' : 'Start with a 14-day free trial'}
                </p>
            </div>
        `;
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }

    handleUpgrade() {
        // Track analytics event
        if (window.trackConversion) {
            window.trackConversion('upgrade_clicked', {
                source: 'usage_dashboard',
                plan: this.usageData?.plan || 'free',
                trial_active: this.trialData?.is_active || false
            });
        }

        // Redirect to pricing page
        window.location.href = '/pricing.html?source=dashboard';
    }

    setupAutoRefresh() {
        // Refresh usage data every 5 minutes
        setInterval(() => {
            this.loadUsageData();
            this.loadTrialData();
            this.render();
        }, 5 * 60 * 1000);
    }

    attachEventListeners() {
        // Additional event listeners can be added here
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.usageDashboard = new UsageDashboard();
    });
} else {
    window.usageDashboard = new UsageDashboard();
}
