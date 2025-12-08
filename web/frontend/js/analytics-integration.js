/**
 * Analytics Integration Helper
 * Integrates Google Analytics and Facebook Pixel with cookie consent
 */

class AnalyticsIntegration {
    constructor(config = {}) {
        this.config = {
            gaTrackingId: config.gaTrackingId || 'G-XXXXXXXXXX', // Replace with actual GA4 ID
            fbPixelId: config.fbPixelId || '000000000000000', // Replace with actual Pixel ID
            debug: config.debug || false,
            ...config
        };

        this.initialized = false;
        this.consentGiven = false;

        // Listen for cookie consent updates
        window.addEventListener('cookieConsentUpdated', (e) => {
            this.handleConsentUpdate(e.detail);
        });

        // Check if consent already given
        this.checkConsent();
    }

    /**
     * Check if user has already consented
     */
    checkConsent() {
        const analyticsCookie = this.getCookie('analytics_enabled');
        const marketingCookie = this.getCookie('marketing_enabled');

        if (analyticsCookie === 'true' || marketingCookie === 'true') {
            this.handleConsentUpdate({
                analytics: analyticsCookie === 'true',
                marketing: marketingCookie === 'true'
            });
        }
    }

    /**
     * Handle consent update
     */
    handleConsentUpdate(consent) {
        this.consentGiven = true;

        if (consent.analytics) {
            this.initGoogleAnalytics();
        }

        if (consent.marketing) {
            this.initFacebookPixel();
        }

        this.log('Analytics initialized with consent:', consent);
    }

    /**
     * Initialize Google Analytics 4
     */
    initGoogleAnalytics() {
        if (typeof gtag !== 'undefined') {
            this.log('Google Analytics already loaded');
            return;
        }

        // Load Google Analytics script
        const script = document.createElement('script');
        script.async = true;
        script.src = `https://www.googletagmanager.com/gtag/js?id=${this.config.gaTrackingId}`;
        document.head.appendChild(script);

        // Initialize gtag
        window.dataLayer = window.dataLayer || [];
        window.gtag = function() {
            window.dataLayer.push(arguments);
        };

        gtag('js', new Date());
        gtag('config', this.config.gaTrackingId, {
            'anonymize_ip': true,
            'cookie_flags': 'SameSite=None;Secure'
        });

        this.log('Google Analytics initialized:', this.config.gaTrackingId);
    }

    /**
     * Initialize Facebook Pixel
     */
    initFacebookPixel() {
        if (typeof fbq !== 'undefined') {
            this.log('Facebook Pixel already loaded');
            return;
        }

        // Load Facebook Pixel
        !function(f,b,e,v,n,t,s) {
            if(f.fbq)return;n=f.fbq=function(){n.callMethod?
            n.callMethod.apply(n,arguments):n.queue.push(arguments)};
            if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
            n.queue=[];t=b.createElement(e);t.async=!0;
            t.src=v;s=b.getElementsByTagName(e)[0];
            s.parentNode.insertBefore(t,s)
        }(window, document,'script',
        'https://connect.facebook.net/en_US/fbevents.js');

        fbq('init', this.config.fbPixelId);
        fbq('track', 'PageView');

        this.log('Facebook Pixel initialized:', this.config.fbPixelId);
    }

    /**
     * Track custom event
     */
    trackEvent(eventName, params = {}) {
        if (!this.consentGiven) {
            this.log('Event not tracked - no consent:', eventName);
            return;
        }

        // Google Analytics event
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, params);
            this.log('GA Event:', eventName, params);
        }

        // Facebook Pixel event
        if (typeof fbq !== 'undefined') {
            fbq('track', eventName, params);
            this.log('FB Event:', eventName, params);
        }
    }

    /**
     * Track page view
     */
    trackPageView(page) {
        if (!this.consentGiven) return;

        if (typeof gtag !== 'undefined') {
            gtag('config', this.config.gaTrackingId, {
                'page_path': page || window.location.pathname
            });
        }

        if (typeof fbq !== 'undefined') {
            fbq('track', 'PageView');
        }

        this.log('Page view tracked:', page);
    }

    /**
     * Track conversion funnel events
     */
    trackConversionEvent(eventType, data = {}) {
        const eventMap = {
            'signup_started': {
                ga: 'sign_up_started',
                fb: 'Lead',
                params: { source: data.source || 'web' }
            },
            'signup_completed': {
                ga: 'sign_up',
                fb: 'CompleteRegistration',
                params: { method: data.method || 'email' }
            },
            'trial_activated': {
                ga: 'trial_start',
                fb: 'StartTrial',
                params: { plan: data.plan || 'pro' }
            },
            'first_receipt_uploaded': {
                ga: 'first_upload',
                fb: 'Lead',
                params: { model: data.model || 'tesseract' }
            },
            'upgrade_clicked': {
                ga: 'begin_checkout',
                fb: 'InitiateCheckout',
                params: { plan: data.plan, value: data.value, currency: 'USD' }
            },
            'payment_completed': {
                ga: 'purchase',
                fb: 'Purchase',
                params: {
                    transaction_id: data.transaction_id,
                    value: data.value,
                    currency: 'USD',
                    items: [{ item_name: data.plan }]
                }
            }
        };

        const event = eventMap[eventType];
        if (!event) {
            this.log('Unknown conversion event:', eventType);
            return;
        }

        // Track in Google Analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', event.ga, { ...event.params, ...data });
        }

        // Track in Facebook Pixel
        if (typeof fbq !== 'undefined') {
            fbq('track', event.fb, { ...event.params, ...data });
        }

        this.log('Conversion event tracked:', eventType, event);
    }

    /**
     * Get cookie value
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
     * Debug logging
     */
    log(...args) {
        if (this.config.debug) {
            console.log('[Analytics]', ...args);
        }
    }
}

// Create singleton instance
window.analyticsIntegration = new AnalyticsIntegration({
    debug: false // Set to true for development
});

// Export for convenience
window.trackEvent = (event, params) => window.analyticsIntegration.trackEvent(event, params);
window.trackConversion = (event, data) => window.analyticsIntegration.trackConversionEvent(event, data);
