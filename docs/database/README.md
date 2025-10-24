# Database Documentation

## Overview

The database layer uses PostgreSQL with SQLModel ORM for type-safe database operations. The schema is designed to support a comprehensive travel planning and management system with user authentication, trip planning, collaboration, and AI-powered features.

## Technology Stack

- **PostgreSQL 17**: Primary database
- **SQLModel**: Python ORM with Pydantic integration
- **Alembic**: Database migration management
- **Redis**: Caching and session storage

## Database Schema

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Trips Table
```sql
CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    budget DECIMAL(10,2),
    description TEXT,
    status VARCHAR(20) DEFAULT 'planned',
    trip_type VARCHAR(20) DEFAULT 'leisure',
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Itineraries Table
```sql
CREATE TABLE itineraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID REFERENCES trips(id) ON DELETE CASCADE,
    day INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    activities TEXT[],
    start_time TIME,
    end_time TIME,
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Bookings Table
```sql
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID REFERENCES trips(id) ON DELETE CASCADE,
    booking_type VARCHAR(50) NOT NULL,
    provider VARCHAR(255) NOT NULL,
    confirmation_number VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    booking_date DATE NOT NULL,
    travel_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Trip Collaborators Table
```sql
CREATE TABLE trip_collaborators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID REFERENCES trips(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    inviter_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'viewer',
    status VARCHAR(20) DEFAULT 'pending',
    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP
);
```

#### Conversations Table
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID REFERENCES trips(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Conversation Messages Table
```sql
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',
    sender_type VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Data Models

### User Model
**File**: `backend/app/models.py`

```python
class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    trips: List["Trip"] = Relationship(back_populates="user")
    conversations: List["Conversation"] = Relationship(back_populates="user")
```

### Trip Model
**File**: `backend/app/models.py`

```python
class Trip(SQLModel, table=True):
    __tablename__ = "trips"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    title: str
    destination: str
    start_date: date
    end_date: date
    budget: Optional[float] = None
    description: Optional[str] = None
    status: TripStatus = Field(default=TripStatus.PLANNED)
    trip_type: TripType = Field(default=TripType.LEISURE)
    user_id: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: User = Relationship(back_populates="trips")
    itineraries: List["Itinerary"] = Relationship(back_populates="trip")
    bookings: List["Booking"] = Relationship(back_populates="trip")
    collaborators: List["TripCollaborator"] = Relationship(back_populates="trip")
    conversations: List["Conversation"] = Relationship(back_populates="trip")
```

### Enums
**File**: `backend/app/models.py`

```python
class TripStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TripType(str, Enum):
    LEISURE = "leisure"
    BUSINESS = "business"
    ADVENTURE = "adventure"
    FAMILY = "family"
    SOLO = "solo"

class BookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
```

## Database Operations

### CRUD Operations

#### Create Operations
```python
# Create a new trip
trip = Trip(
    title="Paris Adventure",
    destination="Paris, France",
    start_date=date(2024, 8, 15),
    end_date=date(2024, 8, 20),
    budget=2500.0,
    user_id=user.id
)
session.add(trip)
session.commit()
```

#### Read Operations
```python
# Get user's trips
trips = session.exec(
    select(Trip).where(Trip.user_id == user_id)
).all()

# Get trip with relationships
trip = session.exec(
    select(Trip)
    .where(Trip.id == trip_id)
    .options(selectinload(Trip.itineraries))
    .options(selectinload(Trip.bookings))
).first()
```

#### Update Operations
```python
# Update trip
trip.title = "Updated Paris Adventure"
trip.budget = 3000.0
session.add(trip)
session.commit()
```

#### Delete Operations
```python
# Delete trip (cascades to related records)
session.delete(trip)
session.commit()
```

### Complex Queries

#### Trip Search with Filters
```python
def search_trips(
    session: Session,
    user_id: UUID,
    destination: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[TripStatus] = None
) -> List[Trip]:
    query = select(Trip).where(Trip.user_id == user_id)
    
    if destination:
        query = query.where(Trip.destination.ilike(f"%{destination}%"))
    if start_date:
        query = query.where(Trip.start_date >= start_date)
    if end_date:
        query = query.where(Trip.end_date <= end_date)
    if status:
        query = query.where(Trip.status == status)
    
    return session.exec(query).all()
```

