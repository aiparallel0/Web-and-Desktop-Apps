/**
 * Analytics Tracker
 * Track user interactions, page views, and custom events
 */

class Analytics {
    constructor(options = {}) {
        this.options = {
            enabled: true,
            debug: false,
            trackPageViews: true,
            trackClicks: true,
            trackForms: true,
            trackErrors: true,
            sessionId: this.generateSessionId(),
            ...options
        };

        this.events = [];
        this.sessionStart = Date.now();
        this.pageViewStart = Date.now();
        
        if (this.options.enabled) {
            this.init();
        }
    }

    /**
     * Initialize analytics
     */
    init() {
        // Track initial page view
        if (this.options.trackPageViews) {
            this.trackPageView();
        }

        // Auto-track clicks
        if (this.options.trackClicks) {
            this.setupClickTracking();
        }

        // Auto-track form submissions
        if (this.options.trackForms) {
            this.setupFormTracking();
        }

        // Auto-track errors
        if (this.options.trackErrors) {
            this.setupErrorTracking();
        }

        // Track session end
        window.addEventListener('beforeunload', () => {
            this.trackEvent('session_end', {
                duration: Date.now() - this.sessionStart,
                events_count: this.events.length
            });
            this.flush();
        });

        // Track page visibility
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.trackEvent('page_hidden', {
                    time_on_page: Date.now() - this.pageViewStart
                });
            } else {
                this.trackEvent('page_visible');
                this.pageViewStart = Date.now();
            }
        });

        this.log('Analytics initialized');
    }

    /**
     * Generate unique session ID
     */
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Track page view
     */
    trackPageView(page = window.location.pathname, title = document.title) {
        this.trackEvent('page_view', {
            page,
            title,
            referrer: document.referrer,
            timestamp: new Date().toISOString()
        });

        this.pageViewStart = Date.now();
    }

    /**
     * Track custom event
     */
    trackEvent(eventName, properties = {}) {
        if (!this.options.enabled) return;

        const event = {
            event: eventName,
            timestamp: new Date().toISOString(),
            session_id: this.options.sessionId,
            page: window.location.pathname,
            ...properties,
            user_agent: navigator.userAgent,
            screen_resolution: `${window.screen.width}x${window.screen.height}`,
            viewport_size: `${window.innerWidth}x${window.innerHeight}`
        };

        this.events.push(event);
        this.log('Event tracked:', event);

        // Send to backend if available
        this.sendEvent(event);
    }

    /**
     * Track click event
     */
    trackClick(element, properties = {}) {
        const elementInfo = {
            tag: element.tagName.toLowerCase(),
            id: element.id || undefined,
            class: element.className || undefined,
            text: element.textContent?.trim().substring(0, 100) || undefined,
            href: element.href || undefined
        };

        this.trackEvent('click', {
            ...elementInfo,
            ...properties
        });
    }

    /**
     * Track form submission
     */
    trackFormSubmit(form, properties = {}) {
        const formInfo = {
            form_id: form.id || undefined,
            form_name: form.name || undefined,
            action: form.action || undefined,
            method: form.method || undefined,
            fields_count: form.elements.length
        };

        this.trackEvent('form_submit', {
            ...formInfo,
            ...properties
        });
    }

    /**
     * Track error
     */
    trackError(error, properties = {}) {
        const errorInfo = {
            message: error.message || error,
            stack: error.stack?.substring(0, 500),
            type: error.name || 'Error'
        };

        this.trackEvent('error', {
            ...errorInfo,
            ...properties
        });
    }

    /**
     * Track performance metric
     */
    trackPerformance(metric, value, properties = {}) {
        this.trackEvent('performance', {
            metric,
            value,
            ...properties
        });
    }

    /**
     * Track user timing
     */
    trackTiming(category, variable, time, label = '') {
        this.trackEvent('timing', {
            category,
            variable,
            time,
            label
        });
    }

    /**
     * Track conversion
     */
    trackConversion(type, value = 0, properties = {}) {
        this.trackEvent('conversion', {
            type,
            value,
            ...properties
        });
    }

    /**
     * Setup automatic click tracking
     */
    setupClickTracking() {
        document.addEventListener('click', (e) => {
            const element = e.target;
            
            // Track buttons and links
            if (element.tagName === 'BUTTON' || element.tagName === 'A') {
                this.trackClick(element);
            }

            // Track elements with data-track attribute
            const tracked = element.closest('[data-track]');
            if (tracked) {
                const trackData = tracked.dataset.track;
                try {
                    const properties = JSON.parse(trackData);
                    this.trackClick(tracked, properties);
                } catch (e) {
                    this.trackClick(tracked, { track_id: trackData });
                }
            }
        });
    }

    /**
     * Setup automatic form tracking
     */
    setupFormTracking() {
        document.addEventListener('submit', (e) => {
            if (e.target.tagName === 'FORM') {
                this.trackFormSubmit(e.target);
            }
        });
    }

    /**
     * Setup automatic error tracking
     */
    setupErrorTracking() {
        window.addEventListener('error', (e) => {
            this.trackError(e.error || e.message, {
                filename: e.filename,
                line: e.lineno,
                column: e.colno
            });
        });

        window.addEventListener('unhandledrejection', (e) => {
            this.trackError(e.reason, {
                type: 'unhandled_promise_rejection'
            });
        });
    }

    /**
     * Send event to backend
     */
    async sendEvent(event) {
        try {
            // Use navigator.sendBeacon for reliability
            if (navigator.sendBeacon) {
                const blob = new Blob([JSON.stringify(event)], {
                    type: 'application/json'
                });
                navigator.sendBeacon('/api/analytics/track', blob);
            } else {
                // Fallback to fetch
                fetch('/api/analytics/track', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(event),
                    keepalive: true
                }).catch(() => {
                    // Silently fail
                });
            }
        } catch (error) {
            this.log('Error sending event:', error);
        }
    }

    /**
     * Flush all pending events
     */
    flush() {
        if (this.events.length === 0) return;

        try {
            const blob = new Blob([JSON.stringify(this.events)], {
                type: 'application/json'
            });
            navigator.sendBeacon('/api/analytics/batch', blob);
            this.events = [];
        } catch (error) {
            this.log('Error flushing events:', error);
        }
    }

    /**
     * Get session statistics
     */
    getSessionStats() {
        return {
            session_id: this.options.sessionId,
            duration: Date.now() - this.sessionStart,
            events_count: this.events.length,
            page_views: this.events.filter(e => e.event === 'page_view').length,
            clicks: this.events.filter(e => e.event === 'click').length,
            errors: this.events.filter(e => e.event === 'error').length
        };
    }

    /**
     * Export events
     */
    exportEvents() {
        return [...this.events];
    }

    /**
     * Clear events
     */
    clearEvents() {
        this.events = [];
    }

    /**
     * Enable/disable tracking
     */
    setEnabled(enabled) {
        this.options.enabled = enabled;
        this.log(`Analytics ${enabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Debug logging
     */
    log(...args) {
        if (this.options.debug) {
            console.log('[Analytics]', ...args);
        }
    }
}

// Create singleton instance
const analytics = new Analytics({
    debug: false,
    enabled: true
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = analytics;
}
