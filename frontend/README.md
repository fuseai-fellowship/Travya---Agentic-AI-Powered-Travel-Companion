# Frontend Module - Component Flow

This document describes how React components and routes work together in the Travya frontend.

## Frontend Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Main Entry Point                    │
│                   main.tsx                            │
│  • QueryClient setup                                │
│  • Router initialization                            │
│  • Provider wrapping                                │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│               Router System                         │
│            TanStack Router                          │
│  • Route matching                                  │
│  • Preloading                                      │
│  • Context injection                               │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│               Route Components                      │
│  • _layout.tsx (Main Layout)                       │
│  • login.tsx, signup.tsx (Auth)                    │
│  • _layout/index.tsx (Dashboard)                   │
│  • _layout/plan-trip.tsx (Trip Planning)           │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│             Business Components                     │
│  • MapParserComponent.tsx                          │
│  • PhotoGallery.tsx                                │
│  • AddItem.tsx, EditItem.tsx                       │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              UI Components                       │
│  • Navbar.tsx, Sidebar.tsx                        │
│  • Buttons, Inputs, Modals                        │
└─────────────────────────────────────────────────────┘
```

## Code Flow: Trip Planning Feature

### Complete User Journey

**1. User Navigates to Plan Trip Page**

```typescript
// frontend/src/routes/_layout/plan-trip.tsx
export const Route = createFileRoute("/_layout/plan-trip")({
  component: PlanTripPage,
})

function PlanTripPage() {
  // 2. Component mounts, fetches data
  const { data: trips } = useQuery({
    queryKey: ["trips"],
    queryFn: () => TravelService.readTrips({ skip: 0, limit: 100 })
  })
  
  // 3. Initialize form state
  const [formData, setFormData] = useState({
    destination: "",
    startDate: "",
    endDate: "",
    budget: 0,
    tripType: "leisure",
    interests: []
  })
  
  // 4. Handle form submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    
    // 5. Create trip plan via API
    const response = await TravelService.planTrip({
      destination: formData.destination,
      start_date: formData.startDate,
      end_date: formData.endDate,
      budget: formData.budget,
      trip_type: formData.tripType,
      interests: formData.interests
    })
    
    // 6. Navigate to trip details
    router.navigate({ 
      to: "/trips/$tripId", 
      params: { tripId: response.trip_id } 
    })
  }
  
  return (
    <div className="plan-trip-page">
      <form onSubmit={handleSubmit}>
        {/* Form fields */}
        <button type="submit">Plan Trip</button>
      </form>
    </div>
  )
}
```

**2. API Client Generation** (`frontend/src/client/sdk.gen.ts`)

```typescript
// Auto-generated from OpenAPI schema
export class TravelService {
  static async planTrip(requestBody: TripPlanningRequest): Promise<TripPlanningResponse> {
    return await fetch(`${OpenAPI.BASE}/api/v1/ai-travel/plan-trip`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(requestBody)
    }).then(response => response.json())
  }
}
```

**3. Authentication Flow**

```typescript
// frontend/src/contexts/AuthContext.tsx
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null)
  
  // Check auth on mount
  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (token) {
      // Fetch current user
      UsersService.readUserMe().then(setUser)
    }
  }, [])
  
  const login = async (email: string, password: string) => {
    // 1. Call login endpoint
    const response = await LoginService.loginAccessToken({
      username: email,
      password: password
    })
    
    // 2. Store token
    localStorage.setItem("access_token", response.access_token)
    
    // 3. Fetch user data
    const user = await UsersService.readUserMe()
    setUser(user)
  }
  
  const logout = () => {
    localStorage.removeItem("access_token")
    setUser(null)
    router.navigate({ to: "/login" })
  }
  
  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
```

## Component Patterns

### 1. Travel Notes (Items)

**Component Hierarchy:**
```
items.tsx (Main Page)
  └─ NoteCard.tsx (Individual Note)
       ├─ EditItem.tsx (Modal)
       └─ DeleteItem.tsx (Modal with confirmation)
```

**Code Flow:**

```typescript
// items.tsx
function Items() {
  // 1. Fetch notes from API
  const { data, isLoading } = useQuery({
    queryFn: () => ItemsService.readItems({ skip: 0, limit: 100 }),
    queryKey: ["items"]
  })
  
  // 2. Render notes in grid
  return (
    <div className="notes-grid">
      {data?.data.map(item => (
        <NoteCard key={item.id} item={item} />
      ))}
    </div>
  )
}

