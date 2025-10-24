# Frontend Documentation

## Overview

The frontend is built with React, TypeScript, Vite, and Chakra UI v3, providing a modern, responsive interface for the Travya travel companion application.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │────│  TanStack Router│────│  API Client     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         └──────────────│  Chakra UI v3   │────│  Backend API    │
                        │  Components     │    │  (FastAPI)      │
                        └─────────────────┘    └─────────────────┘
```

## Tech Stack

- **React 18**: UI library with hooks and functional components
- **TypeScript**: Type-safe JavaScript development
- **Vite**: Fast build tool and development server
- **TanStack Router**: Type-safe routing
- **Chakra UI v3**: Component library (simplified for compatibility)
- **React Icons**: Icon library
- **Axios**: HTTP client for API calls

## Project Structure

```
frontend/
├── public/
│   ├── vite.svg
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── Common/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── SidebarItems.tsx
│   │   └── Layout/
│   │       └── Layout.tsx
│   ├── routes/
│   │   ├── _layout/
│   │   │   ├── index.tsx
│   │   │   ├── trips.tsx
│   │   │   ├── trips.$tripId.tsx
│   │   │   ├── plan-trip.tsx
│   │   │   └── chat.tsx
│   │   ├── _layout.tsx
│   │   ├── index.tsx
│   │   └── routeTree.gen.ts
│   ├── client/
│   │   ├── core/
│   │   │   └── OpenAPI.ts
│   │   ├── sdk.gen.ts
│   │   └── index.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── package.json
├── tsconfig.json
├── vite.config.ts
└── Dockerfile
```

## Key Components

### 1. Layout Components

#### Header
**File**: `src/components/Common/Header.tsx`

Main navigation header with user authentication status and navigation links.

#### Sidebar
**File**: `src/components/Common/Sidebar.tsx`

Navigation sidebar with menu items for different sections of the application.

#### SidebarItems
**File**: `src/components/Common/SidebarItems.tsx`

Defines the navigation menu structure and icons.

### 2. Page Components

#### Dashboard
**File**: `src/routes/_layout/index.tsx`

Main dashboard showing travel statistics, quick actions, and recent trips.

#### Trips List
**File**: `src/routes/_layout/trips.tsx`

Displays a list of user's trips with filtering and search capabilities.

#### Trip Details
**File**: `src/routes/_layout/trips.$tripId.tsx`

Detailed view of a specific trip including itineraries, bookings, and collaborators.

#### Plan Trip
**File**: `src/routes/_layout/plan-trip.tsx`

AI-powered trip planning interface with form inputs and real-time suggestions.

#### AI Chat
**File**: `src/routes/_layout/chat.tsx`

Chat interface for interacting with the AI travel assistant.

## API Integration

### OpenAPI Client
**File**: `src/client/core/OpenAPI.ts`

Configured to use the backend API with proper base URL and authentication.

### Generated SDK
**File**: `src/client/sdk.gen.ts`

Auto-generated TypeScript client for the FastAPI backend.

### API Services
**File**: `src/client/index.ts`

Convenience functions for common API operations:

```typescript
// Travel services
export const { getTrips, getTrip, createTrip, updateTrip, deleteTrip } = TravelService;

// AI travel services
export const { planTrip, chat, getSuggestions, optimizeItinerary } = AiTravelService;
```

## Routing

### TanStack Router Configuration

The application uses TanStack Router for type-safe routing:

```typescript
// Route structure
/ (index)
├── _layout/
│   ├── index (dashboard)
│   ├── trips
│   ├── trips/$tripId
│   ├── plan-trip
│   └── chat
```

### Route Parameters

- `$tripId`: Dynamic trip ID parameter for trip detail pages

## State Management

### Local State
- React hooks (`useState`, `useEffect`) for component state
- Form state management with controlled components
- Loading states and error handling

### API State
- Axios for HTTP requests
- Error handling with try-catch blocks
- Loading indicators during API calls

## Styling

### Chakra UI v3 Compatibility

Due to Chakra UI v3 compatibility issues, the application uses simplified styling:

- Basic HTML elements with minimal styling
- Inline styles for layout and spacing
- Responsive design with CSS Grid and Flexbox
- Custom CSS classes for consistent styling

### Responsive Design

- Mobile-first approach
- Flexible layouts that adapt to different screen sizes
- Touch-friendly interface elements

## Development

### Prerequisites

- Node.js 18+
- npm or yarn package manager

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development Server

The development server runs on `http://localhost:5173` with:
- Hot module replacement (HMR)
- TypeScript compilation
- ESLint integration
- Source maps for debugging

## Building and Deployment

### Production Build

```bash
# Create production build
npm run build

# Output directory: dist/
```

### Docker Build

```dockerfile
# Multi-stage build
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Testing

### Test Structure

```
src/
├── __tests__/
│   ├── components/
│   │   ├── Header.test.tsx
│   │   └── Sidebar.test.tsx
│   ├── pages/
│   │   ├── Dashboard.test.tsx
│   │   └── Trips.test.tsx
│   └── utils/
│       └── api.test.ts
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## Performance Optimization

### Code Splitting

- Route-based code splitting with TanStack Router
- Lazy loading of components
- Dynamic imports for heavy components

### Bundle Optimization

- Vite's built-in optimizations
- Tree shaking for unused code
- Asset optimization and compression

### Caching

- API response caching
- Static asset caching
- Service worker for offline functionality

## Accessibility

### WCAG Compliance

- Semantic HTML elements
- Proper ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- Color contrast compliance

### Best Practices

```typescript
// Accessible button component
<button
  aria-label="Plan new trip"
  role="button"
  tabIndex={0}
  onClick={handlePlanTrip}
>
  Plan Trip
</button>

// Accessible form inputs
<input
  type="text"
  aria-label="Trip destination"
  placeholder="Enter destination"
  required
/>
```

## Error Handling

### API Error Handling

```typescript
try {
  const response = await api.getTrips();
  setTrips(response.data);
} catch (error) {
  if (error.response?.status === 401) {
    // Handle authentication error
    redirectToLogin();
  } else {
    // Handle other errors
    setError('Failed to load trips');
  }
}
```

### User Feedback

- Loading states during API calls
- Error messages for failed operations
- Success notifications for completed actions
- Form validation with inline error messages

## Browser Support

### Supported Browsers

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Polyfills

- Automatic polyfill injection by Vite
- Modern JavaScript features
- CSS Grid and Flexbox support

## Security

### XSS Prevention

- React's built-in XSS protection
- Proper input sanitization
- Safe HTML rendering

### CSRF Protection

- CSRF tokens in API requests
- SameSite cookie attributes
- Origin validation

### Content Security Policy

```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline'; 
               style-src 'self' 'unsafe-inline';">
```

## Troubleshooting

### Common Issues

1. **Chakra UI v3 Compatibility**: Use simplified HTML elements instead
2. **TypeScript Errors**: Ensure proper type definitions
3. **API Connection Issues**: Check backend server status
4. **Build Failures**: Clear node_modules and reinstall

### Debug Tools

- React Developer Tools
- Browser DevTools
- Vite DevTools
- Network tab for API debugging

## Contributing

### Code Style

- ESLint configuration for consistent code style
- Prettier for code formatting
- TypeScript strict mode enabled
- Component naming conventions

### Git Workflow

1. Create feature branch
2. Make changes with proper commits
3. Write tests for new functionality
4. Submit pull request
5. Code review and merge

### Component Guidelines

- Use functional components with hooks
- Implement proper TypeScript types
- Add PropTypes or TypeScript interfaces
- Write comprehensive tests
- Document component props and usage
