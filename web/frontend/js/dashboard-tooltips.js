/**
 * Dashboard Onboarding Tooltips Configuration
 * Guides first-time users through the dashboard
 */

// Dashboard tooltips configuration
const dashboardTooltips = [
    {
        element: '.sidebar-link[data-section="overview"]',
        title: 'Welcome to Your Dashboard! 👋',
        description: 'This is your command center for receipt extraction. Let\'s take a quick tour to get you started.',
        placement: 'right'
    },
    {
        element: '.sidebar-link[data-section="extractions"]',
        title: 'View Extractions',
        description: 'Access all your processed receipts here. You can search, filter, and export your extraction history.',
        placement: 'right'
    },
    {
        element: '.sidebar-link[data-section="batch"]',
        title: 'Batch Processing',
        description: 'Upload multiple receipts at once and process them in parallel. Perfect for end-of-month expense reports!',
        placement: 'right'
    },
    {
        element: '.sidebar-link[data-section="api"]',
        title: 'API Keys',
        description: 'Generate API keys to integrate receipt extraction into your own applications and workflows.',
        placement: 'right'
    },
    {
        element: '#userMenuBtn',
        title: 'Your Account',
        description: 'Access your profile settings, subscription details, and billing information from here.',
        placement: 'bottom'
    },
    {
        element: '#notificationsBtn',
        title: 'Stay Updated',
        description: 'Get notified about completed extractions, API usage alerts, and important account updates.',
        placement: 'bottom'
    }
];

// Initialize tooltips when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboardTooltips);
} else {
    initDashboardTooltips();
}

function initDashboardTooltips() {
    // Only show on dashboard page
    if (!document.body.classList.contains('dashboard-page')) {
        return;
    }

    // Create onboarding instance
    window.onboardingTooltips = new OnboardingTooltips({
        storageKey: 'receipt_extractor_dashboard_onboarding',
        tooltips: dashboardTooltips,
        autoStart: true
    });

    // Add reset button for testing (remove in production)
    if (window.location.search.includes('reset_onboarding')) {
        window.onboardingTooltips.reset();
    }
}
