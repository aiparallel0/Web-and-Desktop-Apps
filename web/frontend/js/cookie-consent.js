/**
 * Cookie Consent Banner
 * GDPR/CCPA compliant cookie consent management
 */

class CookieConsent {
    constructor(options = {}) {
        this.options = {
            cookieName: 'receipt_extractor_cookie_consent',
            cookieExpiry: 365, // days
            privacyUrl: 'privacy.html',
            position: 'bottom', // 'top' or 'bottom'
            ...options
        };

        this.init();
    }

    /**
     * Initialize cookie consent
     */
    init() {
        // Check if user has already consented
        if (this.hasConsented()) {
            this.enableAnalytics();
            return;
        }

        // Show consent banner
        this.showBanner();
    }

    /**
     * Check if user has already consented
     */
    hasConsented() {
        return this.getCookie(this.options.cookieName) === 'accepted';
    }

    /**
     * Show consent banner
     */
    showBanner() {
        const banner = document.createElement('div');
        banner.id = 'cookie-consent-banner';
        banner.className = `cookie-consent-banner cookie-consent-${this.options.position}`;
        banner.innerHTML = `
            <div class="cookie-consent-content">
                <div class="cookie-consent-text">
                    <p>
                        <strong>🍪 We use cookies</strong><br>
                        We use essential cookies to make our site work. With your consent, we may also use non-essential cookies to improve user experience and analyze website traffic. 
                        <a href="${this.options.privacyUrl}" target="_blank">Learn more</a>
                    </p>
                </div>
                <div class="cookie-consent-actions">
                    <button class="btn btn-ghost btn-sm" id="cookie-reject">
                        Reject All
                    </button>
                    <button class="btn btn-outline btn-sm" id="cookie-customize">
                        Customize
                    </button>
                    <button class="btn btn-primary btn-sm" id="cookie-accept">
                        Accept All
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(banner);

        // Add event listeners
        document.getElementById('cookie-accept').addEventListener('click', () => this.acceptCookies());
        document.getElementById('cookie-reject').addEventListener('click', () => this.rejectCookies());
        document.getElementById('cookie-customize').addEventListener('click', () => this.showCustomize());

        // Animate banner in
        setTimeout(() => banner.classList.add('show'), 100);
    }

    /**
     * Show customization modal
     */
    showCustomize() {
        const modal = document.createElement('div');
        modal.id = 'cookie-customize-modal';
        modal.className = 'cookie-modal';
        modal.innerHTML = `
            <div class="cookie-modal-overlay"></div>
            <div class="cookie-modal-content">
                <div class="cookie-modal-header">
                    <h3>Customize Cookie Preferences</h3>
                    <button class="cookie-modal-close" aria-label="Close">&times;</button>
                </div>
                <div class="cookie-modal-body">
                    <div class="cookie-category">
                        <div class="cookie-category-header">
                            <div>
                                <h4>Essential Cookies</h4>
                                <p>Required for the website to function properly. Cannot be disabled.</p>
                            </div>
                            <label class="cookie-toggle disabled">
                                <input type="checkbox" checked disabled>
                                <span class="cookie-toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="cookie-category">
                        <div class="cookie-category-header">
                            <div>
                                <h4>Analytics Cookies</h4>
                                <p>Help us understand how visitors interact with our website by collecting and reporting information anonymously.</p>
                            </div>
                            <label class="cookie-toggle">
                                <input type="checkbox" id="analytics-cookies" checked>
                                <span class="cookie-toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="cookie-category">
                        <div class="cookie-category-header">
                            <div>
                                <h4>Marketing Cookies</h4>
                                <p>Used to track visitors across websites to display relevant ads and measure campaign effectiveness.</p>
                            </div>
                            <label class="cookie-toggle">
                                <input type="checkbox" id="marketing-cookies" checked>
                                <span class="cookie-toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
                <div class="cookie-modal-footer">
                    <button class="btn btn-outline" id="cookie-save-preferences">
                        Save Preferences
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Event listeners
        modal.querySelector('.cookie-modal-close').addEventListener('click', () => this.closeModal(modal));
        modal.querySelector('.cookie-modal-overlay').addEventListener('click', () => this.closeModal(modal));
        document.getElementById('cookie-save-preferences').addEventListener('click', () => {
            const analytics = document.getElementById('analytics-cookies').checked;
            const marketing = document.getElementById('marketing-cookies').checked;
            this.savePreferences({ analytics, marketing });
            this.closeModal(modal);
        });

        // Animate modal in
        setTimeout(() => modal.classList.add('show'), 100);
    }

    /**
     * Close modal
     */
    closeModal(modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 300);
    }

    /**
     * Accept all cookies
     */
    acceptCookies() {
        this.setCookie(this.options.cookieName, 'accepted', this.options.cookieExpiry);
        this.setCookie('analytics_enabled', 'true', this.options.cookieExpiry);
        this.setCookie('marketing_enabled', 'true', this.options.cookieExpiry);
        this.enableAnalytics();
        this.hideBanner();
    }

    /**
     * Reject all cookies
     */
    rejectCookies() {
        this.setCookie(this.options.cookieName, 'rejected', this.options.cookieExpiry);
        this.setCookie('analytics_enabled', 'false', this.options.cookieExpiry);
        this.setCookie('marketing_enabled', 'false', this.options.cookieExpiry);
        this.hideBanner();
    }

    /**
     * Save custom preferences
     */
    savePreferences(preferences) {
        this.setCookie(this.options.cookieName, 'accepted', this.options.cookieExpiry);
        this.setCookie('analytics_enabled', preferences.analytics ? 'true' : 'false', this.options.cookieExpiry);
        this.setCookie('marketing_enabled', preferences.marketing ? 'true' : 'false', this.options.cookieExpiry);
        
        if (preferences.analytics || preferences.marketing) {
            this.enableAnalytics();
        }
        
        this.hideBanner();
    }

    /**
     * Hide consent banner
     */
    hideBanner() {
        const banner = document.getElementById('cookie-consent-banner');
        if (banner) {
            banner.classList.remove('show');
            setTimeout(() => banner.remove(), 300);
        }
    }

    /**
     * Enable analytics based on consent
     */
    enableAnalytics() {
        const analyticsEnabled = this.getCookie('analytics_enabled') === 'true';
        const marketingEnabled = this.getCookie('marketing_enabled') === 'true';

        // Initialize Google Analytics if enabled
        if (analyticsEnabled && typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'analytics_storage': 'granted'
            });
        }

        // Initialize Facebook Pixel if enabled
        if (marketingEnabled && typeof fbq !== 'undefined') {
            fbq('consent', 'grant');
        }

        // Trigger event for other scripts
        window.dispatchEvent(new CustomEvent('cookieConsentUpdated', {
            detail: { analytics: analyticsEnabled, marketing: marketingEnabled }
        }));
    }

    /**
     * Set cookie
     */
    setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
    }

    /**
     * Get cookie
     */
    getCookie(name) {
        const nameEQ = name + '=';
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.indexOf(nameEQ) === 0) {
                return cookie.substring(nameEQ.length);
            }
        }
        return null;
    }

    /**
     * Delete cookie
     */
    deleteCookie(name) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
    }

    /**
     * Reset consent (for testing)
     */
    reset() {
        this.deleteCookie(this.options.cookieName);
        this.deleteCookie('analytics_enabled');
        this.deleteCookie('marketing_enabled');
        location.reload();
    }
}

// Initialize cookie consent when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.cookieConsent = new CookieConsent();
    });
} else {
    window.cookieConsent = new CookieConsent();
}
