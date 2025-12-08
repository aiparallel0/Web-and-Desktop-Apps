/**
 * In-app Tooltips for First-Time Users
 * Provides guided onboarding experience
 */

class OnboardingTooltips {
    constructor(options = {}) {
        this.options = {
            storageKey: 'receipt_extractor_onboarding',
            tooltips: [],
            currentStep: 0,
            autoStart: true,
            ...options
        };

        this.completed = this.isCompleted();
        
        if (this.options.autoStart && !this.completed) {
            this.init();
        }
    }

    /**
     * Initialize tooltips system
     */
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.start());
        } else {
            this.start();
        }
    }

    /**
     * Check if user has completed onboarding
     */
    isCompleted() {
        return localStorage.getItem(this.options.storageKey) === 'completed';
    }

    /**
     * Start the onboarding tour
     */
    start() {
        if (this.completed) return;

        this.currentStep = 0;
        this.showTooltip(this.currentStep);
    }

    /**
     * Show tooltip for specific step
     */
    showTooltip(stepIndex) {
        const tooltips = this.getTooltips();
        if (stepIndex >= tooltips.length) {
            this.complete();
            return;
        }

        const tooltip = tooltips[stepIndex];
        const element = document.querySelector(tooltip.element);

        if (!element) {
            // Element not found, skip to next
            this.next();
            return;
        }

        // Create tooltip overlay
        this.createOverlay();

        // Highlight element
        this.highlightElement(element);

        // Create tooltip popup
        this.createTooltipPopup(element, tooltip, stepIndex, tooltips.length);
    }

    /**
     * Create dark overlay
     */
    createOverlay() {
        const existingOverlay = document.getElementById('onboarding-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }

        const overlay = document.createElement('div');
        overlay.id = 'onboarding-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 9998;
            backdrop-filter: blur(2px);
        `;
        
        overlay.addEventListener('click', () => this.skip());
        document.body.appendChild(overlay);
    }

    /**
     * Highlight target element
     */
    highlightElement(element) {
        const existingHighlight = document.getElementById('onboarding-highlight');
        if (existingHighlight) {
            existingHighlight.remove();
        }

        const rect = element.getBoundingClientRect();
        const highlight = document.createElement('div');
        highlight.id = 'onboarding-highlight';
        highlight.style.cssText = `
            position: fixed;
            top: ${rect.top - 8}px;
            left: ${rect.left - 8}px;
            width: ${rect.width + 16}px;
            height: ${rect.height + 16}px;
            border: 3px solid #3B82F6;
            border-radius: 8px;
            z-index: 9999;
            pointer-events: none;
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
            animation: pulse 2s ease-in-out infinite;
        `;

        document.body.appendChild(highlight);

        // Scroll element into view
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    /**
     * Create tooltip popup
     */
    createTooltipPopup(element, tooltip, stepIndex, totalSteps) {
        const existingPopup = document.getElementById('onboarding-popup');
        if (existingPopup) {
            existingPopup.remove();
        }

        const rect = element.getBoundingClientRect();
        const popup = document.createElement('div');
        popup.id = 'onboarding-popup';
        
        // Calculate position (prefer bottom, but adjust if near edge)
        let top = rect.bottom + 16;
        let left = rect.left;
        const placement = tooltip.placement || 'bottom';

        if (placement === 'top') {
            top = rect.top - 200; // Approximate height
        } else if (placement === 'left') {
            top = rect.top;
            left = rect.left - 320;
        } else if (placement === 'right') {
            top = rect.top;
            left = rect.right + 16;
        }

        popup.style.cssText = `
            position: fixed;
            top: ${top}px;
            left: ${left}px;
            max-width: 320px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            animation: tooltipFadeIn 0.3s ease;
        `;

        popup.innerHTML = `
            <div style="padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                    <h3 style="margin: 0; font-size: 1.125rem; font-weight: 600; color: #111827;">${tooltip.title}</h3>
                    <button onclick="window.onboardingTooltips.skip()" style="background: none; border: none; padding: 0; cursor: pointer; color: #6B7280; font-size: 20px; line-height: 1;">×</button>
                </div>
                <p style="margin: 0 0 16px 0; color: #6B7280; line-height: 1.5; font-size: 0.9375rem;">${tooltip.description}</p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 0.875rem; color: #9CA3AF;">
                        ${stepIndex + 1} of ${totalSteps}
                    </div>
                    <div style="display: flex; gap: 8px;">
                        ${stepIndex > 0 ? '<button onclick="window.onboardingTooltips.previous()" style="padding: 8px 16px; background: #F3F4F6; border: none; border-radius: 6px; cursor: pointer; font-weight: 500; color: #6B7280;">Back</button>' : ''}
                        <button onclick="window.onboardingTooltips.next()" style="padding: 8px 16px; background: #3B82F6; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;">
                            ${stepIndex < totalSteps - 1 ? 'Next' : 'Finish'}
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(popup);
    }

    /**
     * Get tooltips configuration
     */
    getTooltips() {
        // Override in specific pages
        return this.options.tooltips;
    }

    /**
     * Move to next step
     */
    next() {
        this.currentStep++;
        this.showTooltip(this.currentStep);
    }

    /**
     * Move to previous step
     */
    previous() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showTooltip(this.currentStep);
        }
    }

    /**
     * Skip onboarding
     */
    skip() {
        this.cleanup();
        localStorage.setItem(this.options.storageKey, 'skipped');
    }

    /**
     * Complete onboarding
     */
    complete() {
        this.cleanup();
        localStorage.setItem(this.options.storageKey, 'completed');
        
        // Show completion message
        this.showCompletionMessage();
    }

    /**
     * Show completion message
     */
    showCompletionMessage() {
        const message = document.createElement('div');
        message.style.cssText = `
            position: fixed;
            top: 24px;
            right: 24px;
            background: white;
            padding: 20px 24px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            z-index: 10001;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: tooltipFadeIn 0.3s ease;
        `;

        message.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <div>
                <div style="font-weight: 600; color: #111827;">You're all set!</div>
                <div style="font-size: 0.875rem; color: #6B7280;">Ready to start extracting receipts</div>
            </div>
        `;

        document.body.appendChild(message);

        setTimeout(() => {
            message.style.animation = 'tooltipFadeOut 0.3s ease';
            setTimeout(() => message.remove(), 300);
        }, 3000);
    }

    /**
     * Clean up tooltips
     */
    cleanup() {
        const overlay = document.getElementById('onboarding-overlay');
        const highlight = document.getElementById('onboarding-highlight');
        const popup = document.getElementById('onboarding-popup');

        if (overlay) overlay.remove();
        if (highlight) highlight.remove();
        if (popup) popup.remove();
    }

    /**
     * Reset onboarding (for testing)
     */
    reset() {
        localStorage.removeItem(this.options.storageKey);
        this.completed = false;
        this.start();
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes tooltipFadeIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes tooltipFadeOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-10px);
        }
    }

    @keyframes pulse {
        0%, 100% {
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
        }
        50% {
            box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.1);
        }
    }
`;
document.head.appendChild(style);

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OnboardingTooltips;
}
