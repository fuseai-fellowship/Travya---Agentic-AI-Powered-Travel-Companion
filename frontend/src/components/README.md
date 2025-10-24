# Frontend Components

This module contains all React components for the Travya travel companion frontend application. Components are organized by functionality and follow a modular architecture.

## Component Architecture

The frontend uses a component-based architecture with the following structure:

- **UI Components**: Reusable UI elements and design system components
- **Feature Components**: Business logic components for specific features
- **Layout Components**: Page layout and navigation components
- **Admin Components**: Administrative interface components

## Component Categories

### UI Components (`ui/`)
Reusable design system components built with Chakra UI:

- **Button**: Custom button variants and styles
- **Input**: Form input components with validation
- **Dialog**: Modal and dialog components
- **Menu**: Navigation and action menus
- **Skeleton**: Loading state components
- **Toaster**: Notification and toast components

### Common Components (`Common/`)
Shared components used across the application:

- **Navbar**: Main navigation bar
- **Sidebar**: Application sidebar with navigation
- **UserMenu**: User account and settings menu
- **NotFound**: 404 error page component
- **ItemActionsMenu**: Context menu for items

### Feature Components

#### Admin Components (`Admin/`)
Administrative interface components:

- **AddUser**: User creation form
- **EditUser**: User editing interface
- **DeleteUser**: User deletion confirmation

#### Items Components (`Items/`)
Item management components:

- **AddItem**: Create new items
- **EditItem**: Edit existing items
- **DeleteItem**: Delete item confirmation

#### User Settings (`UserSettings/`)
User account management components:

- **UserInformation**: User profile information
- **ChangePassword**: Password change form
- **DeleteAccount**: Account deletion interface
- **Appearance**: Theme and appearance settings

#### Pending Components (`Pending/`)
Pending items and user management:

- **PendingItems**: Items awaiting approval
- **PendingUsers**: Users awaiting approval

### Specialized Components

#### AgentActivityFeed
Real-time activity feed for AI agent interactions and updates.

#### ItineraryDisplay
Comprehensive itinerary display with interactive features:
- Day-by-day itinerary breakdown
- Interactive maps and locations
- Booking integration
- Real-time updates

## Component Structure

### Base Component Pattern
All components follow a consistent structure:

```typescript
interface ComponentProps {
  // Component-specific props
}

export function ComponentName({ ...props }: ComponentProps) {
  // Component logic
  return (
    // JSX structure
  );
}
```

### Styling
Components use Chakra UI for styling with custom theme extensions:

```typescript
// Custom theme components
const theme = extendTheme({
  components: {
    Button: {
      variants: {
        // Custom button variants
      }
    }
  }
});
```

## State Management

### Context Providers
Components use React Context for state management:

- **AuthContext**: Authentication state and user information
- **TravelContext**: Travel planning and booking state

### Custom Hooks
Reusable logic is encapsulated in custom hooks:

- **useAuth**: Authentication and user management
- **useCustomToast**: Toast notification management

## Component Usage

### Basic Component Usage
```typescript
import { Button } from './ui/button';
import { Dialog } from './ui/dialog';

function MyComponent() {
  return (
    <Dialog>
      <Button variant="primary">
        Click me
      </Button>
    </Dialog>
  );
}
```

### Form Components
```typescript
import { Field } from './ui/field';
import { PasswordInput } from './ui/password-input';

function LoginForm() {
  return (
    <form>
      <Field label="Email">
        <Input type="email" />
      </Field>
      <Field label="Password">
        <PasswordInput />
      </Field>
    </form>
  );
}
```

## Props and Interfaces

### Common Props
Most components accept common props:

```typescript
interface BaseComponentProps {
  children?: React.ReactNode;
  className?: string;
  isDisabled?: boolean;
  isLoading?: boolean;
}
```

### Form Props
Form components include validation props:

```typescript
interface FormFieldProps {
  label: string;
  error?: string;
  isRequired?: boolean;
  helperText?: string;
}
```

## Styling Guidelines

### Chakra UI Integration
Components are built on Chakra UI with custom extensions:

- **Color Scheme**: Consistent color palette
- **Typography**: Standardized text styles
- **Spacing**: Consistent spacing scale
- **Responsive Design**: Mobile-first responsive design

### Custom Styling
Custom styles are defined in CSS files:

- **globals.css**: Global styles and CSS variables
- **components.css**: Component-specific styles

## Testing

Components include comprehensive testing:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Visual Tests**: Screenshot and visual regression testing
- **Accessibility Tests**: WCAG compliance testing

## Accessibility

All components follow accessibility best practices:

- **ARIA Labels**: Proper ARIA labeling
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Support**: Screen reader compatibility
- **Color Contrast**: WCAG AA color contrast compliance

## Performance

Components are optimized for performance:

- **Lazy Loading**: Dynamic imports for large components
- **Memoization**: React.memo for expensive components
- **Code Splitting**: Route-based code splitting
- **Bundle Optimization**: Tree shaking and dead code elimination

## Development Guidelines

### Component Creation
1. Create component file with TypeScript
2. Define props interface
3. Implement component logic
4. Add styling with Chakra UI
5. Write tests
6. Add documentation

### Naming Conventions
- Components: PascalCase (e.g., `UserProfile`)
- Props: camelCase (e.g., `isLoading`)
- Files: PascalCase for components (e.g., `UserProfile.tsx`)

### Import Organization
```typescript
// External libraries
import React from 'react';
import { Box, Button } from '@chakra-ui/react';

// Internal components
import { CustomComponent } from './CustomComponent';
import { useAuth } from '../hooks/useAuth';
```
