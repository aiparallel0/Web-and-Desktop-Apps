/**
 * Analytics Tracking - Client-Side
 * 
 * Integrates with:
 * - Google Analytics 4
 * - Mixpanel
 * - Internal tracking API
 */

(function() {
    'use strict';

    // Configuration
    const ANALYTICS_CONFIG = {
        apiEndpoint: '/api/marketing/track-event',
        enabled: true,
        debug: false
    };

    // Session management
    let sessionId = null;
    let userId = null;

    /**
     * Initialize analytics
     */
    function init() {
        // Generate or retrieve session ID
        sessionId = getOrCreateSessionId();
        
        // Get user ID if logged in
        userId = getUserId();
        
        if (ANALYTICS_CONFIG.debug) {
            console.log('Analytics initialized', { sessionId, userId });
        }

        // Track page view
        trackPageView();

        // Set up automatic tracking
        setupEventTrackers();
    }

    /**
     * Get or create session ID
     */
    function getOrCreateSessionId() {
        let sid = sessionStorage.getItem('analytics_session_id');
        if (!sid) {
            sid = generateId();
            sessionStorage.setItem('analytics_session_id', sid);
        }
        return sid;
    }

    /**
     * Get user ID from localStorage or cookie
     */
    function getUserId() {
        // Try localStorage first
        const uid = localStorage.getItem('user_id');
        if (uid) return uid;
        
        // Try to parse from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'user_id') {
                return value;
            }
        }
        
        return null;
    }

    /**
     * Generate unique ID
     */
    function generateId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Track event to backend and external services
     */
    function trackEvent(eventName, properties = {}) {
        if (!ANALYTICS_CONFIG.enabled) return;

        const event = {
            event: eventName,
            properties: {
                ...properties,
                page_url: window.location.href,
                page_title: document.title,
                referrer: document.referrer,
                timestamp: new Date().toISOString()
            },
            user_id: userId,
            session_id: sessionId
        };

        // Add UTM parameters if present
        const utmParams = getUTMParameters();
        if (Object.keys(utmParams).length > 0) {
            event.properties.utm = utmParams;
        }

        if (ANALYTICS_CONFIG.debug) {
            console.log('Track event:', event);
        }

        // Send to backend
        sendToBackend(event);

        // Send to Google Analytics 4
        sendToGA4(eventName, properties);

        // Send to Mixpanel
        sendToMixpanel(eventName, properties);
    }

    /**
     * Send event to backend API
     */
    function sendToBackend(event) {
        fetch(ANALYTICS_CONFIG.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-Id': sessionId
            },
            body: JSON.stringify(event)
        }).catch(err => {
            if (ANALYTICS_CONFIG.debug) {
                console.error('Failed to send event to backend:', err);
            }
        });
    }

    /**
     * Send event to Google Analytics 4
     */
    function sendToGA4(eventName, properties) {
        if (typeof gtag === 'function') {
            gtag('event', eventName, properties);
        }
    }

    /**
     * Send event to Mixpanel
     */
    function sendToMixpanel(eventName, properties) {
        if (typeof mixpanel !== 'undefined') {
            mixpanel.track(eventName, properties);
        }
    }

    /**
     * Track page view
     */
    function trackPageView() {
        const pagePath = window.location.pathname;
        const pageTitle = document.title;
        
        trackEvent('page_view', {
            page_path: pagePath,
            page_title: pageTitle
        });
    }

    /**
     * Track button click
     */
    function trackClick(element, eventName = null) {
        const name = eventName || 
                    element.getAttribute('data-track-event') ||
                    'button_click';
        
        const properties = {
            button_text: element.textContent.trim(),
            button_id: element.id,
            button_class: element.className
        };

        trackEvent(name, properties);
    }

    /**
     * Track form submission
     */
    function trackFormSubmit(form, eventName = null) {
        const name = eventName || 
                    form.getAttribute('data-track-event') ||
                    'form_submit';
        
        const properties = {
            form_id: form.id,
            form_name: form.name,
            form_action: form.action
        };

        trackEvent(name, properties);
    }

    /**
     * Track scroll depth
     */
    let maxScrollDepth = 0;
    let scrollTimeout = null;

    function trackScrollDepth() {
        const scrollHeight = document.documentElement.scrollHeight;
        const scrollTop = window.scrollY || window.pageYOffset;
        const clientHeight = window.innerHeight;
        
        const scrollDepth = Math.round((scrollTop + clientHeight) / scrollHeight * 100);
        
        if (scrollDepth > maxScrollDepth) {
            maxScrollDepth = scrollDepth;
            
            // Track milestones: 25%, 50%, 75%, 100%
            const milestones = [25, 50, 75, 100];
            for (let milestone of milestones) {
                if (maxScrollDepth >= milestone && 
                    maxScrollDepth < milestone + 5) {
                    trackEvent('scroll_depth', {
                        depth_percentage: milestone
                    });
                    break;
                }
            }
        }
    }

    function onScroll() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(trackScrollDepth, 500);
    }

    /**
     * Track time on page
     */
    let pageStartTime = Date.now();

    function trackTimeOnPage() {
        const timeSpent = Math.round((Date.now() - pageStartTime) / 1000);
        
        trackEvent('time_on_page', {
            seconds: timeSpent,
            page_path: window.location.pathname
        });
    }

    /**
     * Track exit intent
     */
    function trackExitIntent(event) {
        // Only trigger when moving up (towards browser chrome)
        if (event.clientY < 10 && !sessionStorage.getItem('exit_intent_tracked')) {
            trackEvent('exit_intent', {
                page_path: window.location.pathname
            });
            
            sessionStorage.setItem('exit_intent_tracked', 'true');
        }
    }

    /**
     * Get UTM parameters from URL
     */
    function getUTMParameters() {
        const params = new URLSearchParams(window.location.search);
        const utm = {};
        
        const utmKeys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'];
        for (let key of utmKeys) {
            if (params.has(key)) {
                utm[key] = params.get(key);
            }
        }
        
        // Store UTM params for session
        if (Object.keys(utm).length > 0) {
            sessionStorage.setItem('utm_params', JSON.stringify(utm));
        }
        
        // Return stored UTM params if not in current URL
        const stored = sessionStorage.getItem('utm_params');
        return stored ? JSON.parse(stored) : utm;
    }

    /**
     * Set up automatic event trackers
     */
    function setupEventTrackers() {
        // Track clicks on elements with data-track attribute
        document.addEventListener('click', function(event) {
            const target = event.target.closest('[data-track]');
            if (target) {
                trackClick(target);
            }
        });

        // Track form submissions
        document.addEventListener('submit', function(event) {
            const form = event.target;
            if (form.hasAttribute('data-track-submit')) {
                trackFormSubmit(form);
            }
        });

        // Track scroll depth
        window.addEventListener('scroll', onScroll);

        // Track time on page before unload
        window.addEventListener('beforeunload', trackTimeOnPage);

        // Track exit intent
        document.addEventListener('mousemove', trackExitIntent);
    }

    /**
     * Public API
     */
    window.Analytics = {
        track: trackEvent,
        trackClick: trackClick,
        trackFormSubmit: trackFormSubmit,
        identify: function(uid) {
            userId = uid;
            localStorage.setItem('user_id', uid);
            
            // Send identify to services
            if (typeof mixpanel !== 'undefined') {
                mixpanel.identify(uid);
            }
        },
        reset: function() {
            userId = null;
            sessionId = generateId();
            localStorage.removeItem('user_id');
            sessionStorage.removeItem('analytics_session_id');
            sessionStorage.removeItem('utm_params');
            sessionStorage.removeItem('exit_intent_tracked');
        }
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
