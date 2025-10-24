# Services Module

This module contains service layer components that handle business logic, external API integrations, and data processing for the Travya travel companion system.

## Components

### Document Storage (`document_storage.py`)
Handles file upload, storage, and retrieval operations:

- **File Upload**: Secure file upload with validation
- **Storage Management**: Local and cloud storage options
- **File Processing**: Document parsing and content extraction
- **Media Handling**: Image and document processing for travel content

Key features:
```python
# File upload handling
async def upload_document(file: UploadFile, user_id: str) -> str:
    # Validate file type and size
    # Store file securely
    # Return file URL or ID
    pass

# Document processing
async def process_document(file_path: str) -> dict:
    # Extract text content
    # Parse structured data
    # Return processed information
    pass
```

### External APIs (`external_apis.py`)
Integration with external travel and AI services:

- **Travel APIs**: Amadeus, Google Maps, weather services
- **AI Services**: OpenAI, Google AI, other LLM providers
- **Payment Processing**: Stripe, PayPal integration
- **Notification Services**: Email, SMS, push notifications

Key integrations:
```python
# Amadeus flight search
async def search_flights(origin: str, destination: str, date: str) -> list:
    # Call Amadeus API
    # Process flight data
    # Return formatted results
    pass

# Google Maps integration
async def get_place_details(place_id: str) -> dict:
    # Call Google Maps API
    # Extract place information
    # Return structured data
    pass

# OpenAI integration
async def generate_travel_suggestions(prompt: str) -> str:
    # Call OpenAI API
    # Process response
    # Return generated content
    pass
```

## Service Architecture

### Service Layer Pattern
The services module follows the service layer pattern to separate business logic from API controllers:

```
API Layer (routes) -> Service Layer (services) -> Data Layer (models/crud)
```

### Dependency Injection
Services are injected into API endpoints using FastAPI's dependency injection:

```python
from app.services.external_apis import ExternalAPIService
from app.services.document_storage import DocumentStorageService

# Service dependencies
async def get_external_api_service() -> ExternalAPIService:
    return ExternalAPIService()

async def get_document_storage_service() -> DocumentStorageService:
    return DocumentStorageService()
```

## External API Integrations

### Travel Services
- **Amadeus API**: Flight and hotel booking
- **Google Maps API**: Places, directions, and geocoding
- **Weather API**: Current and forecast weather data
- **Currency API**: Real-time exchange rates

### AI Services
- **OpenAI API**: GPT models for natural language processing
- **Google AI**: Gemini models for multimodal processing
- **Vector Databases**: Semantic search and RAG functionality

### Payment Services
- **Stripe**: Payment processing and subscription management
- **PayPal**: Alternative payment processing
- **Banking APIs**: Direct bank integration options

## Configuration

Services are configured through environment variables:

```bash
# External API Keys
AMADEUS_API_KEY=your-amadeus-key
AMADEUS_API_SECRET=your-amadeus-secret
GOOGLE_MAPS_API_KEY=your-google-maps-key
OPENAI_API_KEY=your-openai-key
STRIPE_SECRET_KEY=your-stripe-secret

# Service Configuration
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=image/jpeg,image/png,application/pdf
STORAGE_BACKEND=local  # or 's3', 'gcs'
```

## Error Handling

Services include comprehensive error handling:

- **API Rate Limiting**: Handle external API rate limits
- **Timeout Handling**: Graceful handling of service timeouts
- **Retry Logic**: Automatic retry for transient failures
- **Fallback Services**: Alternative services when primary fails

```python
async def call_external_api_with_retry(api_call, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await api_call()
        except TimeoutError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

## Caching

Services implement caching for improved performance:

- **Redis Caching**: Cache external API responses
- **TTL Management**: Appropriate cache expiration times
- **Cache Invalidation**: Smart cache invalidation strategies

```python
async def get_cached_place_details(place_id: str) -> dict:
    cache_key = f"place_details:{place_id}"
    cached_data = await redis.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    
    # Fetch from API and cache
    data = await google_maps.get_place_details(place_id)
    await redis.setex(cache_key, 3600, json.dumps(data))
    return data
```

## Testing

Services include comprehensive testing:

- **Unit Tests**: Individual service function testing
- **Integration Tests**: External API integration testing
- **Mock Testing**: External service mocking for reliable tests
- **Performance Tests**: Load and stress testing

## Monitoring

Services include monitoring and observability:

- **Metrics Collection**: Service performance metrics
- **Logging**: Comprehensive logging for debugging
- **Health Checks**: Service availability monitoring
- **Alerting**: Automated alerting for service failures

## Security

Security considerations for services:

- **API Key Management**: Secure storage and rotation of API keys
- **Input Validation**: Comprehensive input validation and sanitization
- **Rate Limiting**: Protection against abuse and overuse
- **Data Encryption**: Encryption of sensitive data in transit and at rest
