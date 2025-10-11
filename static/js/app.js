// PawVision Main Application
// Entry point that coordinates all modules

/**
 * Main PawVision application controller
 */
const PawVisionApp = {
    initialized: false,
    
    /**
     * Initialize the application
     */
    async init() {
        // Prevent double initialization
        if (this.initialized) {
            console.log('⚠️ PawVision already initialized, skipping...');
            return;
        }
        
        console.log('🐾 PawVision JavaScript modules loaded');
        
        // Initialize i18n system first
        if (typeof I18n !== 'undefined') {
            await I18n.init('en'); // Default to English
        }
        
        // Initialize all modules in the correct order
        this.initModules();
        
        // Set up global event listeners
        this.setupGlobalListeners();
        
        // Handle initial page state
        this.handleInitialState();
        
        this.initialized = true;
        console.log('✅ PawVision application initialized');
    },

    /**
     * Initialize all modules
     */
    initModules() {
        // Initialize core modules
        if (typeof SPA !== 'undefined') {
            SPA.init();
        }

        if (typeof Modal !== 'undefined') {
            // Modal system doesn't need explicit initialization
            console.log('Modal system ready');
        }

        if (typeof Forms !== 'undefined') {
            Forms.init();
        }

        if (typeof VideoManager !== 'undefined') {
            VideoManager.init();
        }

        if (typeof YouTube !== 'undefined') {
            YouTube.init();
        }

        if (typeof Library !== 'undefined') {
            Library.init();
        }

        if (typeof Statistics !== 'undefined') {
            Statistics.init();
        }
    },

    /**
     * Set up global event listeners
     */
    setupGlobalListeners() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            if (typeof NotificationSystem !== 'undefined') {
                const message = typeof t !== 'undefined' ? t('app.error') : 'An unexpected error occurred';
                NotificationSystem.show(message, 'error');
            } else {
                showStatus('An unexpected error occurred', true);
            }
        });

        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            if (typeof NotificationSystem !== 'undefined') {
                const message = typeof t !== 'undefined' ? t('app.error') : 'An unexpected error occurred';
                NotificationSystem.show(message, 'error');
            } else {
                showStatus('An unexpected error occurred', true);
            }
        });

        // Handle offline/online status
        window.addEventListener('offline', () => {
            if (typeof NotificationSystem !== 'undefined') {
                const message = typeof t !== 'undefined' ? t('app.connectionLost') : 'Connection lost - some features may not work';
                NotificationSystem.show(message, 'warning', 6000);
            } else {
                showStatus('Connection lost - some features may not work', true);
            }
        });

        window.addEventListener('online', () => {
            if (typeof NotificationSystem !== 'undefined') {
                const message = typeof t !== 'undefined' ? t('app.connectionRestored') : 'Connection restored';
                NotificationSystem.show(message, 'success');
            } else {
                showStatus('Connection restored', false);
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            // Ctrl/Cmd + K to focus search (if implemented)
            if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
                event.preventDefault();
                const searchInput = document.querySelector('input[type="search"]');
                if (searchInput) {
                    searchInput.focus();
                }
            }

            // Escape to close any open modals
            if (event.key === 'Escape') {
                // Close any open modals
                if (typeof Modal !== 'undefined' && Modal.activeModals && Modal.activeModals.size > 0) {
                    // Let Modal system handle ESC key
                    return;
                }
                
                // Fallback for any remaining modals
                const openModals = document.querySelectorAll('.modal[style*="block"], .general-modal[style*="block"], .delete-modal[style*="block"]');
                openModals.forEach(modal => {
                    modal.style.display = 'none';
                });
                
                // Clean up modal body class
                document.body.classList.remove('modal-open');
            }
        });
    },

    /**
     * Handle initial page state
     */
    handleInitialState() {
        // Show welcome message on first visit
        if (!localStorage.getItem('pawvision_visited')) {
            setTimeout(() => {
                if (typeof NotificationSystem !== 'undefined') {
                    const message = typeof t !== 'undefined' ? t('app.welcome') : 'Welcome to PawVision! 🐾';
                    NotificationSystem.show(message, 'info', 5000);
                } else {
                    showStatus('Welcome to PawVision! 🐾', false);
                }
                localStorage.setItem('pawvision_visited', 'true');
            }, 1000);
        }
    },

    /**
     * Show loading state
     */
    showLoading(element) {
        if (element) {
            element.classList.add('loading');
            element.disabled = true;
        }
    },

    /**
     * Hide loading state
     */
    hideLoading(element) {
        if (element) {
            element.classList.remove('loading');
            element.disabled = false;
        }
    },

    /**
     * Refresh application data
     */
    refresh() {
        // Reload current page
        window.location.reload();
    }
};

// Initialize when DOM is ready (fallback if not initialized by main.js)
document.addEventListener('DOMContentLoaded', function() {
    // Small delay to let main.js handle initialization first
    setTimeout(() => {
        if (!PawVisionApp.initialized) {
            PawVisionApp.init();
        }
    }, 100);
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PawVisionApp;
}
