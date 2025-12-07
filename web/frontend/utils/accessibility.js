/**
 * Keyboard Shortcuts Manager
 * Manages global keyboard shortcuts and accessibility features
 */

class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.enabled = true;
        this.modal = null;
        
        this.init();
    }

    /**
     * Initialize keyboard shortcuts
     */
    init() {
        document.addEventListener('keydown', (e) => {
            this.handleKeyPress(e);
        });

        // Register default shortcuts
        this.registerDefaultShortcuts();
    }

    /**
     * Register default shortcuts
     */
    registerDefaultShortcuts() {
        // Help
        this.register('?', () => this.showHelp(), 'Show keyboard shortcuts');
        
        // Navigation
        this.register('g h', () => window.location.href = 'index.html', 'Go to home');
        this.register('g d', () => window.location.href = 'dashboard.html', 'Go to dashboard');
        this.register('g p', () => window.location.href = 'pricing.html', 'Go to pricing');
        
        // Actions
        this.register('n', () => this.triggerNewReceipt(), 'New receipt upload');
        this.register('s', () => this.triggerSearch(), 'Search receipts');
        this.register('/', () => this.triggerSearch(), 'Focus search');
        
        // Common
        this.register('Escape', () => this.closeModals(), 'Close modal/dialog');
        
        // Accessibility
        this.register('Alt+1', () => this.skipToMain(), 'Skip to main content');
    }

    /**
     * Register keyboard shortcut
     */
    register(keys, callback, description = '') {
        const normalizedKeys = this.normalizeKeys(keys);
        
        this.shortcuts.set(normalizedKeys, {
            keys,
            callback,
            description
        });
    }

    /**
     * Unregister keyboard shortcut
     */
    unregister(keys) {
        const normalizedKeys = this.normalizeKeys(keys);
        this.shortcuts.delete(normalizedKeys);
    }

    /**
     * Normalize keys for matching
     */
    normalizeKeys(keys) {
        return keys.toLowerCase().trim();
    }

    /**
     * Handle key press
     */
    handleKeyPress(e) {
        if (!this.enabled) return;
        
        // Ignore if typing in input field
        if (this.isTyping(e.target)) {
            // Except for Escape
            if (e.key !== 'Escape') return;
        }

        const key = this.getKeyString(e);
        const normalized = this.normalizeKeys(key);

        const shortcut = this.shortcuts.get(normalized);
        if (shortcut) {
            e.preventDefault();
            shortcut.callback(e);
        }
    }

    /**
     * Get key string from event
     */
    getKeyString(e) {
        const parts = [];
        
        if (e.ctrlKey) parts.push('Ctrl');
        if (e.altKey) parts.push('Alt');
        if (e.shiftKey && e.key.length > 1) parts.push('Shift');
        if (e.metaKey) parts.push('Meta');
        
        parts.push(e.key);
        
        return parts.join('+');
    }

    /**
     * Check if user is typing in input
     */
    isTyping(element) {
        const tagName = element.tagName.toLowerCase();
        const isInput = tagName === 'input' || tagName === 'textarea';
        const isContentEditable = element.contentEditable === 'true';
        
        return isInput || isContentEditable;
    }

    /**
     * Trigger new receipt upload
     */
    triggerNewReceipt() {
        const uploadZone = document.getElementById('mainUploadZone');
        if (uploadZone && uploadZone.triggerFileSelect) {
            uploadZone.triggerFileSelect();
        } else {
            // Fallback - click file input
            const fileInput = document.querySelector('input[type="file"]');
            if (fileInput) fileInput.click();
        }
    }

    /**
     * Trigger search
     */
    triggerSearch() {
        const searchInput = document.querySelector('[type="search"], [placeholder*="Search"]');
        if (searchInput) {
            searchInput.focus();
        }
    }

    /**
     * Close modals
     */
    closeModals() {
        if (typeof modal !== 'undefined') {
            modal.closeAll();
        }
    }

    /**
     * Skip to main content
     */
    skipToMain() {
        const main = document.querySelector('main, [role="main"], #main');
        if (main) {
            main.setAttribute('tabindex', '-1');
            main.focus();
            main.scrollIntoView({ behavior: 'smooth' });
        }
    }

    /**
     * Show help modal with shortcuts
     */
    showHelp() {
        const shortcuts = Array.from(this.shortcuts.values());
        
        const shortcutList = shortcuts
            .filter(s => s.description)
            .map(s => `
                <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #E5E7EB;">
                    <span style="color: #374151;">${s.description}</span>
                    <kbd style="background: #F3F4F6; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-family: monospace;">${s.keys}</kbd>
                </div>
            `)
            .join('');

        if (typeof modal !== 'undefined') {
            modal.show({
                title: 'Keyboard Shortcuts',
                content: `
                    <div style="max-height: 400px; overflow-y: auto;">
                        ${shortcutList}
                    </div>
                `,
                footer: `
                    <button class="modal-btn modal-btn-primary" data-action="close">Close</button>
                `,
                size: 'md'
            });

            setTimeout(() => {
                const closeBtn = document.querySelector('[data-action="close"]');
                if (closeBtn) {
                    closeBtn.addEventListener('click', () => {
                        modal.closeAll();
                    });
                }
            }, 0);
        } else {
            console.log('Keyboard Shortcuts:', shortcuts);
        }
    }

    /**
     * Enable shortcuts
     */
    enable() {
        this.enabled = true;
    }

    /**
     * Disable shortcuts
     */
    disable() {
        this.enabled = false;
    }

    /**
     * Toggle shortcuts
     */
    toggle() {
        this.enabled = !this.enabled;
    }
}

