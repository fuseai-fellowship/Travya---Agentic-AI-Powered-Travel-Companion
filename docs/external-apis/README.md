# External APIs Documentation

## Overview

The Travya application integrates with multiple external APIs to provide comprehensive travel services including maps, flight search, hotel booking, payment processing, and weather information.

## API Integrations

### 1. Google Maps API
**Purpose**: Location services, places search, and geocoding

#### Configuration
```python
# Environment variables
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

#### Services
- **Places API**: Search for attractions, restaurants, hotels
- **Geocoding API**: Convert addresses to coordinates
- **Directions API**: Get travel routes and directions
- **Distance Matrix API**: Calculate travel times and distances

#### Implementation
**File**: `backend/app/agents/tools.py`

```python
from googlemaps import Client as GoogleMapsClient

# Initialize client
gmaps = GoogleMapsClient(key=settings.GOOGLE_MAPS_API_KEY)

def places_api(tool_context: ToolContext, location: str, query: str) -> list:
    """Search for places using Google Places API."""
    try:
        places_result = gmaps.places_nearby(
            location=location,
            radius=5000,
            keyword=query
        )
        return places_result.get('results', [])
    except Exception as e:
        logger.error(f"Google Places API error: {e}")
        return []
```

#### Rate Limits
- **Places API**: 1,000 requests per day (free tier)
- **Geocoding API**: 2,500 requests per day (free tier)
- **Directions API**: 2,500 requests per day (free tier)

### 2. Amadeus API
**Purpose**: Flight and hotel search and booking

#### Configuration
```python
# Environment variables
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
```

#### Services
- **Flight Offers API**: Search for flights
- **Hotel Offers API**: Search for hotels
- **Airport API**: Get airport information
- **City Search API**: Search for cities

#### Implementation
**File**: `backend/app/agents/tools.py`

```python
from amadeus import Client as AmadeusClient

# Initialize client
amadeus = AmadeusClient(
    client_id=settings.AMADEUS_CLIENT_ID,
    client_secret=settings.AMADEUS_CLIENT_SECRET
)

def amadeus_flight_search(
    tool_context: ToolContext,
    origin: str,
    destination: str,
    date: str
) -> list:
    """Search for flights using Amadeus API."""
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=date,
            adults=1
        )
        return response.data
    except Exception as e:
        logger.error(f"Amadeus API error: {e}")
        return []
```

#### Rate Limits
- **Free Tier**: 2,000 requests per month
- **Paid Tier**: Based on subscription plan

### 3. Stripe API
**Purpose**: Payment processing for bookings

#### Configuration
```python
# Environment variables
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
```

#### Services
- **Payment Intents**: Process payments
- **Customers**: Manage customer information
- **Subscriptions**: Handle recurring payments
- **Webhooks**: Handle payment events

#### Implementation
**File**: `backend/app/agents/tools.py`

```python
import stripe

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def stripe_payment(
    tool_context: ToolContext,
    amount: float,
    description: str
) -> dict:
    """Process payment using Stripe API."""
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency='usd',
            description=description
        )
        return {
            "payment_id": payment_intent.id,
            "status": payment_intent.status,
            "client_secret": payment_intent.client_secret
        }
    except Exception as e:
        logger.error(f"Stripe API error: {e}")
        return {"error": str(e)}
```

#### Security
- Use HTTPS for all requests
- Store API keys securely
- Implement webhook signature verification
- Use idempotency keys for retries

### 4. Weather API
**Purpose**: Weather forecasts and conditions

#### Configuration
```python
# Environment variables
WEATHER_API_KEY=your_weather_api_key
WEATHER_API_URL=https://api.openweathermap.org/data/2.5
```

#### Services
- **Current Weather**: Get current conditions
- **Forecast**: Get 5-day weather forecast
- **Historical Data**: Get past weather data
- **Alerts**: Get weather warnings

#### Implementation
**File**: `backend/app/agents/tools.py`

```python
import httpx

