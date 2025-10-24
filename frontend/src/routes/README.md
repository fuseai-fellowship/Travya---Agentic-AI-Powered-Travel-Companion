# Frontend Routes

This module contains all the route definitions and page components for the Travya travel companion frontend application. Routes are organized using TanStack Router for type-safe routing.

## Route Architecture

The application uses TanStack Router for file-based routing with the following structure:

- **Root Route**: Main application layout and providers
- **Layout Routes**: Shared layouts for different sections
- **Page Routes**: Individual page components
- **Dynamic Routes**: Routes with parameters and dynamic segments

## Route Structure

### Root Route (`__root.tsx`)
Main application root that provides:
- Global providers (Auth, Travel, Query Client)
- Error boundaries
- Global layout components
- Route context setup

### Layout Routes (`_layout/`)
Shared layouts for different application sections:

#### Main Layout (`_layout.tsx`)
Primary application layout with:
- Navigation sidebar
- Header with user menu
- Main content area
- Footer

#### Admin Layout (`_layout/admin.tsx`)
Administrative interface layout with:
- Admin navigation
- User management tools
- System administration features

#### Chat Layout (`_layout/chat.tsx`)
AI chat interface layout with:
- Chat interface
- Message history
- Agent activity feed

### Page Routes

#### Authentication Pages
- **Login** (`login.tsx`): User authentication
- **Signup** (`signup.tsx`): User registration
- **Password Recovery** (`recover-password.tsx`): Password reset request
- **Password Reset** (`reset-password.tsx`): Password reset form

#### Main Application Pages
- **Dashboard** (`_layout/index.tsx`): Main dashboard
- **Items** (`_layout/items.tsx`): Item management
- **Trips** (`_layout/trips.tsx`): Trip management
- **Itineraries** (`_layout/itineraries.tsx`): Itinerary display
- **Plan Trip** (`_layout/plan-trip.tsx`): Trip planning interface
- **Settings** (`_layout/settings.tsx`): User settings

#### Dynamic Routes
- **Trip Details** (`_layout/trips.$tripId.tsx`): Individual trip details
- **Test Page** (`test.tsx`): Development testing page

## Route Configuration

### Route Definitions
Routes are defined using TanStack Router's file-based routing:

```typescript
// Route structure
/                           // Dashboard
/login                      // Login page
/signup                     // Signup page
/items                      // Items management
/trips                      // Trips list
/trips/$tripId              // Trip details
/itineraries                // Itineraries
/plan-trip                  // Trip planning
/settings                   // User settings
/admin                      // Admin interface
/chat                       // AI chat
```

### Route Parameters
Dynamic routes use parameters:

```typescript
// Trip details route
/trips/$tripId

// Access parameter in component
const { tripId } = useParams({ from: '/trips/$tripId' });
```

### Route Guards
Authentication and authorization are handled through route guards:

```typescript
// Protected route example
const protectedRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/dashboard',
  beforeLoad: async ({ context }) => {
    if (!context.user) {
      throw redirect({ to: '/login' });
    }
  },
  component: Dashboard,
});
```

## Page Components

### Dashboard (`_layout/index.tsx`)
Main application dashboard featuring:
- Recent trips overview
- Quick actions
- AI agent status
- Travel recommendations

### Trip Management (`_layout/trips.tsx`)
Trip listing and management with:
- Trip list with filtering
- Search and sort functionality
- Trip creation and editing
- Trip status management

### Trip Details (`_layout/trips.$tripId.tsx`)
Individual trip details including:
- Trip information display
- Itinerary breakdown
- Booking details
- Real-time updates

### Plan Trip (`_layout/plan-trip.tsx`)
AI-powered trip planning interface:
- Multi-step planning wizard
- AI agent integration
- Real-time suggestions
- Interactive itinerary builder

### Itineraries (`_layout/itineraries.tsx`)
Itinerary display and management:
- Day-by-day itinerary view
- Interactive maps
- Activity details
- Booking integration

### Settings (`_layout/settings.tsx`)
User account and application settings:
- Profile information
- Password management
- Preferences
- Account management

## Route Context

### Authentication Context
Routes have access to authentication context:

```typescript
interface RouteContext {
  user: User | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}
```

### Travel Context
Travel-related state and actions:

```typescript
interface TravelContext {
  currentTrip: Trip | null;
  itineraries: Itinerary[];
  bookTrip: (trip: Trip) => Promise<void>;
  updateItinerary: (itinerary: Itinerary) => Promise<void>;
}
```

## Navigation

### Programmatic Navigation
Routes support programmatic navigation:

```typescript
import { useNavigate } from '@tanstack/react-router';

function MyComponent() {
  const navigate = useNavigate();
  
  const handleClick = () => {
    navigate({ to: '/trips/$tripId', params: { tripId: '123' } });
  };
}
```

### Link Components
Navigation links with type safety:

```typescript
import { Link } from '@tanstack/react-router';

<Link to="/trips/$tripId" params={{ tripId: '123' }}>
  View Trip
</Link>
```

## Route Loading

### Data Loading
Routes support data loading patterns:

```typescript
const tripRoute = createRoute({
  path: '/trips/$tripId',
  loader: async ({ params }) => {
    const trip = await fetchTrip(params.tripId);
    return { trip };
  },
  component: TripDetails,
});
```

### Loading States
Routes handle loading states:

```typescript
function TripDetails() {
  const { trip, isLoading } = useLoaderData({ from: '/trips/$tripId' });
  
  if (isLoading) return <Skeleton />;
  return <div>{trip.name}</div>;
}
```

## Error Handling

### Route Error Boundaries
Routes include error handling:

```typescript
const errorRoute = createRoute({
  path: '/error',
  component: ErrorPage,
});

// Error boundary in root route
<ErrorBoundary fallback={ErrorPage}>
  <Router />
</ErrorBoundary>
```

### 404 Handling
Not found routes are handled:

```typescript
const notFoundRoute = createRoute({
  path: '*',
  component: NotFound,
});
```

## SEO and Meta

### Route Meta
Routes can define meta information:

```typescript
const tripRoute = createRoute({
  path: '/trips/$tripId',
  meta: () => [
    { title: 'Trip Details' },
    { name: 'description', content: 'View trip details' },
  ],
  component: TripDetails,
});
```

## Testing

Routes include comprehensive testing:

- **Route Testing**: Route configuration and navigation
- **Component Testing**: Page component functionality
- **Integration Testing**: Full route workflows
- **E2E Testing**: End-to-end user journeys

## Performance

Routes are optimized for performance:

- **Code Splitting**: Automatic route-based code splitting
- **Lazy Loading**: Dynamic imports for route components
- **Preloading**: Route preloading for better UX
- **Caching**: Route data caching and invalidation
