// PawVision Control Center Management
// Auto-refresh status and control center functionality

/**
 * Control center management
 */
const ControlCenter = {
    statusInterval: null,

    /**
     * Start auto-refresh of status when control tab is active
     */
    startStatusRefresh() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }
        
        this.statusInterval = setInterval(() => {
            if (typeof SPA !== 'undefined' && SPA.currentTab === 'control' && typeof VideoManager !== 'undefined') {
                VideoManager.updateStatus();
            }
        }, 30000); // Refresh every 30 seconds
    },

    /**
     * Stop the status refresh interval
     */
    stopStatusRefresh() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    },

    /**
     * Initialize control center functionality
     */
    init() {
        this.startStatusRefresh();
        console.log('Control Center initialized');
    },

    /**
     * Cleanup when leaving control tab
     */
    cleanup() {
        this.stopStatusRefresh();
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ControlCenter.init();

    // Listen for tab changes to start/stop refresh
    document.addEventListener('tabChanged', function(e) {
        if (e.detail && e.detail.tab === 'control') {
            ControlCenter.startStatusRefresh();
        } else {
            ControlCenter.stopStatusRefresh();
        }
    });
});