/**
 * Accessibility Helper
 * Provides accessibility utilities and enhancements
 */
class AccessibilityHelper {
    /**
     * Add skip to content link
     */
    static addSkipLink() {
        if (document.getElementById('skip-to-content')) return;

        const skipLink = document.createElement('a');
        skipLink.id = 'skip-to-content';
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'skip-link';
        
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 0;
            background: #3B82F6;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            z-index: 100000;
            transition: top 0.2s;
        `;

        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '0';
        });

        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });

        document.body.insertBefore(skipLink, document.body.firstChild);
    }

    /**
     * Enhance focus visibility
     */
    static enhanceFocusVisibility() {
        const style = document.createElement('style');
        style.textContent = `
            *:focus {
                outline: 2px solid #3B82F6;
                outline-offset: 2px;
            }
            
            *:focus:not(:focus-visible) {
                outline: none;
            }
            
            *:focus-visible {
                outline: 2px solid #3B82F6;
                outline-offset: 2px;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Add ARIA labels to elements
     */
    static addAriaLabels() {
        // Add labels to buttons without text
        document.querySelectorAll('button:not([aria-label]):not(:has(text))').forEach(btn => {
            const icon = btn.querySelector('svg, img');
            if (icon) {
                btn.setAttribute('aria-label', 'Button');
            }
        });

        // Add labels to links without text
        document.querySelectorAll('a:not([aria-label]):not(:has(text))').forEach(link => {
            link.setAttribute('aria-label', 'Link');
        });
    }

    /**
     * Improve heading structure
     */
    static validateHeadingStructure() {
        const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
        let previousLevel = 0;
        
        headings.forEach(heading => {
            const level = parseInt(heading.tagName[1]);
            
            if (level > previousLevel + 1) {
                console.warn(`Heading structure issue: ${heading.tagName} follows h${previousLevel}`, heading);
            }
            
            previousLevel = level;
        });
    }

    /**
     * Add live regions
     */
    static addLiveRegions() {
        // Add polite live region for notifications
        if (!document.getElementById('polite-live-region')) {
            const politeRegion = document.createElement('div');
            politeRegion.id = 'polite-live-region';
            politeRegion.setAttribute('role', 'status');
            politeRegion.setAttribute('aria-live', 'polite');
            politeRegion.setAttribute('aria-atomic', 'true');
            politeRegion.style.cssText = 'position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;';
            document.body.appendChild(politeRegion);
        }

        // Add assertive live region for alerts
        if (!document.getElementById('assertive-live-region')) {
            const assertiveRegion = document.createElement('div');
            assertiveRegion.id = 'assertive-live-region';
            assertiveRegion.setAttribute('role', 'alert');
            assertiveRegion.setAttribute('aria-live', 'assertive');
            assertiveRegion.setAttribute('aria-atomic', 'true');
            assertiveRegion.style.cssText = 'position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;';
            document.body.appendChild(assertiveRegion);
        }
    }

    /**
     * Announce to screen readers
     */
    static announce(message, assertive = false) {
        const regionId = assertive ? 'assertive-live-region' : 'polite-live-region';
        const region = document.getElementById(regionId);
        
        if (region) {
            region.textContent = '';
            setTimeout(() => {
                region.textContent = message;
            }, 100);
        }
    }

    /**
     * Check color contrast
     */
    static checkColorContrast(foreground, background) {
        const rgb1 = this.hexToRgb(foreground);
        const rgb2 = this.hexToRgb(background);
        
        const l1 = this.relativeLuminance(rgb1);
        const l2 = this.relativeLuminance(rgb2);
        
        const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
        
        return {
            ratio,
            passAA: ratio >= 4.5,
            passAAA: ratio >= 7,
            passAALarge: ratio >= 3,
            passAAALarge: ratio >= 4.5
        };
    }

    /**
     * Convert hex color to RGB
     */
    static hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    /**
     * Calculate relative luminance
     */
    static relativeLuminance(rgb) {
        const rsRGB = rgb.r / 255;
        const gsRGB = rgb.g / 255;
        const bsRGB = rgb.b / 255;

        const r = rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4);
        const g = gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4);
        const b = bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4);

        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    }

    /**
     * Initialize all accessibility enhancements
     */
    static initAll() {
        this.addSkipLink();
        this.enhanceFocusVisibility();
        this.addLiveRegions();
        this.addAriaLabels();
        this.validateHeadingStructure();
    }
}

// Create singleton instance
const keyboardShortcuts = new KeyboardShortcuts();

// Initialize accessibility on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        AccessibilityHelper.initAll();
    });
} else {
    AccessibilityHelper.initAll();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { KeyboardShortcuts, AccessibilityHelper, keyboardShortcuts };
}