// NoteCard.tsx
function NoteCard({ item }: { item: ItemPublic }) {
  const [isHovered, setIsHovered] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  
  return (
    <div 
      className="note-card"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <h3>{item.title}</h3>
      <p>{item.description}</p>
      
      {isHovered && (
        <div className="note-actions">
          <button onClick={() => setIsEditing(true)}>Edit</button>
          <DeleteItem id={item.id} />
        </div>
      )}
      
      {isEditing && (
        <EditItem item={item} onClose={() => setIsEditing(false)} />
      )}
    </div>
  )
}
```

### 2. AI Chat Interface

**Component Flow:**

```typescript
// chat.tsx
function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const { user } = useAuth()
  
  const sendMessage = async () => {
    if (!input.trim()) return
    
    // 1. Add user message to UI
    const userMsg: Message = {
      sender: "user",
      message: input,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMsg])
    
    // 2. Send to backend
    const response = await ConversationsService.sendMessage({
      message: input,
      conversation_id: conversationId
    })
    
    // 3. Add AI response to UI
    const aiMsg: Message = {
      sender: "assistant",
      message: response.message,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, aiMsg])
    
    // 4. Clear input
    setInput("")
  }
  
  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <ChatMessage key={idx} message={msg} />
        ))}
      </div>
      
      <form onSubmit={sendMessage}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your trip..."
        />
      </form>
    </div>
  )
}
```

### 3. Map Parser Integration

```typescript
// MapParserComponent.tsx
function MapParserComponent() {
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [locations, setLocations] = useState<Location[]>([])
  
  const handleUpload = async (e: FormEvent) => {
    e.preventDefault()
    if (!imageFile) return
    
    // 1. Create FormData
    const formData = new FormData()
    formData.append("file", imageFile)
    
    // 2. Upload to backend
    const response = await fetch("/api/v1/map-parser/parse", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${localStorage.getItem("access_token")}`
      },
      body: formData
    })
    
    const data = await response.json()
    setLocations(data.locations)
  }
  
  return (
    <div>
      <form onSubmit={handleUpload}>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setImageFile(e.target.files?.[0] || null)}
        />
        <button type="submit">Parse Map</button>
      </form>
      
      {locations.length > 0 && (
        <GoogleMap locations={locations} />
      )}
    </div>
  )
}
```

## State Management

### TanStack Query for Server State

```typescript
// Configure in main.tsx
const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => {
      if (error instanceof ApiError && [401, 403].includes(error.status)) {
        localStorage.removeItem("access_token")
        window.location.href = "/login"
      }
    }
  })
})

// Usage in components
function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["trips"],
    queryFn: () => TravelService.readTrips()
  })
  
  const { mutate } = useMutation({
    mutationFn: (trip: TripCreate) => TravelService.createTrip(trip),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips"] })
    }
  })
  
  return <div>...</div>
}
```

### React Context for Global State

```typescript
// AuthContext for user authentication
// TravelContext for travel data
// SidebarContext for UI state
```

## Styling System

### Global Styles

```css
/* globals.css */
:root {
  --primary-color: #007aff;
  --bg-primary: #000000;
  --bg-secondary: #1c1c1e;
  --text-primary: #ffffff;
}

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
```

### Component Styles

```typescript
// Inline styles for component-specific styling
<style>{`
  .note-card {
    background: var(--note-color);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  }
`}</style>
```

## Type Safety

```typescript
// Auto-generated types from OpenAPI schema
import type { TripPublic, TripCreate } from "@/client"

// Usage
const trip: TripPublic = await TravelService.readTrip({ tripId })
const newTrip: TripCreate = {
  destination: "Paris",
  start_date: "2024-06-01",
  // ...
}
```

## Testing

```typescript
// Component test with Playwright
import { test, expect } from '@playwright/test'

test('user can create trip', async ({ page }) => {
  await page.goto('/plan-trip')
  await page.fill('[name="destination"]', 'Paris')
  await page.fill('[name="start_date"]', '2024-06-01')
  await page.click('button[type="submit"]')
  
  await expect(page.locator('.success-message')).toBeVisible()
})
```

## Build & Deployment

```bash
# Development
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Docker build
docker-compose build frontend
```