async def weather_api(
    tool_context: ToolContext,
    location: str,
    date: str
) -> dict:
    """Get weather information for a location."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.WEATHER_API_URL}/weather",
                params={
                    "q": location,
                    "appid": settings.WEATHER_API_KEY,
                    "units": "metric"
                }
            )
            data = response.json()
            return {
                "location": data["name"],
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"]
            }
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return {"error": str(e)}
```

## API Service Layer

### Service Architecture
**File**: `backend/app/services/external_apis.py`

```python
class TravelAPIService:
    """Orchestrates all external API services."""
    
    def __init__(self):
        self.google_maps = GoogleMapsService()
        self.amadeus = AmadeusService()
        self.weather = WeatherService()
    
    async def search_destination(self, query: str) -> dict:
        """Search for destinations using multiple APIs."""
        # Use Google Maps for places
        places = await self.google_maps.search_places(query)
        
        # Get weather for each place
        weather_data = {}
        for place in places:
            weather = await self.weather.get_weather(place["name"])
            weather_data[place["name"]] = weather
        
        return {
            "places": places,
            "weather": weather_data
        }
```

### Error Handling

#### Retry Logic
```python
import asyncio
from functools import wraps

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry API calls on failure."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=3, delay=1.0)
async def call_external_api(url: str, params: dict) -> dict:
    """Call external API with retry logic."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
```

#### Circuit Breaker
```python
class CircuitBreaker:
    """Circuit breaker pattern for API calls."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self.failure_count = 0
            self.state = "CLOSED"
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e
```

## Rate Limiting

### Implementation
```python
import asyncio
from collections import defaultdict
import time

class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    async def acquire(self, key: str):
        """Acquire permission to make API call."""
        now = time.time()
        # Remove old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < self.time_window
        ]
        
        if len(self.requests[key]) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[key][0])
            await asyncio.sleep(sleep_time)
        
        self.requests[key].append(now)

# Usage
rate_limiter = RateLimiter(max_requests=100, time_window=60)  # 100 requests per minute

async def make_api_call():
    await rate_limiter.acquire("google_maps")
    # Make API call
```

## Caching

### Redis Caching
```python
import redis
import json
from typing import Optional, Any

class APICache:
    """Cache for API responses."""
    
    def __init__(self, redis_client: redis.Redis, ttl: int = 3600):
        self.redis = redis_client
        self.ttl = ttl
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached response."""
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    async def set(self, key: str, value: Any) -> None:
        """Cache response."""
        self.redis.setex(key, self.ttl, json.dumps(value))
    
    async def get_or_set(self, key: str, func, *args, **kwargs) -> Any:
        """Get from cache or set if not exists."""
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        result = await func(*args, **kwargs)
        await self.set(key, result)
        return result

# Usage
cache = APICache(redis_client, ttl=3600)

async def get_weather_cached(location: str):
    key = f"weather:{location}"
    return await cache.get_or_set(key, weather_api, location)
```

## Monitoring and Logging

### API Monitoring
```python
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

def monitor_api_calls(api_name: str):
    """Decorator to monitor API calls."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{api_name} API call successful in {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{api_name} API call failed after {duration:.2f}s: {e}")
                raise
        return wrapper
    return decorator

@monitor_api_calls("Google Maps")
async def search_places(location: str, query: str):
    # API call implementation
    pass
```

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
api_calls_total = Counter('api_calls_total', 'Total API calls', ['api', 'status'])
api_duration = Histogram('api_duration_seconds', 'API call duration', ['api'])
api_rate_limit = Gauge('api_rate_limit_remaining', 'API rate limit remaining', ['api'])

def track_api_metrics(api_name: str):
    """Track API metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with api_duration.labels(api=api_name).time():
                try:
                    result = await func(*args, **kwargs)
                    api_calls_total.labels(api=api_name, status='success').inc()
                    return result
                except Exception as e:
                    api_calls_total.labels(api=api_name, status='error').inc()
                    raise
        return wrapper
    return decorator
```

## Testing

### Mock Services
```python
from unittest.mock import AsyncMock, patch

