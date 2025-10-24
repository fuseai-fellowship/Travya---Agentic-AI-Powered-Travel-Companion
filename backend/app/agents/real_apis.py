"""
Real API Integrations for Travya Agents

This module provides production-ready integrations with external APIs:
- Google Places API for location data
- Amadeus API for flight search and booking
- Stripe API for payment processing
- Weather API for real-time weather data
- Hotel booking APIs
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from app.core.config import settings

@dataclass
class Place:
    """Represents a place from Google Places API"""
    name: str
    place_id: str
    rating: float
    price_level: Optional[int]
    types: List[str]
    location: Dict[str, float]
    address: str
    phone_number: Optional[str] = None
    website: Optional[str] = None
    photos: List[str] = None

@dataclass
class Flight:
    """Represents a flight from Amadeus API"""
    id: str
    price: float
    currency: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    airline: str
    flight_number: str
    duration: str
    stops: int

@dataclass
class Hotel:
    """Represents a hotel from booking API"""
    id: str
    name: str
    rating: float
    price_per_night: float
    currency: str
    location: Dict[str, float]
    address: str
    amenities: List[str]
    photos: List[str]
    availability: bool

class GooglePlacesAPI:
    """Real Google Places API integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_places(self, 
                           query: str, 
                           location: Optional[Dict[str, float]] = None,
                           radius: int = 50000,
                           place_type: str = "tourist_attraction") -> List[Place]:
        """Search for places using Google Places API"""
        if not self.session:
            raise RuntimeError("API client not initialized. Use async context manager.")
        
        try:
            # Text search
            url = f"{self.base_url}/textsearch/json"
            params = {
                "query": query,
                "key": self.api_key,
                "type": place_type
            }
            
            if location:
                params["location"] = f"{location['lat']},{location['lng']}"
                params["radius"] = radius
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_places(data.get("results", []))
                else:
                    print(f"Google Places API error: {response.status}")
                    return []
        
        except Exception as e:
            print(f"Error calling Google Places API: {e}")
            return []
    
    async def get_place_details(self, place_id: str) -> Optional[Place]:
        """Get detailed information about a specific place"""
        if not self.session:
            raise RuntimeError("API client not initialized. Use async context manager.")
        
        try:
            url = f"{self.base_url}/details/json"
            params = {
                "place_id": place_id,
                "key": self.api_key,
                "fields": "name,rating,price_level,types,geometry,formatted_address,formatted_phone_number,website,photos"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get("result")
                    if result:
                        return self._parse_place_detail(result)
                return None
        
        except Exception as e:
            print(f"Error getting place details: {e}")
            return None
    
    def _parse_places(self, results: List[Dict]) -> List[Place]:
        """Parse places from API response"""
        places = []
        for item in results:
            try:
                place = Place(
                    name=item.get("name", ""),
                    place_id=item.get("place_id", ""),
                    rating=item.get("rating", 0.0),
                    price_level=item.get("price_level"),
                    types=item.get("types", []),
                    location=item.get("geometry", {}).get("location", {}),
                    address=item.get("formatted_address", ""),
                    photos=[photo.get("photo_reference", "") for photo in item.get("photos", [])]
                )
                places.append(place)
            except Exception as e:
                print(f"Error parsing place: {e}")
                continue
        
        return places
    
    def _parse_place_detail(self, result: Dict) -> Place:
        """Parse detailed place information"""
        return Place(
            name=result.get("name", ""),
            place_id=result.get("place_id", ""),
            rating=result.get("rating", 0.0),
            price_level=result.get("price_level"),
            types=result.get("types", []),
            location=result.get("geometry", {}).get("location", {}),
            address=result.get("formatted_address", ""),
            phone_number=result.get("formatted_phone_number"),
            website=result.get("website"),
            photos=[photo.get("photo_reference", "") for photo in result.get("photos", [])]
        )

class AmadeusAPI:
    """Real Amadeus API integration for flights"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://test.api.amadeus.com"
        self.access_token = None
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self._authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _authenticate(self):
        """Authenticate with Amadeus API"""
        if not self.session:
            raise RuntimeError("API client not initialized. Use async context manager.")
        
        try:
            url = f"{self.base_url}/v1/security/oauth2/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result.get("access_token")
                else:
                    print(f"Amadeus authentication failed: {response.status}")
        
        except Exception as e:
            print(f"Error authenticating with Amadeus: {e}")
    
    async def search_flights(self, 
                           origin: str, 
                           destination: str, 
                           departure_date: str,
                           return_date: Optional[str] = None,
                           adults: int = 1,
                           children: int = 0,
                           infants: int = 0) -> List[Flight]:
        """Search for flights using Amadeus API"""
        if not self.session or not self.access_token:
            raise RuntimeError("API client not authenticated. Use async context manager.")
        
        try:
            url = f"{self.base_url}/v2/shopping/flight-offers"
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": adults,
                "children": children,
                "infants": infants
            }
            
            if return_date:
                params["returnDate"] = return_date
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_flights(data.get("data", []))
                else:
                    print(f"Amadeus flight search error: {response.status}")
                    return []
        
        except Exception as e:
            print(f"Error searching flights: {e}")
            return []
    
    def _parse_flights(self, data: List[Dict]) -> List[Flight]:
        """Parse flights from API response"""
        flights = []
        for item in data:
            try:
                # Extract price information
                price_data = item.get("price", {})
                price = float(price_data.get("total", 0))
                currency = price_data.get("currency", "USD")
                
                # Extract itinerary information
                itineraries = item.get("itineraries", [])
                if itineraries:
                    itinerary = itineraries[0]
                    segments = itinerary.get("segments", [])
                    if segments:
                        first_segment = segments[0]
                        last_segment = segments[-1]
                        
                        flight = Flight(
                            id=item.get("id", ""),
                            price=price,
                            currency=currency,
                            origin=first_segment.get("departure", {}).get("iataCode", ""),
                            destination=last_segment.get("arrival", {}).get("iataCode", ""),
                            departure_time=datetime.fromisoformat(
                                first_segment.get("departure", {}).get("at", "").replace("Z", "+00:00")
                            ),
                            arrival_time=datetime.fromisoformat(
                                last_segment.get("arrival", {}).get("at", "").replace("Z", "+00:00")
                            ),
                            airline=first_segment.get("carrierCode", ""),
                            flight_number=first_segment.get("number", ""),
                            duration=itinerary.get("duration", ""),
                            stops=len(segments) - 1
                        )
                        flights.append(flight)
            
            except Exception as e:
                print(f"Error parsing flight: {e}")
                continue
        
        return flights

class StripeAPI:
    """Real Stripe API integration for payments"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.base_url = "https://api.stripe.com/v1"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_payment_intent(self, 
                                  amount: float, 
                                  currency: str = "usd",
                                  description: str = "",
                                  metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a payment intent using Stripe API"""
        if not self.session:
            raise RuntimeError("API client not initialized. Use async context manager.")
        
        try:
            url = f"{self.base_url}/payment_intents"
            data = {
                "amount": int(amount * 100),  # Convert to cents
                "currency": currency,
                "description": description
            }
            
            if metadata:
                data["metadata"] = metadata
            
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            async with self.session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    raise Exception(f"Stripe API error: {error_data.get('error', {}).get('message', 'Unknown error')}")
        
        except Exception as e:
            print(f"Error creating payment intent: {e}")
            raise
    
    async def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm a payment intent"""
        if not self.session:
            raise RuntimeError("API client not initialized. Use async context manager.")
        
        try:
            url = f"{self.base_url}/payment_intents/{payment_intent_id}/confirm"
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            async with self.session.post(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    raise Exception(f"Stripe API error: {error_data.get('error', {}).get('message', 'Unknown error')}")
        
        except Exception as e:
            print(f"Error confirming payment: {e}")
            raise

class WeatherAPI:
    """Real weather API integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_current_weather(self, city: str, country_code: str = "") -> Dict[str, Any]:
        """Get current weather for a city"""
        if not self.session:
            raise RuntimeError("API client not initialized. Use async context manager.")
        
        try:
            location = f"{city},{country_code}" if country_code else city
            url = f"{self.base_url}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Weather API error: {response.status}")
                    return {}
        
        except Exception as e:
            print(f"Error getting weather: {e}")
            return {}
    
    async def get_forecast(self, city: str, country_code: str = "", days: int = 5) -> Dict[str, Any]:
        """Get weather forecast for a city"""
        if not self.session:
            raise RuntimeError("API client not initialized. Use async context manager.")
        
        try:
            location = f"{city},{country_code}" if country_code else city
            url = f"{self.base_url}/forecast"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",
                "cnt": days * 8  # 8 forecasts per day (every 3 hours)
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Weather forecast API error: {response.status}")
                    return {}
        
        except Exception as e:
            print(f"Error getting weather forecast: {e}")
            return {}

# Global API instances
google_places = GooglePlacesAPI(settings.GOOGLE_MAPS_API_KEY) if hasattr(settings, 'GOOGLE_MAPS_API_KEY') else None
amadeus = AmadeusAPI(settings.AMADEUS_CLIENT_ID, settings.AMADEUS_CLIENT_SECRET) if hasattr(settings, 'AMADEUS_CLIENT_ID') else None
stripe_api = StripeAPI(settings.STRIPE_SECRET_KEY) if hasattr(settings, 'STRIPE_SECRET_KEY') else None
weather_api = WeatherAPI(settings.WEATHER_API_KEY) if hasattr(settings, 'WEATHER_API_KEY') else None
