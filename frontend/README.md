# PawVision Frontend

React + TypeScript + Vite frontend for PawVision Pet Entertainment System.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - High-quality UI components built on Radix UI
- **react-i18next** - Internationalization
- **Chart.js** - Data visualization
- **Lucide React** - Icon library

## Getting Started

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`. API requests are proxied to `http://localhost:5000`.

### Build

Build for production:

```bash
npm run build
```

The build output will be in `../static/dist` directory, ready to be served by the Flask backend.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── ui/         # shadcn/ui components
│   │   ├── Layout.tsx  # Main layout component
│   │   └── Toaster.tsx # Toast notification component
│   ├── pages/          # Page components (routes)
│   │   ├── ControlPage.tsx
│   │   ├── LibraryPage.tsx
│   │   ├── StatisticsPage.tsx
│   │   └── ConfigPage.tsx
│   ├── services/       # API service layer
│   │   ├── api.ts
│   │   ├── videoService.ts
│   │   ├── youtubeService.ts
│   │   ├── statisticsService.ts
│   │   └── configService.ts
│   ├── hooks/          # Custom React hooks
│   │   ├── useVideos.ts
│   │   ├── usePlaybackStatus.ts
│   │   ├── useConfig.ts
│   │   └── useToast.ts
│   ├── types/          # TypeScript type definitions
│   │   └── index.ts
│   ├── lib/            # Utilities
│   │   └── utils.ts
│   ├── i18n/           # Internationalization
│   │   ├── index.ts
│   │   └── locales/
│   │       └── en.json
│   ├── styles/         # Global styles
│   │   └── globals.css
│   ├── App.tsx         # Main App component
│   └── main.tsx        # Entry point
├── public/             # Static assets
├── index.html          # HTML template
├── vite.config.ts      # Vite configuration
├── tailwind.config.js  # Tailwind CSS configuration
├── tsconfig.json       # TypeScript configuration
└── package.json        # Dependencies and scripts
```

## Features

### Control Page
- Play/Pause/Stop video controls
- Volume control with slider
- Quick play menu for recent videos
- Real-time playback status updates

### Library Page
- Upload local video files
- Download videos from YouTube
- View all videos with metadata
- Play or delete videos
- Thumbnail display

### Statistics Page
- Total plays and duration
- Plays by day chart
- Plays by video chart
- Favorite video tracking

### Configuration Page
- General settings (auto-play, volume)
- GPIO hardware button configuration
- YouTube download quality settings
- Schedule settings for active hours

## API Integration

The frontend communicates with the Flask backend through REST API endpoints:

- `/api/video/*` - Video management
- `/api/youtube/*` - YouTube downloads
- `/api/statistics/*` - Statistics data
- `/api/config/*` - Configuration management

All API calls are handled through service layers in `src/services/`.

## Styling

The app uses Tailwind CSS with a custom theme based on PawVision brand colors:
- Primary (Orange): `#FF914D`
- Accent (Teal): `#2BA8A0`
- Destructive (Red): `#ee5a24`

Components from shadcn/ui provide consistent, accessible UI elements built on Radix UI primitives.

## Internationalization

The app supports multiple languages through react-i18next. Translation files are located in `src/i18n/locales/`.

To add a new language:
1. Create a new JSON file in `src/i18n/locales/` (e.g., `de.json`)
2. Add the translations following the same structure as `en.json`
3. Import and add to the resources in `src/i18n/index.ts`

## Contributing

When adding new features:
1. Create components in `src/components/`
2. Add pages in `src/pages/`
3. Add API services in `src/services/`
4. Add types in `src/types/`
5. Use hooks for state management
6. Follow the existing patterns and conventions

## License

This project is part of PawVision and shares the same license.
