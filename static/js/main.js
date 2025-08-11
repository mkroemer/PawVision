// PawVision Main JavaScript Loader
// Loads all JavaScript modules in the correct order

// Load modules in dependency order
(function() {
    'use strict';
    
    // List of modules to load in order
    const modules = [
        '/static/js/utils.js',        // Core utilities (no dependencies)
        '/static/js/modal.js',        // Universal modal system
        '/static/js/navigation.js',   // Navigation system
        '/static/js/forms.js',        // Forms handling
        '/static/js/video.js',        // Video management
        '/static/js/library.js',      // Library management
        '/static/js/youtube.js',      // YouTube functionality
        '/static/js/control.js',      // Control center functionality
        '/static/js/config.js',       // Configuration management
        '/static/js/statistics.js',   // Statistics and charts
        '/static/js/app.js'           // Main application (depends on all others)
    ];
    
    // Function to load script dynamically
    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    // Load all modules sequentially
    async function loadModules() {
        try {
            for (const module of modules) {
                await loadScript(module);
                console.log(`✅ Loaded: ${module}`);
            }
            console.log('🎉 All PawVision modules loaded successfully');
            
            // Initialize the application after all modules are loaded
            if (document.readyState === 'complete' || document.readyState === 'interactive') {
                // DOM is already ready, initialize immediately
                if (typeof PawVisionApp !== 'undefined') {
                    PawVisionApp.init();
                }
            } else {
                // Wait for DOM to be ready
                document.addEventListener('DOMContentLoaded', function() {
                    if (typeof PawVisionApp !== 'undefined') {
                        PawVisionApp.init();
                    }
                });
            }
        } catch (error) {
            console.error('❌ Failed to load module:', error);
            throw error; // Re-throw to let caller handle
        }
    }
    
    // Start loading modules
    loadModules();
})();