class MockGoogleMapsService:
    """Mock Google Maps service for testing."""
    
    async def search_places(self, location: str, query: str) -> list:
        return [
            {
                "name": f"Mock {query} in {location}",
                "rating": 4.5,
                "place_id": "mock_place_id"
            }
        ]

class MockAmadeusService:
    """Mock Amadeus service for testing."""
    
    async def search_flights(self, origin: str, destination: str, date: str) -> list:
        return [
            {
                "id": "mock_flight_id",
                "price": {"total": "500.00"},
                "itineraries": []
            }
        ]

# Test usage
@patch('app.services.external_apis.GoogleMapsService', MockGoogleMapsService)
async def test_search_destination():
    service = TravelAPIService()
    result = await service.search_destination("Paris")
    assert "places" in result
    assert len(result["places"]) > 0
```

### Integration Tests
```python
import pytest
import httpx

@pytest.mark.asyncio
async def test_google_maps_integration():
    """Test Google Maps API integration."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={
                "query": "restaurants in Paris",
                "key": settings.GOOGLE_MAPS_API_KEY
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
```

## Security

### API Key Management
```python
import os
from cryptography.fernet import Fernet

class APIKeyManager:
    """Secure API key management."""
    
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
    
    def encrypt_key(self, api_key: str) -> bytes:
        """Encrypt API key."""
        return self.cipher.encrypt(api_key.encode())
    
    def decrypt_key(self, encrypted_key: bytes) -> str:
        """Decrypt API key."""
        return self.cipher.decrypt(encrypted_key).decode()
    
    def get_api_key(self, service: str) -> str:
        """Get decrypted API key for service."""
        encrypted_key = os.getenv(f"{service.upper()}_API_KEY_ENCRYPTED")
        if encrypted_key:
            return self.decrypt_key(encrypted_key.encode())
        return os.getenv(f"{service.upper()}_API_KEY")
```

### Request Signing
```python
import hmac
import hashlib
import time

def sign_request(api_key: str, timestamp: str, body: str) -> str:
    """Sign API request for authentication."""
    message = f"{timestamp}{body}"
    signature = hmac.new(
        api_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature
```

## Error Handling

### API Error Types
```python
class APIError(Exception):
    """Base API error."""
    pass

class RateLimitError(APIError):
    """Rate limit exceeded."""
    pass

class AuthenticationError(APIError):
    """Authentication failed."""
    pass

class ServiceUnavailableError(APIError):
    """Service temporarily unavailable."""
    pass

def handle_api_error(response: httpx.Response) -> None:
    """Handle API response errors."""
    if response.status_code == 429:
        raise RateLimitError("Rate limit exceeded")
    elif response.status_code == 401:
        raise AuthenticationError("Authentication failed")
    elif response.status_code >= 500:
        raise ServiceUnavailableError("Service unavailable")
    elif response.status_code >= 400:
        raise APIError(f"API error: {response.status_code}")
```

## Configuration

### Environment Variables
```bash
# Google Maps
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Amadeus
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret

# Stripe
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key

# Weather
WEATHER_API_KEY=your_weather_api_key
WEATHER_API_URL=https://api.openweathermap.org/data/2.5

# Rate Limiting
GOOGLE_MAPS_RATE_LIMIT=1000
AMADEUS_RATE_LIMIT=2000
STRIPE_RATE_LIMIT=100

# Caching
API_CACHE_TTL=3600
REDIS_URL=redis://localhost:6379/0
```

### Configuration Class
```python
from pydantic_settings import BaseSettings

class ExternalAPISettings(BaseSettings):
    # Google Maps
    google_maps_api_key: str
    google_maps_rate_limit: int = 1000
    
    # Amadeus
    amadeus_client_id: str
    amadeus_client_secret: str
    amadeus_rate_limit: int = 2000
    
    # Stripe
    stripe_secret_key: str
    stripe_publishable_key: str
    stripe_rate_limit: int = 100
    
    # Weather
    weather_api_key: str
    weather_api_url: str = "https://api.openweathermap.org/data/2.5"
    
    # Caching
    api_cache_ttl: int = 3600
    redis_url: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```
