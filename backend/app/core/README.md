# Core Module

This module contains the core functionality and configuration for the Travya travel companion system. It provides essential services, database connections, security features, and configuration management.

## Components

### Configuration (`config.py`)
Central configuration management using Pydantic settings:

- **Database Configuration**: PostgreSQL connection settings
- **Security Settings**: JWT tokens, CORS, authentication
- **External Services**: API keys and service endpoints
- **Environment Settings**: Development, staging, production configurations
- **Email Configuration**: SMTP settings for notifications

Key configuration options:
```python
# Database
POSTGRES_SERVER: str
POSTGRES_PORT: int = 5432
POSTGRES_USER: str
POSTGRES_PASSWORD: str
POSTGRES_DB: str

# Security
SECRET_KEY: str
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
BACKEND_CORS_ORIGINS: list[str]

# External Services
OPENAI_API_KEY: str | None = None
GOOGLE_AI_API_KEY: str | None = None
AMADEUS_API_KEY: str | None = None
```

### Database (`db.py`)
Database connection and session management:

- **SQLAlchemy Integration**: ORM setup and configuration
- **Session Management**: Database session handling
- **Connection Pooling**: Efficient database connections
- **Migration Support**: Alembic integration

Key features:
```python
# Database session dependency
def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

# Database initialization
def init_db(session: Session) -> None:
    # Create initial data and superuser
    pass
```

### Security (`security.py`)
Authentication and security utilities:

- **Password Hashing**: Secure password storage using bcrypt
- **JWT Tokens**: Token generation and validation
- **OAuth2**: Password-based authentication flow
- **User Authentication**: Login and session management

Key security functions:
```python
# Password hashing
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Password verification
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT token creation
def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    # Create JWT access token
    pass
```

### LLM Integration (`llm.py`)
Large Language Model integration and configuration:

- **Model Configuration**: AI model settings and parameters
- **API Integration**: External AI service connections
- **Prompt Management**: Template and prompt handling
- **Response Processing**: AI response parsing and validation

## Usage

### Configuration Access
```python
from app.core.config import settings

# Access configuration values
database_url = settings.SQLALCHEMY_DATABASE_URI
secret_key = settings.SECRET_KEY
cors_origins = settings.all_cors_origins
```

### Database Operations
```python
from app.core.db import get_db
from sqlalchemy.orm import Session

def some_endpoint(session: Session = Depends(get_db)):
    # Use database session
    users = session.query(User).all()
    return users
```

### Security Functions
```python
from app.core.security import get_password_hash, verify_password, create_access_token

# Hash password
hashed_password = get_password_hash("user_password")

# Verify password
is_valid = verify_password("user_password", hashed_password)

# Create access token
token = create_access_token(subject="user@example.com")
```

## Environment Variables

The core module reads configuration from environment variables:

```bash
# Database
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=travya
POSTGRES_PASSWORD=changethis
POSTGRES_DB=travya

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# External Services
OPENAI_API_KEY=your-openai-key
GOOGLE_AI_API_KEY=your-google-ai-key
AMADEUS_API_KEY=your-amadeus-key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Dependencies

### Core Dependencies
- **Pydantic**: Settings management and validation
- **SQLAlchemy**: Database ORM
- **Passlib**: Password hashing
- **Python-JOSE**: JWT token handling
- **Bcrypt**: Password hashing algorithm

### External Services
- **PostgreSQL**: Primary database
- **Redis**: Caching and session storage
- **External APIs**: AI services, travel APIs, payment processors

## Testing

The core module includes comprehensive testing:

- Configuration validation tests
- Database connection tests
- Security function tests
- Integration tests with external services

## Security Considerations

- All passwords are hashed using bcrypt
- JWT tokens are signed and validated
- CORS is properly configured
- Environment variables are validated
- Sensitive data is never logged

## Error Handling

The core module provides robust error handling:

- Configuration validation errors
- Database connection failures
- Authentication failures
- External service timeouts
