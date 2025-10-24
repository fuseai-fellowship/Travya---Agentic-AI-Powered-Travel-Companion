# Context Providers

This module contains React Context providers that manage global application state for the Travya travel companion frontend application.

## Context Architecture

The application uses React Context for state management with the following providers:

- **AuthContext**: Authentication and user management
- **TravelContext**: Travel planning and booking state
- **QueryClient**: TanStack Query for server state management

## Context Providers

### Authentication Context (`AuthContext.tsx`)
Manages user authentication state and operations:

#### State
```typescript
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
```

#### Actions
```typescript
interface AuthActions {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  register: (userData: RegisterData) => Promise<void>;
  updateProfile: (profileData: ProfileData) => Promise<void>;
  changePassword: (passwordData: PasswordData) => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
}
```

#### Usage
```typescript
import { useAuth } from '../contexts/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();
  
  if (!isAuthenticated) {
    return <LoginForm onLogin={login} />;
  }
  
  return <div>Welcome, {user?.name}!</div>;
}
```

### Travel Context (`TravelContext.tsx`)
Manages travel planning and booking state:

#### State
```typescript
interface TravelState {
  currentTrip: Trip | null;
  itineraries: Itinerary[];
  bookings: Booking[];
  preferences: TravelPreferences;
  isLoading: boolean;
  error: string | null;
}
```

#### Actions
```typescript
interface TravelActions {
  createTrip: (tripData: CreateTripData) => Promise<void>;
  updateTrip: (tripId: string, updates: TripUpdates) => Promise<void>;
  deleteTrip: (tripId: string) => Promise<void>;
  createItinerary: (itineraryData: CreateItineraryData) => Promise<void>;
  updateItinerary: (itineraryId: string, updates: ItineraryUpdates) => Promise<void>;
  bookTrip: (tripId: string) => Promise<void>;
  updatePreferences: (preferences: TravelPreferences) => Promise<void>;
}
```

#### Usage
```typescript
import { useTravel } from '../contexts/TravelContext';

function TripPlanner() {
  const { 
    currentTrip, 
    itineraries, 
    createTrip, 
    createItinerary 
  } = useTravel();
  
  const handleCreateTrip = async (tripData) => {
    await createTrip(tripData);
  };
  
  return (
    <div>
      {itineraries.map(itinerary => (
        <ItineraryCard key={itinerary.id} itinerary={itinerary} />
      ))}
    </div>
  );
}
```

## Context Implementation

### Provider Setup
Contexts are set up in the root component:

```typescript
// main.tsx
import { AuthProvider } from './contexts/AuthContext';
import { TravelProvider } from './contexts/TravelContext';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TravelProvider>
          <Router />
        </TravelProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
```

### Context Hooks
Custom hooks provide easy access to context:

```typescript
// AuthContext.tsx
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

// TravelContext.tsx
export function useTravel() {
  const context = useContext(TravelContext);
  if (!context) {
    throw new Error('useTravel must be used within TravelProvider');
  }
  return context;
}
```

## State Management Patterns

### Local State
Contexts manage local state using React hooks:

```typescript
const [user, setUser] = useState<User | null>(null);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

### Server State
Server state is managed with TanStack Query:

```typescript
const { data: trips, isLoading } = useQuery({
  queryKey: ['trips'],
  queryFn: fetchTrips,
});
```

### State Updates
State updates are handled through actions:

```typescript
const login = async (credentials: LoginCredentials) => {
  setIsLoading(true);
  setError(null);
  
  try {
    const user = await authService.login(credentials);
    setUser(user);
    setIsAuthenticated(true);
  } catch (error) {
    setError(error.message);
  } finally {
    setIsLoading(false);
  }
};
```

## Error Handling

### Context Error Boundaries
Contexts include error handling:

```typescript
const [error, setError] = useState<string | null>(null);

const handleError = (error: Error) => {
  setError(error.message);
  console.error('Context error:', error);
};
```

### Error Recovery
Contexts provide error recovery mechanisms:

```typescript
const clearError = () => setError(null);

const retry = async () => {
  setError(null);
  await performAction();
};
```

## Persistence

### Local Storage
Contexts can persist state to local storage:

```typescript
// Save to localStorage
useEffect(() => {
  if (user) {
    localStorage.setItem('user', JSON.stringify(user));
  }
}, [user]);

// Load from localStorage
useEffect(() => {
  const savedUser = localStorage.getItem('user');
  if (savedUser) {
    setUser(JSON.parse(savedUser));
  }
}, []);
```

### Session Storage
Temporary state can be stored in session storage:

```typescript
// Save to sessionStorage
useEffect(() => {
  if (currentTrip) {
    sessionStorage.setItem('currentTrip', JSON.stringify(currentTrip));
  }
}, [currentTrip]);
```

## Testing

Contexts include comprehensive testing:

- **Unit Tests**: Individual context functionality
- **Integration Tests**: Context interactions
- **Provider Tests**: Provider setup and configuration
- **Hook Tests**: Custom hook behavior

### Testing Setup
```typescript
// Test wrapper
function TestWrapper({ children }) {
  return (
    <AuthProvider>
      <TravelProvider>
        {children}
      </TravelProvider>
    </AuthProvider>
  );
}

// Test usage
render(<MyComponent />, { wrapper: TestWrapper });
```

## Performance

Contexts are optimized for performance:

- **Memoization**: React.memo for expensive components
- **Context Splitting**: Separate contexts for different concerns
- **Lazy Loading**: Dynamic context loading
- **State Optimization**: Minimal re-renders

### Context Optimization
```typescript
// Memoized context value
const contextValue = useMemo(() => ({
  user,
  isAuthenticated,
  login,
  logout,
}), [user, isAuthenticated]);
```

## Security

Contexts handle security considerations:

- **Token Management**: Secure token storage and refresh
- **Data Validation**: Input validation and sanitization
- **Error Handling**: Secure error messages
- **State Protection**: Protected state access

## Migration

Contexts support migration patterns:

- **Version Management**: Context version handling
- **Data Migration**: State migration between versions
- **Backward Compatibility**: Legacy state support
- **Upgrade Paths**: Smooth upgrade processes
