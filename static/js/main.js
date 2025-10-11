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
    
    // Load all modules sequentially with better error handling
    async function loadModules() {
        const failedModules = [];
        
        for (const module of modules) {
            try {
                await loadScript(module);
                console.log(`✅ Loaded: ${module}`);
            } catch (error) {
                console.error(`❌ Failed to load ${module}:`, error);
                failedModules.push(module);
                
                // Continue loading other modules instead of failing completely
                // Some modules might be optional or have fallbacks
                continue;
            }
        }
        
        if (failedModules.length > 0) {
            console.warn(`⚠️ Some modules failed to load: ${failedModules.join(', ')}`);
            console.warn('🔄 Application will continue with available modules');
        } else {
            console.log('🎉 All PawVision modules loaded successfully');
        }
        
        // Initialize the application after all modules are loaded (or failed)
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            // DOM is already ready, initialize immediately
            initializeApplication();
        } else {
            // Wait for DOM to be ready
            document.addEventListener('DOMContentLoaded', initializeApplication);
        }
    }
    
    // Separate initialization function for cleaner code
    function initializeApplication() {
        if (typeof PawVisionApp !== 'undefined') {
            try {
                PawVisionApp.init();
            } catch (error) {
                console.error('❌ Failed to initialize PawVision application:', error);
                // Show user-friendly error message
                setTimeout(() => {
                    const body = document.body;
                    if (body) {
                        body.innerHTML = `
                            <div style="padding: 40px; text-align: center; color: #ee5a24;">
                                <h2>⚠️ Application Error</h2>
                                <p>PawVision failed to initialize properly. Please refresh the page.</p>
                                <button onclick="location.reload()" style="padding: 10px 20px; margin-top: 20px; background: #2BA8A0; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                    🔄 Refresh Page
                                </button>
                            </div>
                        `;
                    }
                }, 100);
            }
        } else {
            console.error('❌ PawVisionApp not available, initialization skipped');
        }
    }
    
    // Start loading modules
    loadModules();
})();
