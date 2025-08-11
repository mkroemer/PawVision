# PawVision JavaScript Architecture

This project uses a modular JavaScript architecture to improve maintainability, testability, and organization.

## File Structure

```
static/js/
├── main.js          # Module loader (entry point)
├── app.js           # Main application controller
├── utils.js         # Core utilities and helper functions
├── navigation.js    # Tab navigation and routing
├── modals.js        # Modal system (general, progress, delete)
├── forms.js         # Form handling and validation
├── video.js         # Video management (play, stop, edit, delete)
├── youtube.js       # YouTube functionality (validate, download, add)
└── statistics.js    # Statistics and chart management
```

## Module Dependencies

```
utils.js (no dependencies)
├── navigation.js (uses utils)
├── modals.js (uses utils)
├── forms.js (uses utils)
├── video.js (uses utils, modals)
├── youtube.js (uses utils, modals)
├── statistics.js (uses utils, modals)
└── app.js (coordinates all modules)
```

## Module Responsibilities

### utils.js - Core Utilities
- `showStatus()` - User feedback messages
- `formatTime()` - Time formatting utilities
- `formatDuration()` - Duration formatting
- `debounce()` - Function throttling
- `apiRequest()` - Centralized API calls

### navigation.js - Navigation & Routing
- Tab switching functionality
- URL hash management
- Page state handling
- Navigation initialization

### modals.js - Modal System
- General modal system with multiple types
- Progress modals for downloads
- Delete confirmation dialogs
- Modal animations and keyboard handling

### forms.js - Form Management
- Form validation
- Settings toggles (button/motion sensor)
- Schedule item management
- Auto-save functionality
- Form submission handling

### video.js - Video Management
- Video playback controls (play/stop)
- Video editing modal
- Video deletion
- Video list management

### youtube.js - YouTube Integration
- URL validation and title fetching
- Video downloading with progress
- Quick add vs advanced forms
- YouTube-specific messaging

### statistics.js - Statistics & Charts
- Statistics data loading
- Chart.js integration
- Hourly usage charts
- Statistics clearing

### app.js - Main Application
- Module coordination
- Global event handling
- Application initialization
- Error handling

## Design Patterns Used

### 1. Module Pattern
Each file exports a module object with related functionality:

```javascript
const ModuleName = {
    method1() { /* ... */ },
    method2() { /* ... */ },
    init() { /* ... */ }
};
```

### 2. Backward Compatibility
Global functions are maintained for existing HTML:

```javascript
function globalFunction() {
    ModuleName.method();
}
```

### 3. Dependency Injection
Modules check for dependencies before using them:

```javascript
if (typeof ModuleName !== 'undefined') {
    ModuleName.method();
}
```

### 4. Event-Driven Architecture
Modules communicate through events and callbacks:

```javascript
element.addEventListener('event', () => Module.handler());
```

## Usage Examples

### Adding a New Modal
```javascript
Modals.showModal({
    title: 'Confirmation',
    message: 'Are you sure?',
    type: 'confirm',
    confirmText: 'Yes',
    cancelText: 'No',
    showCancel: true,
    onConfirm: () => console.log('Confirmed!')
});
```

### Making an API Call
```javascript
apiRequest('/api/endpoint', {
    method: 'POST',
    body: JSON.stringify(data)
})
.then(result => {
    showStatus('Success!', false);
})
.catch(error => {
    showStatus('Error occurred', true);
});
```

### Adding Form Validation
```javascript
const validation = Forms.validateForm(formElement);
if (!validation.valid) {
    showStatus(validation.errors.join('\n'), true);
    return;
}
```

## Development Guidelines

### Adding New Functionality
1. Determine which module the functionality belongs to
2. Add methods to the appropriate module object
3. Provide backward-compatible global functions if needed
4. Update the module's `init()` method if event listeners are needed

### Error Handling
- Use try-catch blocks for async operations
- Always provide user feedback via `showStatus()`
- Log errors to console for debugging
- Provide fallback behavior when possible

### Testing Considerations
- Each module can be tested independently
- Global functions can be tested without module knowledge
- Mock dependencies using feature detection patterns

## Browser Support

- Modern browsers (Chrome 88+, Firefox 85+, Safari 14+)
- ES6+ features (arrow functions, destructuring, async/await)
- Promises and Fetch API
- DOM manipulation and event handling

## Migration from Monolithic File

The original `pawvision.js` file has been completely replaced with modular architecture while maintaining:
- ✅ All existing functionality
- ✅ Backward compatibility with HTML onclick handlers
- ✅ Same global function names for HTML integration
- ✅ Identical behavior and UI

### Loading Strategy
- **Modular Loading**: All functionality now loads via `js/main.js`
- **No Fallback**: Fully committed to modular architecture
- **Development**: Can load individual modules for debugging

## Production Optimization

For production deployment, consider:
1. **Bundling**: Combine modules into a single file
2. **Minification**: Compress JavaScript for smaller file sizes
3. **Tree Shaking**: Remove unused functions
4. **Caching**: Use proper cache headers for static files

## Future Enhancements

The modular architecture enables:
- **Unit Testing**: Test individual modules
- **Code Splitting**: Load modules on demand
- **Progressive Enhancement**: Load features based on capability
- **Team Development**: Multiple developers can work on different modules
- **Plugin System**: Easy addition of new features
