/**
 * Referral Dashboard Component
 * 
 * Displays referral stats, sharing options, and rewards progress
 */

class ReferralDashboard {
    constructor() {
        this.referralData = null;
        this.init();
    }

    async init() {
        await this.loadReferralData();
        this.render();
        this.setupEventListeners();
    }

    async loadReferralData() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            const response = await fetch('/api/auth/referral-stats', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.referralData = data.referrals;
            }
        } catch (error) {
            console.error('Failed to load referral data:', error);
        }
    }

    render() {
        const container = document.getElementById('referral-dashboard');
        if (!container) return;

        container.innerHTML = this.generateHTML();
        this.attachEventListeners();
    }

    generateHTML() {
        if (!this.referralData) {
            return '<div class="loading">Loading referral data...</div>';
        }

        return `
            <div class="referral-dashboard-container">
                ${this.renderReferralHeader()}
                ${this.renderProgressTracker()}
                ${this.renderShareOptions()}
                ${this.renderReferralStats()}
            </div>
        `;
    }

    renderReferralHeader() {
        const code = this.referralData.referral_code || 'LOADING';
        const baseUrl = window.location.origin;
        const referralUrl = `${baseUrl}/register.html?ref=${code}`;

        return `
            <div class="referral-header-card">
                <h3>🎁 Refer Friends, Earn Free Months</h3>
                <p class="referral-description">
                    Share your unique referral code and earn 1 month of free Pro access for every 3 friends who sign up!
                </p>

                <div class="referral-code-display">
                    <label>Your Referral Code</label>
                    <div class="code-container">
                        <input 
                            type="text" 
                            id="referral-code-input" 
                            value="${code}" 
                            readonly
                            class="code-input"
                        />
                        <button 
                            class="btn-copy-code" 
                            onclick="window.referralDashboard.copyCode('${code}')"
                            title="Copy code"
                        >
                            📋 Copy
                        </button>
                    </div>
                </div>

                <div class="referral-url-display">
                    <label>Referral Link</label>
                    <div class="url-container">
                        <input 
                            type="text" 
                            id="referral-url-input" 
                            value="${referralUrl}" 
                            readonly
                            class="url-input"
                        />
                        <button 
                            class="btn-copy-url" 
                            onclick="window.referralDashboard.copyUrl('${referralUrl}')"
                            title="Copy link"
                        >
                            🔗 Copy Link
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderProgressTracker() {
        const completed = this.referralData.completed_referrals || 0;
        const pending = this.referralData.pending_referrals || 0;
        const progress = this.referralData.progress_to_next_reward || 0;
        const needed = this.referralData.referrals_needed_for_reward || 3;
        const rewardsEarned = this.referralData.total_rewards_earned || 0;
        const rewardMonths = this.referralData.reward_months_earned || 0;

        const progressPercentage = Math.round((progress / 3) * 100);

        return `
            <div class="referral-progress-card">
                <h4>Rewards Progress</h4>
                
                ${rewardMonths > 0 ? `
                    <div class="rewards-earned-banner">
                        🎉 You've earned <strong>${rewardMonths} month${rewardMonths !== 1 ? 's' : ''}</strong> of free Pro access!
                    </div>
                ` : ''}

                <div class="progress-tracker">
                    <div class="progress-info">
                        <span>${progress} of 3 referrals</span>
                        <span class="progress-percentage">${progressPercentage}%</span>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar" style="width: ${progressPercentage}%"></div>
                    </div>
                    <p class="progress-message">
                        ${needed === 0 
                            ? '🎊 Reward earned! Keep referring to earn more.' 
                            : `${needed} more referral${needed !== 1 ? 's' : ''} to earn 1 free month!`}
                    </p>
                </div>

                <div class="referral-counts">
                    <div class="count-item">
                        <span class="count-value">${completed}</span>
                        <span class="count-label">Successful</span>
                    </div>
                    <div class="count-item">
                        <span class="count-value">${pending}</span>
                        <span class="count-label">Pending</span>
                    </div>
                    <div class="count-item">
                        <span class="count-value">${rewardsEarned}</span>
                        <span class="count-label">Rewards</span>
                    </div>
                </div>
            </div>
        `;
    }

    renderShareOptions() {
        const code = this.referralData.referral_code;
        const baseUrl = window.location.origin;
        const referralUrl = encodeURIComponent(`${baseUrl}/register.html?ref=${code}`);
        const shareText = encodeURIComponent(`Check out Receipt Extractor - AI-powered receipt text extraction! Use my code ${code} to sign up.`);

        return `
            <div class="share-options-card">
                <h4>Share Your Code</h4>
                <div class="share-buttons">
                    <button 
                        class="share-btn email-btn" 
                        onclick="window.referralDashboard.shareViaEmail('${code}')"
                    >
                        📧 Email
                    </button>
                    <button 
                        class="share-btn twitter-btn" 
                        onclick="window.referralDashboard.shareViaTwitter('${shareText}', '${referralUrl}')"
                    >
                        🐦 Twitter
                    </button>
                    <button 
                        class="share-btn linkedin-btn" 
                        onclick="window.referralDashboard.shareViaLinkedIn('${referralUrl}')"
                    >
                        💼 LinkedIn
                    </button>
                    <button 
                        class="share-btn facebook-btn" 
                        onclick="window.referralDashboard.shareViaFacebook('${referralUrl}')"
                    >
                        📘 Facebook
                    </button>
                </div>
            </div>
        `;
    }

    renderReferralStats() {
        return `
            <div class="referral-info-card">
                <h4>How It Works</h4>
                <ol class="referral-steps">
                    <li>Share your unique referral code or link with friends</li>
                    <li>They sign up using your code and verify their email</li>
                    <li>For every 3 successful referrals, you earn 1 month of free Pro access</li>
                </ol>
                <p class="referral-terms">
                    <small>Rewards are automatically applied to your account. See our <a href="/terms.html">terms</a> for details.</small>
                </p>
            </div>
        `;
    }

    async copyCode(code) {
        try {
            await navigator.clipboard.writeText(code);
            this.showToast('Referral code copied! 📋');
        } catch (error) {
            this.fallbackCopy(code);
        }
    }

    async copyUrl(url) {
        try {
            await navigator.clipboard.writeText(url);
            this.showToast('Referral link copied! 🔗');
        } catch (error) {
            this.fallbackCopy(url);
        }
    }

    fallbackCopy(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            this.showToast('Copied to clipboard!');
        } catch (error) {
            this.showToast('Failed to copy. Please copy manually.');
        }
        document.body.removeChild(textarea);
    }

    shareViaEmail(code) {
        const baseUrl = window.location.origin;
        const subject = encodeURIComponent('Try Receipt Extractor - AI-Powered Receipt Extraction');
        const body = encodeURIComponent(
            `Hi!\n\nI've been using Receipt Extractor and thought you might find it useful. It's an AI-powered tool for extracting text from receipts.\n\n` +
            `Use my referral code "${code}" when you sign up to get started!\n\n` +
            `${baseUrl}/register.html?ref=${code}\n\n` +
            `Best regards`
        );
        window.location.href = `mailto:?subject=${subject}&body=${body}`;
    }

    shareViaTwitter(text, url) {
        window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank', 'width=600,height=400');
    }

    shareViaLinkedIn(url) {
        window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`, '_blank', 'width=600,height=400');
    }

    shareViaFacebook(url) {
        window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank', 'width=600,height=400');
    }

    showToast(message) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        document.body.appendChild(toast);

        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);

        // Remove toast after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }

    setupEventListeners() {
        // Refresh data periodically
        setInterval(() => this.loadReferralData().then(() => this.render()), 60000); // Every minute
    }

    attachEventListeners() {
        // Additional event listeners
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.referralDashboard = new ReferralDashboard();
    });
} else {
    window.referralDashboard = new ReferralDashboard();
}
