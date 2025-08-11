// PawVision Navigation System
// Single Page Application (SPA) controller for tab management

/**
 * Main SPA Navigation Controller
 * Handles tab switching, URL management, and state persistence
 */
const SPA = {
    currentTab: 'control',
    
    /**
     * Switch to a specific tab
     * @param {Event} event - Click event (optional)
     * @param {string} tabName - Name of tab to switch to
     */
    switchTab(event, tabName) {
        // Prevent default if it's a button
        if (event) {
            event.preventDefault();
        }
        
        // Don't switch if already active
        if (this.currentTab === tabName) {
            return;
        }
        
        // Hide all tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none'; // Ensure hidden
        });
        
        // Remove active class from all tabs
        document.querySelectorAll('.header-link').forEach(tab => {
            tab.classList.remove('active');
            tab.removeAttribute('aria-current');
        });
        
        // Show selected tab content
        const selectedContent = document.getElementById(tabName);
        if (selectedContent) {
            selectedContent.style.display = 'block'; // Show before adding active class
            selectedContent.classList.add('active');
        }
        
        // Mark selected tab as active
        if (event && event.target) {
            event.target.classList.add('active');
            event.target.setAttribute('aria-current', 'page');
        } else {
            // If no event (programmatic call), find and activate the correct tab button
            const tabButtons = document.querySelectorAll('.header-link[data-tab]');
            tabButtons.forEach(button => {
                const tabAttr = button.getAttribute('data-tab');
                if (tabAttr === tabName) {
                    button.classList.add('active');
                    button.setAttribute('aria-current', 'page');
                }
            });
        }
        
        // Update current tab
        this.currentTab = tabName;
        
        // Update URL without page reload
        history.pushState({tab: tabName}, '', `#${tabName}`);
        
        // Initialize tab-specific functionality
        this.initializeTab(tabName);
        
        console.log(`Switched to ${tabName} tab`);
    },
    
    /**
     * Initialize tab-specific functionality
     * @param {string} tabName - Name of tab to initialize
     */
    initializeTab(tabName) {
        switch(tabName) {
            case 'control':
                // Refresh control status
                if (typeof VideoManager !== 'undefined') {
                    VideoManager.updateStatus();
                }
                break;
                
            case 'playlist':
                // Refresh video library
                if (typeof Library !== 'undefined') {
                    Library.refreshLibrary();
                }
                break;
                
            case 'statistics':
                // Load statistics data and charts
                if (typeof Statistics !== 'undefined') {
                    Statistics.initializeTab();
                }
                break;
                
            case 'config':
                // No specific initialization needed for config
                console.log('Configuration tab loaded');
                break;
        }
    },
    
    /**
     * Handle browser back/forward buttons
     * @param {PopStateEvent} event - Browser navigation event
     */
    handlePopState(event) {
        if (event.state && event.state.tab) {
            // Find and click the appropriate tab
            const tabButton = document.querySelector(`.header-link[data-tab="${event.state.tab}"]`);
            if (tabButton) {
                this.switchTab({target: tabButton}, event.state.tab);
            }
        }
    },
    
    /**
     * Initialize from URL hash
     */
    initFromHash() {
        const hash = window.location.hash.slice(1); // Remove #
        if (hash && ['control', 'playlist', 'statistics', 'config'].includes(hash)) {
            const tabButton = document.querySelector(`.header-link[data-tab="${hash}"]`);
            if (tabButton) {
                this.switchTab({target: tabButton}, hash);
            }
        }
    },
    
    /**
     * Initialize the SPA system
     */
    init() {
        // Handle browser navigation
        window.addEventListener('popstate', (event) => this.handlePopState(event));
        
        // Initialize from URL hash
        this.initFromHash();
        
        // Set initial state if no hash
        if (!window.location.hash) {
            history.replaceState({tab: this.currentTab}, '', `#${this.currentTab}`);
        }
        
        // Initialize the current tab
        this.initializeTab(this.currentTab);
        
        console.log('SPA Navigation system initialized');
    }
};

// Legacy Navigation object for backwards compatibility
const Navigation = {
    openTab: function(event, tabName) {
        SPA.switchTab(event, tabName);
    },
    init: function() {
        SPA.init();
    }
};

// Global function for backwards compatibility
function openTab(event, tabName) {
    SPA.switchTab(event, tabName);
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SPA, Navigation };
}
