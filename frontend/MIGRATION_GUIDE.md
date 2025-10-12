# PawVision Frontend Migration Guide

## Overview

The PawVision frontend has been completely rewritten from vanilla JavaScript to a modern React application with TypeScript, using Vite as the build tool, Tailwind CSS for styling, shadcn/ui for components, and react-i18next for internationalization.

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

Or use the setup script:

```bash
cd frontend
./setup.sh
```

### 2. Start Development Server

```bash
npm run dev
```

The development server will start at `http://localhost:3000` with hot module replacement (HMR).

### 3. Build for Production

```bash
npm run build
```

This will create an optimized production build in `../static/dist/`.

## Architecture Changes

### Before (Vanilla JS)
```
static/
├── js/
│   ├── main.js (module loader)
│   ├── app.js
│   ├── navigation.js
│   ├── control.js
│   ├── library.js
│   ├── etc...
├── css/
│   ├── main.css
│   ├── buttons.css
│   ├── etc...
└── locales/
    └── en.json

templates/
└── dashboard.html (Jinja2 template)
```

### After (React + TypeScript)
```
frontend/
├── src/
│   ├── components/     # React components
│   ├── pages/          # Page components (routes)
│   ├── services/       # API layer
│   ├── hooks/          # Custom hooks
│   ├── types/          # TypeScript types
│   ├── lib/            # Utilities
│   ├── i18n/           # Internationalization
│   └── styles/         # Global styles
├── public/             # Static assets
└── [config files]

Build output → ../static/dist/
```

## Key Features

### 1. **Type Safety with TypeScript**
All components, functions, and API calls are fully typed, providing:
- Better IDE support with autocomplete
- Compile-time error detection
- Self-documenting code
- Easier refactoring

### 2. **Component-Based Architecture**
- Reusable UI components from shadcn/ui
- Clean separation of concerns
- Easy to test and maintain
- Consistent design system

### 3. **Modern Build System (Vite)**
- Lightning-fast HMR during development
- Optimized production builds
- Built-in TypeScript support
- Tree-shaking for smaller bundle sizes

### 4. **Tailwind CSS**
- Utility-first CSS framework
- No more CSS conflicts
- Responsive design built-in
- Dark mode support ready
- Custom PawVision theme colors

### 5. **React Router**
- Client-side routing
- Fast navigation without page reloads
- Cleaner URLs
- Better user experience

### 6. **Internationalization (i18next)**
- Easy to add new languages
- Type-safe translations
- Lazy loading of translation files
- Pluralization and formatting support

## Development Workflow

### Running the Dev Server

```bash
npm run dev
```

- API requests are proxied to `http://localhost:5000`
- Hot module replacement for instant updates
- TypeScript type checking in real-time

### Building for Production

```bash
npm run build
```

This:
1. Type-checks the entire codebase
2. Builds an optimized production bundle
3. Outputs to `../static/dist/`
4. Minifies and compresses assets

### Previewing Production Build

```bash
npm run preview
```

### Linting

```bash
npm run lint
```

## Backend Integration

The Flask backend needs to be updated to serve the React app instead of Jinja2 templates.

### Option 1: Development Mode (Recommended)

Run both servers:
```bash
# Terminal 1: Flask backend
python main.py

# Terminal 2: React frontend
cd frontend && npm run dev
```

The React dev server (port 3000) will proxy API requests to Flask (port 5000).

### Option 2: Production Mode

Build the React app and serve it from Flask:

```bash
# Build frontend
cd frontend && npm run build

# Start Flask (serves from static/dist/)
python main.py
```

Update Flask to serve the React app (see backend integration section below).

## Backend Changes Required

### Update web_interface.py

The Flask app needs to serve the React SPA. Here's a minimal example:

```python
from flask import Flask, send_from_directory
import os

# ... existing code ...

@app.route('/')
@app.route('/<path:path>')
def serve_react_app(path=''):
    """Serve the React application."""
    dist_dir = os.path.join(app.static_folder, 'dist')
    
    if path and os.path.exists(os.path.join(dist_dir, path)):
        return send_from_directory(dist_dir, path)
    else:
        return send_from_directory(dist_dir, 'index.html')
```

### API Endpoints

All existing API endpoints should continue to work:
- `/api/video/*`
- `/api/youtube/*`
- `/api/statistics/*`
- `/api/config/*`

No changes needed to the API layer!

## Component Overview

### Pages
- **ControlPage** - Play/pause/stop controls, volume, quick play
- **LibraryPage** - Video library management, upload, YouTube downloads
- **StatisticsPage** - Charts and analytics (needs Chart.js integration)
- **ConfigPage** - Settings and configuration

### UI Components (shadcn/ui)
- Button, Input, Label
- Card, Dialog, Toast
- Tabs, Switch
- And more...

### Custom Hooks
- `useVideos` - Fetch and manage videos
- `usePlaybackStatus` - Real-time playback status
- `useConfig` - Configuration management
- `useToast` - Toast notifications

### Services
- `api.ts` - Base API client
- `videoService.ts` - Video operations
- `youtubeService.ts` - YouTube downloads
- `statisticsService.ts` - Statistics data
- `configService.ts` - Configuration

## Customization

### Adding New Pages

1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/Layout.tsx`

### Adding New Components

1. Create component in `src/components/`
2. Use shadcn/ui primitives for consistency
3. Apply Tailwind classes for styling

### Modifying Theme Colors

Edit `frontend/tailwind.config.js`:

```js
colors: {
  pawvision: {
    orange: "#FF914D",
    teal: "#2BA8A0",
    // Add more colors...
  },
}
```

### Adding Translations

1. Add keys to `src/i18n/locales/en.json`
2. Use in components: `const { t } = useTranslation()`
3. Access translations: `t('key.path')`

## Migration Benefits

### Performance
- ✅ Faster initial load (code splitting)
- ✅ Faster navigation (client-side routing)
- ✅ Smaller bundle size (tree-shaking)
- ✅ Better caching

### Developer Experience
- ✅ Type safety catches bugs early
- ✅ Hot module replacement for instant updates
- ✅ Better IDE support
- ✅ Modern tooling (Vite, ESLint, TypeScript)
- ✅ Component reusability

### User Experience
- ✅ Smoother interactions
- ✅ No page reloads
- ✅ Better accessibility (Radix UI primitives)
- ✅ Responsive design
- ✅ Consistent UI

### Maintainability
- ✅ Clear project structure
- ✅ Separation of concerns
- ✅ Easy to test
- ✅ Self-documenting code
- ✅ Reusable components

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Build Errors

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

### Type Errors

```bash
# Check for type errors
npm run build
```

### API Connection Issues

Check that:
1. Flask backend is running on port 5000
2. Vite proxy is configured correctly in `vite.config.ts`
3. CORS is properly configured in Flask

## Future Enhancements

- [ ] Implement Chart.js integration for statistics
- [ ] Add drag-and-drop video upload
- [ ] Add video preview/thumbnails
- [ ] Implement dark mode toggle
- [ ] Add more languages
- [ ] Add unit tests (Vitest)
- [ ] Add E2E tests (Playwright)
- [ ] Add Progressive Web App (PWA) support
- [ ] Optimize images and assets
- [ ] Add service worker for offline support

## Resources

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [React Router](https://reactrouter.com/)
- [react-i18next](https://react.i18next.com/)

## Support

For issues or questions:
1. Check the README.md in the frontend directory
2. Review this migration guide
3. Check existing code examples
4. Refer to the official documentation for each tool

---

Happy coding! 🐾