#### Trip Statistics
```python
def get_trip_statistics(session: Session, user_id: UUID) -> Dict:
    # Total trips
    total_trips = session.exec(
        select(func.count(Trip.id)).where(Trip.user_id == user_id)
    ).first()
    
    # Total budget
    total_budget = session.exec(
        select(func.sum(Trip.budget)).where(Trip.user_id == user_id)
    ).first()
    
    # Trips by status
    trips_by_status = session.exec(
        select(Trip.status, func.count(Trip.id))
        .where(Trip.user_id == user_id)
        .group_by(Trip.status)
    ).all()
    
    return {
        "total_trips": total_trips,
        "total_budget": total_budget,
        "trips_by_status": dict(trips_by_status)
    }
```

## Migrations

### Alembic Configuration
**File**: `backend/alembic.ini`

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://user:password@localhost/travya
```

### Creating Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show migration history
alembic history
```

### Migration Files
**Directory**: `backend/alembic/versions/`

Example migration:
```python
"""Add travel models

Revision ID: abc123
Revises: def456
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None

def upgrade():
    # Create trips table
    op.create_table('trips',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('destination', sa.String(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('budget', sa.DECIMAL(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('trip_type', sa.String(), nullable=True),
        sa.Column('user_id', postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('trips')
```

## Indexing Strategy

### Primary Indexes
- Primary keys (automatic)
- Foreign keys (automatic)
- Unique constraints (automatic)

### Custom Indexes
```sql
-- User email index
CREATE INDEX idx_users_email ON users(email);

-- Trip user_id index
CREATE INDEX idx_trips_user_id ON trips(user_id);

-- Trip destination index
CREATE INDEX idx_trips_destination ON trips(destination);

-- Trip dates index
CREATE INDEX idx_trips_dates ON trips(start_date, end_date);

-- Booking trip_id index
CREATE INDEX idx_bookings_trip_id ON bookings(trip_id);

-- Conversation trip_id index
CREATE INDEX idx_conversations_trip_id ON conversations(trip_id);
```

### Composite Indexes
```sql
-- User trips by status and date
CREATE INDEX idx_trips_user_status_date ON trips(user_id, status, start_date);

-- Booking by type and date
CREATE INDEX idx_bookings_type_date ON bookings(booking_type, travel_date);
```

## Data Validation

### SQLModel Validation
```python
class TripCreate(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    destination: str = Field(min_length=1, max_length=255)
    start_date: date
    end_date: date
    budget: Optional[float] = Field(ge=0)
    description: Optional[str] = Field(max_length=1000)
    trip_type: TripType = TripType.LEISURE
    
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
```

### Database Constraints
```sql
-- Check constraints
ALTER TABLE trips ADD CONSTRAINT chk_trip_dates 
    CHECK (end_date > start_date);

ALTER TABLE trips ADD CONSTRAINT chk_trip_budget 
    CHECK (budget IS NULL OR budget >= 0);

-- Foreign key constraints
ALTER TABLE trips ADD CONSTRAINT fk_trips_user 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

## Performance Optimization

### Query Optimization

#### Use Selectin Loading
```python
# Load related data efficiently
trip = session.exec(
    select(Trip)
    .where(Trip.id == trip_id)
    .options(
        selectinload(Trip.itineraries),
        selectinload(Trip.bookings),
        selectinload(Trip.collaborators)
    )
).first()
```

#### Pagination
```python
def get_trips_paginated(
    session: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 10
) -> List[Trip]:
    return session.exec(
        select(Trip)
        .where(Trip.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(Trip.created_at.desc())
    ).all()
```

### Connection Pooling
```python
# Database engine configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

## Backup and Recovery

### Database Backup
```bash
# Full backup
pg_dump -h localhost -U user -d travya > backup.sql

# Schema only
pg_dump -h localhost -U user -d travya --schema-only > schema.sql

# Data only
pg_dump -h localhost -U user -d travya --data-only > data.sql
```

### Database Restore
```bash
# Restore from backup
psql -h localhost -U user -d travya < backup.sql
```

## Monitoring

### Query Performance
```sql
-- Slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Connection Monitoring
```sql
-- Active connections
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE state = 'active';

-- Connection details
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    query
FROM pg_stat_activity
WHERE state = 'active';
```

## Security

### Data Encryption
- Passwords hashed with bcrypt
- Sensitive data encrypted at rest
- SSL/TLS for connections

### Access Control
```sql
-- Create application user
CREATE USER travya_app WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT CONNECT ON DATABASE travya TO travya_app;
GRANT USAGE ON SCHEMA public TO travya_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO travya_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO travya_app;
```

### Audit Logging
```sql
-- Enable audit logging
CREATE EXTENSION IF NOT EXISTS pgaudit;

-- Audit configuration
ALTER SYSTEM SET pgaudit.log = 'write, ddl';
ALTER SYSTEM SET pgaudit.log_relation = on;
SELECT pg_reload_conf();
```
