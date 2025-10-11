// PawVision Core Utilities
// Base utility functions and helpers

/**
 * Simple Internationalization System
 */
const I18n = {
    locale: 'en',
    translations: {},
    fallback: 'en',
    
    /**
     * Initialize the i18n system
     */
    async init(locale = 'en') {
        this.locale = locale;
        try {
            await this.loadTranslations(locale);
            console.log(`✅ Loaded translations for locale: ${locale}`);
        } catch (error) {
            console.error(`❌ Failed to load translations for ${locale}:`, error);
            if (locale !== this.fallback) {
                console.log(`🔄 Falling back to ${this.fallback} locale`);
                await this.loadTranslations(this.fallback);
            }
        }
    },
    
    /**
     * Load translations from JSON file
     */
    async loadTranslations(locale) {
        const response = await fetch(`/static/locales/${locale}.json`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        this.translations = await response.json();
    },
    
    /**
     * Get translated string
     * @param {string} key - Translation key (dot notation: 'app.title')
     * @param {Object} params - Parameters for string interpolation
     * @returns {string} Translated string
     */
    t(key, params = {}) {
        const keys = key.split('.');
        let value = this.translations;
        
        // Navigate through nested object
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                console.warn(`Translation missing for key: ${key}`);
                return key; // Return key if translation not found
            }
        }
        
        // Handle string interpolation
        if (typeof value === 'string' && Object.keys(params).length > 0) {
            return value.replace(/\{(\w+)\}/g, (match, paramKey) => {
                return params[paramKey] !== undefined ? params[paramKey] : match;
            });
        }
        
        return value;
    },
    
    /**
     * Check if translation exists
     */
    has(key) {
        const keys = key.split('.');
        let value = this.translations;
        
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                return false;
            }
        }
        
        return typeof value === 'string';
    },
    
    /**
     * Get current locale
     */
    getLocale() {
        return this.locale;
    },
    
    /**
     * Change locale dynamically
     */
    async setLocale(locale) {
        if (locale !== this.locale) {
            await this.init(locale);
            // Trigger re-render of UI elements if needed
            document.dispatchEvent(new CustomEvent('localeChanged', { 
                detail: { locale: locale }
            }));
        }
    }
};

// Global alias for convenience
const t = (key, params) => I18n.t(key, params);

/**
 * Universal notification system for PawVision
 * Handles all types of user notifications consistently
 */
const NotificationSystem = {
    /**
     * Show status message to user
     * @param {string} message - Message to display
     * @param {string} type - Message type ('success', 'error', 'warning', 'info')
     * @param {number} duration - Display duration in milliseconds (default: 4000)
     * @param {string} containerId - Optional container ID for scoped messages
     */
    show(message, type = 'info', duration = 4000, containerId = null) {
        // Try specific container first, then fallback to global
        let statusDiv = null;
        
        if (containerId) {
            statusDiv = document.getElementById(containerId);
        }
        
        if (!statusDiv) {
            statusDiv = document.getElementById('status-message');
        }
        
        if (!statusDiv) {
            // Create global status message element if it doesn't exist
            statusDiv = this.createStatusElement();
        }
        
        // Set message content
        statusDiv.textContent = message;
        statusDiv.className = `status-message ${type}`;
        
        // Apply styling based on type
        const styles = this.getTypeStyles(type);
        Object.assign(statusDiv.style, styles, {
            display: 'block',
            position: 'fixed',
            top: '20px',
            right: '20px',
            zIndex: '1000',
            padding: '15px 20px',
            borderRadius: '8px',
            fontWeight: '500',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            maxWidth: '400px',
            wordWrap: 'break-word'
        });
        
        // Clear any existing timeout
        if (statusDiv.hideTimeout) {
            clearTimeout(statusDiv.hideTimeout);
        }
        
        // Hide after specified duration
        statusDiv.hideTimeout = setTimeout(() => {
            statusDiv.style.display = 'none';
        }, duration);
        
        return statusDiv;
    },
    
    /**
     * Create global status message element
     */
    createStatusElement() {
        const statusDiv = document.createElement('div');
        statusDiv.id = 'status-message';
        statusDiv.style.display = 'none';
        document.body.appendChild(statusDiv);
        return statusDiv;
    },
    
    /**
     * Get styles for message type
     */
    getTypeStyles(type) {
        const styles = {
            success: {
                backgroundColor: 'rgba(62, 193, 185, 0.95)',
                color: 'white',
                border: '1px solid rgba(62, 193, 185, 0.8)'
            },
            error: {
                backgroundColor: 'rgba(255, 107, 107, 0.95)',
                color: 'white',
                border: '1px solid rgba(255, 107, 107, 0.8)'
            },
            warning: {
                backgroundColor: 'rgba(255, 177, 66, 0.95)',
                color: 'white',
                border: '1px solid rgba(255, 177, 66, 0.8)'
            },
            info: {
                backgroundColor: 'rgba(74, 144, 226, 0.95)',
                color: 'white',
                border: '1px solid rgba(74, 144, 226, 0.8)'
            }
        };
        
        return styles[type] || styles.info;
    },
    
    /**
     * Hide all visible notifications
     */
    hideAll() {
        const messages = document.querySelectorAll('.status-message[style*="block"]');
        messages.forEach(msg => {
            msg.style.display = 'none';
            if (msg.hideTimeout) {
                clearTimeout(msg.hideTimeout);
            }
        });
    }
};

/**
 * Legacy function for backwards compatibility
 * @deprecated Use NotificationSystem.show() instead
 */
function showStatus(message, isError = false) {
    const type = isError ? 'error' : 'success';
    return NotificationSystem.show(message, type, 3000);
}

/**
 * Format time in seconds to HH:MM:SS format
 * @param {number} seconds - Time in seconds
 * @returns {string} Formatted time string
 */
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
}

/**
 * Format duration in seconds to readable format
 * @param {number} seconds - Duration in seconds
 * @returns {string} Human-readable duration
 */
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
        const minutes = Math.round(seconds / 60);
        return `${minutes}m`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.round((seconds % 3600) / 60);
        return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
    }
}

/**
 * Debounce function to limit the rate of function execution
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Make API request with error handling
 * @param {string} url - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise} Response promise
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Export functions for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        I18n,
        t,
        NotificationSystem,
        showStatus, // Legacy compatibility
        formatTime,
        formatDuration,
        debounce,
        apiRequest
    };
}
