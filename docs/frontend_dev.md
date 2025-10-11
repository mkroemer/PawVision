# PawVision Frontend Development Guide

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Setup](#development-setup)
3. [Module System](#module-system)
4. [Component Guidelines](#component-guidelines)
5. [Styling Standards](#styling-standards)
6. [JavaScript Best Practices](#javascript-best-practices)
7. [Testing Strategy](#testing-strategy)
8. [Common Patterns](#common-patterns)
9. [Debugging Guide](#debugging-guide)
10. [Performance Guidelines](#performance-guidelines)
11. [Contributing Workflow](#contributing-workflow)

## 🏗️ Architecture Overview

### **Frontend Stack**
- **Core:** Vanilla JavaScript ES6+ with module pattern
- **Styling:** Modular CSS with CSS Custom Properties
- **UI Framework:** Single Page Application (SPA) with tab navigation
- **Build System:** No build step - direct browser execution
- **Module Loading:** Sequential dependency-based loading

### **Directory Structure**
```
static/
├── js/
│   ├── main.js              # Module loader and entry point
│   ├── utils.js             # Core utilities and NotificationSystem
│   ├── navigation.js        # SPA navigation controller
│   ├── modal.js             # Universal modal system
│   ├── video.js             # Video management
│   ├── youtube.js           # YouTube integration
│   ├── library.js           # Video library management
│   ├── statistics.js        # Analytics and charts
│   ├── forms.js             # Form handling and validation
│   ├── control.js           # Control center functionality
│   ├── config.js            # Configuration management
│   └── app.js               # Main application controller
├── css/
│   ├── main.css             # CSS entry point (imports all others)
│   ├── base.css             # Variables, reset, typography
│   ├── layout.css           # Layout components
│   ├── components.css       # UI components and utilities
│   ├── buttons.css          # Button styles
│   ├── forms.css            # Form styles
│   ├── modals.css           # Modal system styles
│   ├── control.css          # Control page specific
│   ├── statistics.css       # Statistics page specific
│   └── config.css           # Configuration page specific
└── chart.min.js             # Third-party chart library

templates/
├── dashboard.html           # Main SPA container
└── includes/
    ├── header.html          # Page header
    ├── footer.html          # Page footer
    ├── control_content.html # Control tab content
    ├── playlist_content.html# Playlist tab content
    ├── statistics_content.html# Statistics tab content
    └── config_content.html  # Configuration tab content
```

### **Data Flow Architecture**
```
User Interaction → Component Handler → API Call → Backend → Response → UI Update → NotificationSystem
                                    ↓
                            Error Handler → NotificationSystem
```

## 🛠️ Development Setup

### **Prerequisites**
- Modern browser with ES6+ support
- Python backend running on localhost:5001
- Code editor with JavaScript and CSS support

### **Local Development**
```bash
# Navigate to project directory
cd PawVision

# Activate Python environment
source venv/bin/activate

# Start backend server
python main.py

# Open frontend in browser
open http://localhost:5001
```

### **Development Tools**
- **Browser DevTools:** Primary debugging tool
- **VS Code Extensions:**
  - Live Server (for static testing)
  - JavaScript (ES6) code snippets
  - CSS Intellisense
- **Testing:** `test_frontend.html` for component testing

## 📦 Module System

### **Module Loading Sequence**
```javascript
// Defined in static/js/main.js
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
```

### **Module Structure Pattern**
```javascript
// Standard module structure
const ModuleName = {
    // Private properties
    _privateProperty: null,
    
    // Public methods
    publicMethod() {
        // Implementation
    },
    
    // Initialization
    init() {
        console.log('ModuleName initialized');
    }
};

// Export for module usage (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModuleName;
}
```

### **Module Dependencies**
- **Level 1:** `utils.js` (no dependencies)
- **Level 2:** `modal.js`, `navigation.js` (depend on utils)
- **Level 3:** `forms.js`, `video.js`, `library.js` (depend on Level 1-2)
- **Level 4:** `youtube.js`, `control.js`, `config.js`, `statistics.js` (depend on Level 1-3)
- **Level 5:** `app.js` (coordinates all modules)

## 🧩 Component Guidelines

### **Notification System**
```javascript
// Use the unified notification system for all user feedback
NotificationSystem.show('Operation successful!', 'success');
NotificationSystem.show('Error occurred', 'error');
NotificationSystem.show('Please check this', 'warning');
NotificationSystem.show('Information message', 'info');

// Legacy compatibility (still supported)
showStatus('Legacy message', false); // success
showStatus('Legacy error', true);    // error
```

### **Modal System**
```javascript
// Confirmation modal
Modal.confirm({
    title: 'Confirm Action',
    message: 'Are you sure you want to proceed?',
    confirmText: 'Yes, Continue',
    cancelText: 'Cancel',
    type: 'danger',
    onConfirm: () => {
        // Handle confirmation
    },
    onCancel: () => {
        // Handle cancellation
    }
});

// Form modal
Modal.form({
    title: 'Edit Settings',
    fields: [
        { name: 'title', type: 'text', label: 'Title', value: 'Current Title' },
        { name: 'duration', type: 'number', label: 'Duration (seconds)', value: 120 }
    ],
    submitText: 'Save Changes',
    onSubmit: async (data) => {
        // Handle form submission
        // Return true to close modal, false to keep open
        return true;
    }
});
```

### **SPA Navigation**
```javascript
// Switch tabs programmatically
SPA.switchTab(null, 'statistics');

// Tab initialization hooks
const Statistics = {
    initializeTab() {
        // Called when statistics tab becomes active
        this.loadData();
        this.renderChart();
    }
};
```

### **API Communication**
```javascript
// Use the apiRequest utility for consistent error handling
try {
    const data = await apiRequest('/api/endpoint', {
        method: 'POST',
        body: JSON.stringify(payload)
    });
    
    // Handle success
    NotificationSystem.show('Operation successful', 'success');
} catch (error) {
    console.error('API error:', error);
    NotificationSystem.show('Operation failed', 'error');
}
```

## 🎨 Styling Standards

### **CSS Architecture**
```css
/* Use CSS Custom Properties for consistency */
:root {
    --primary-color: #FF914D;
    --secondary-color: #2BA8A0;
    --success-color: #3EC1B9;
    --error-color: #ee5a24;
    --warning-color: #FFB142;
    --info-color: #4A90E2;
    
    --border-radius-small: 6px;
    --border-radius-medium: 10px;
    --border-radius-large: 15px;
    
    --spacing-xs: 5px;
    --spacing-sm: 10px;
    --spacing-md: 15px;
    --spacing-lg: 20px;
    --spacing-xl: 30px;
}
```

### **Component CSS Pattern**
```css
/* Component: notification-system */
.status-message {
    /* Base styles */
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
    
    /* Use custom properties */
    padding: var(--spacing-md) var(--spacing-lg);
    border-radius: var(--border-radius-small);
    
    /* Animations */
    transform: translateX(100%);
    transition: transform 0.3s ease-in-out;
}

.status-message[style*="block"] {
    transform: translateX(0);
}

/* Component variants */
.status-message.success {
    background-color: var(--success-color);
    color: white;
}

.status-message.error {
    background-color: var(--error-color);
    color: white;
}
```

### **Utility Classes**
```css
/* Utility classes for common patterns */
.hidden { display: none !important; }
.show { display: block !important; }
.text-center { text-align: center; }
.mt-sm { margin-top: var(--spacing-sm); }
.p-md { padding: var(--spacing-md); }
```

### **Responsive Design**
```css
/* Mobile-first approach */
.component {
    /* Mobile styles */
}

@media (min-width: 768px) {
    .component {
        /* Tablet styles */
    }
}

@media (min-width: 1024px) {
    .component {
        /* Desktop styles */
    }
}
```

## 💻 JavaScript Best Practices

### **Error Handling Pattern**
```javascript
async function apiOperation() {
    try {
        const response = await fetch('/api/endpoint');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success || data.status === 'success') {
            NotificationSystem.show('Operation successful', 'success');
            return data;
        } else {
            throw new Error(data.error || data.message || 'Operation failed');
        }
    } catch (error) {
        console.error('Operation failed:', error);
        NotificationSystem.show(error.message || 'Operation failed', 'error');
        throw error; // Re-throw for caller handling
    }
}
```

### **Event Handling Pattern**
```javascript
// Use event delegation for dynamic content
document.addEventListener('click', (e) => {
    // Handle specific button clicks
    if (e.target.closest('.edit-btn')) {
        const button = e.target.closest('.edit-btn');
        const path = button.dataset.path;
        
        e.preventDefault();
        e.stopPropagation();
        
        handleEdit(path);
    }
    
    if (e.target.closest('.delete-btn')) {
        const button = e.target.closest('.delete-btn');
        const path = button.dataset.path;
        
        e.preventDefault();
        e.stopPropagation();
        
        handleDelete(path);
    }
});
```

### **Async/Await Pattern**
```javascript
// Prefer async/await over promises
async function loadData() {
    try {
        // Show loading state
        const loadingElement = document.getElementById('loading');
        loadingElement.classList.remove('hidden');
        
        const data = await apiRequest('/api/data');
        
        // Update UI
        updateInterface(data);
        
    } catch (error) {
        // Handle error
        showErrorState(error.message);
    } finally {
        // Hide loading state
        const loadingElement = document.getElementById('loading');
        loadingElement.classList.add('hidden');
    }
}
```

### **Debouncing Pattern**
```javascript
// Use debouncing for frequent events
const debouncedSearch = debounce((query) => {
    performSearch(query);
}, 300);

searchInput.addEventListener('input', (e) => {
    debouncedSearch(e.target.value);
});
```

## 🧪 Testing Strategy

### **Manual Testing Checklist**
- [ ] All notifications display correctly
- [ ] Tab navigation works smoothly
- [ ] Forms validate properly
- [ ] Error states display appropriately
- [ ] Mobile responsiveness
- [ ] Browser compatibility (Chrome, Firefox, Safari)

### **Component Testing**
```javascript
// Use test_frontend.html for component testing
function testComponent() {
    try {
        // Test setup
        const testData = { test: 'data' };
        
        // Execute test
        const result = ComponentName.testMethod(testData);
        
        // Verify result
        if (result.success) {
            log('✅ Test passed', 'success');
        } else {
            log('❌ Test failed', 'error');
        }
    } catch (error) {
        log(`❌ Test error: ${error.message}`, 'error');
    }
}
```

### **Error Simulation**
```javascript
// Test error handling
function simulateError() {
    // Simulate network error
    fetch('/api/nonexistent')
        .catch(error => {
            console.log('Expected error caught:', error);
        });
        
    // Test notification system
    NotificationSystem.show('Test error message', 'error');
}
```

## 🔧 Common Patterns

### **Loading States**
```javascript
async function operationWithLoading(element) {
    try {
        // Show loading
        element.classList.add('loading');
        element.disabled = true;
        
        // Perform operation
        const result = await apiRequest('/api/operation');
        
        // Handle success
        return result;
    } finally {
        // Hide loading
        element.classList.remove('loading');
        element.disabled = false;
    }
}
```

### **Form Validation**
```javascript
function validateForm(formData) {
    const errors = [];
    
    // Required field validation
    if (!formData.get('title')) {
        errors.push('Title is required');
    }
    
    // Format validation
    const email = formData.get('email');
    if (email && !isValidEmail(email)) {
        errors.push('Valid email is required');
    }
    
    return {
        valid: errors.length === 0,
        errors: errors
    };
}
```

### **Data Refresh Pattern**
```javascript
const DataManager = {
    _refreshing: false,
    
    async refresh() {
        // Prevent duplicate refreshes
        if (this._refreshing) {
            console.warn('Refresh already in progress');
            return;
        }
        
        this._refreshing = true;
        
        try {
            const data = await apiRequest('/api/data');
            this.updateUI(data);
        } finally {
            this._refreshing = false;
        }
    }
};
```

## 🐛 Debugging Guide

### **Console Debugging**
```javascript
// Enable debug mode
const DEBUG = true;

function debug(message, data = null) {
    if (DEBUG) {
        console.log(`[DEBUG] ${message}`, data || '');
    }
}

// Use throughout code
debug('Starting operation', { operation: 'test' });
```

### **Common Issues and Solutions**

#### **Module Not Loading**
```javascript
// Check module dependencies
console.log('Available modules:', {
    utils: typeof NotificationSystem !== 'undefined',
    navigation: typeof SPA !== 'undefined',
    video: typeof VideoManager !== 'undefined'
});
```

#### **Notification Not Showing**
```javascript
// Debug notification system
if (typeof NotificationSystem !== 'undefined') {
    NotificationSystem.show('Test notification', 'info');
} else {
    console.error('NotificationSystem not available');
    // Fallback
    alert('Fallback notification');
}
```

#### **API Request Failing**
```javascript
// Debug API requests
async function debugApiRequest(url, options) {
    console.log('API Request:', { url, options });
    
    try {
        const response = await fetch(url, options);
        console.log('API Response:', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries())
        });
        
        const data = await response.json();
        console.log('API Data:', data);
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}
```

### **Browser DevTools Usage**
- **Console:** Monitor logs and execute debug commands
- **Network:** Monitor API requests and responses
- **Elements:** Inspect DOM changes and CSS issues
- **Sources:** Set breakpoints in JavaScript code

## ⚡ Performance Guidelines

### **Optimization Best Practices**
```javascript
// Batch DOM updates
function batchUpdate(items) {
    const fragment = document.createDocumentFragment();
    
    items.forEach(item => {
        const element = createItemElement(item);
        fragment.appendChild(element);
    });
    
    container.appendChild(fragment);
}

// Use requestAnimationFrame for animations
function smoothUpdate() {
    requestAnimationFrame(() => {
        // Perform DOM updates
        updateElement();
    });
}

// Debounce expensive operations
const expensiveOperation = debounce(function() {
    // Heavy computation
}, 300);
```

### **Memory Management**
```javascript
// Clean up event listeners
const controller = new AbortController();

element.addEventListener('click', handler, {
    signal: controller.signal
});

// Later: clean up
controller.abort();

// Clean up timers
const timerId = setTimeout(callback, 1000);
// Later: clearTimeout(timerId);
```

### **Loading Performance**
- Minimize module dependencies
- Use event delegation instead of multiple listeners
- Lazy load non-critical components
- Cache DOM queries

## 👨‍💻 Contributing Workflow

### **Development Process**
1. **Setup:** Follow development setup instructions
2. **Branch:** Create feature branch from `dev`
3. **Develop:** Make changes following this guide
4. **Test:** Use `test_frontend.html` and manual testing
5. **Document:** Update relevant documentation
6. **Submit:** Create pull request to `dev` branch

### **Code Review Checklist**
- [ ] Follows module structure patterns
- [ ] Uses unified notification system
- [ ] Proper error handling implemented
- [ ] No inline styles in templates
- [ ] CSS follows custom property usage
- [ ] Console errors are addressed
- [ ] Mobile responsiveness tested
- [ ] Documentation updated

### **Commit Message Format**
```
type(scope): description

Examples:
feat(notifications): add unified notification system
fix(navigation): resolve tab switching issue
style(css): improve button component styling
docs(frontend): update development guide
```

### **Pull Request Template**
```markdown
## Changes Made
- Brief description of changes
- List of modified files
- New features added

## Testing
- [ ] Manual testing completed
- [ ] Component tests pass
- [ ] Cross-browser testing done

## Documentation
- [ ] Code comments updated
- [ ] User documentation updated
- [ ] Developer documentation updated
```

## 📚 Additional Resources

### **Reference Documentation**
- [MDN Web Docs](https://developer.mozilla.org/) - JavaScript and CSS reference
- [Can I Use](https://caniuse.com/) - Browser compatibility
- [CSS Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Flexbox Guide](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)

### **PawVision Specific**
- `FRONTEND_IMPROVEMENTS.md` - Recent improvements summary
- `test_frontend.html` - Component testing environment
- Backend API documentation in `docs/api.md`

### **Browser Support**
- **Primary:** Chrome 80+, Firefox 75+, Safari 13+
- **Mobile:** iOS Safari 13+, Chrome Mobile 80+
- **Features Used:** ES6 modules, CSS Custom Properties, Fetch API

---

**Last Updated:** August 11, 2025  
**Version:** 2.0 (Post-Frontend Improvements)  
**Maintainer:** PawVision Development Team
