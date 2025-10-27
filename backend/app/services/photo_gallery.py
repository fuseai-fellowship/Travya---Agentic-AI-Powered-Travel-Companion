"""
Photo Gallery Service
Handles fetching photos from Unsplash and Pexels APIs for travel itineraries
"""

import os
import aiohttp
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class PhotoSource:
    """Represents a photo source with metadata"""
    url: str
    thumbnail_url: str
    photographer_name: str
    photographer_url: str
    source: str  # 'unsplash' or 'pexels'
    width: int
    height: int
    description: Optional[str] = None

@dataclass
class PlacePhoto:
    """Represents a place with its photos"""
    name: str
    type: str  # 'city', 'landmark', 'natural_spot'
    caption: str
    search_query: str
    photos: List[PhotoSource]

class PhotoGalleryService:
    """Service for fetching photos from multiple sources"""
    
    def __init__(self):
        self.unsplash_access_key = os.getenv('UNSPLASH_ACCESS_KEY')
        self.unsplash_secret_key = os.getenv('UNSPLASH_SECRET_KEY')
        self.pexels_api_key = os.getenv('PEXELS_API_KEY')
        
        if not self.unsplash_access_key:
            logger.warning("Unsplash API key not found")
        if not self.pexels_api_key:
            logger.warning("Pexels API key not found")
    
    async def fetch_photos_for_places(self, places: List[Dict[str, str]], max_photos_per_place: int = 6) -> List[PlacePhoto]:
        """
        Fetch photos for a list of places
        
        Args:
            places: List of place dictionaries with 'name', 'type', 'caption', 'search_query'
            max_photos_per_place: Maximum number of photos to fetch per place
            
        Returns:
            List of PlacePhoto objects with fetched photos
        """
        place_photos = []
        
        for place in places:
            try:
                photos = await self._fetch_photos_for_place(
                    place['search_query'], 
                    max_photos_per_place
                )
                
                place_photo = PlacePhoto(
                    name=place['name'],
                    type=place['type'],
                    caption=place['caption'],
                    search_query=place['search_query'],
                    photos=photos
                )
                place_photos.append(place_photo)
                
            except Exception as e:
                logger.error(f"Error fetching photos for {place['name']}: {e}")
                # Add empty photo list for failed places
                place_photos.append(PlacePhoto(
                    name=place['name'],
                    type=place['type'],
                    caption=place['caption'],
                    search_query=place['search_query'],
                    photos=[]
                ))
        
        return place_photos
    
    async def _fetch_photos_for_place(self, search_query: str, max_photos: int = 6) -> List[PhotoSource]:
        """Fetch photos for a single place from multiple sources"""
        photos = []
        
        # Try Unsplash first, then Pexels as fallback
        if self.unsplash_access_key:
            try:
                unsplash_photos = await self._fetch_from_unsplash(search_query, max_photos)
                photos.extend(unsplash_photos)
            except Exception as e:
                logger.error(f"Unsplash API error: {e}")
        
        # If we don't have enough photos, try Pexels
        if len(photos) < max_photos and self.pexels_api_key:
            try:
                remaining = max_photos - len(photos)
                pexels_photos = await self._fetch_from_pexels(search_query, remaining)
                photos.extend(pexels_photos)
            except Exception as e:
                logger.error(f"Pexels API error: {e}")
        
        return photos[:max_photos]
    
    async def _fetch_from_unsplash(self, query: str, per_page: int = 6) -> List[PhotoSource]:
        """Fetch photos from Unsplash API"""
        url = "https://api.unsplash.com/search/photos"
        headers = {
            "Authorization": f"Client-ID {self.unsplash_access_key}",
            "Accept-Version": "v1"
        }
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": "landscape"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Unsplash API error: {response.status}")
                
                data = await response.json()
                photos = []
                
                for item in data.get('results', []):
                    photo = PhotoSource(
                        url=item['urls']['regular'],
                        thumbnail_url=item['urls']['thumb'],
                        photographer_name=item['user']['name'],
                        photographer_url=item['user']['links']['html'],
                        source='unsplash',
                        width=item['width'],
                        height=item['height'],
                        description=item.get('description')
                    )
                    photos.append(photo)
                
                return photos
    
    async def _fetch_from_pexels(self, query: str, per_page: int = 6) -> List[PhotoSource]:
        """Fetch photos from Pexels API"""
        url = "https://api.pexels.com/v1/search"
        headers = {
            "Authorization": self.pexels_api_key
        }
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": "landscape"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Pexels API error: {response.status}")
                
                data = await response.json()
                photos = []
                
                for item in data.get('photos', []):
                    photo = PhotoSource(
                        url=item['src']['large'],
                        thumbnail_url=item['src']['medium'],
                        photographer_name=item['photographer'],
                        photographer_url=item['photographer_url'],
                        source='pexels',
                        width=item['width'],
                        height=item['height'],
                        description=item.get('alt')
                    )
                    photos.append(photo)
                
                return photos
    
    async def download_photo(self, photo_url: str, photographer_name: str) -> None:
        """
        Trigger download event for Unsplash photos (required for production)
        This should be called when a user views/downloads a photo
        """
        if not self.unsplash_access_key:
            return
        
        # For Unsplash, we need to track downloads for production access
        download_url = f"https://api.unsplash.com/photos/{photo_url.split('/')[-1]}/download"
        headers = {
            "Authorization": f"Client-ID {self.unsplash_access_key}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"Download tracked for photo by {photographer_name}")
        except Exception as e:
            logger.error(f"Error tracking download: {e}")

# Global service instance
photo_gallery_service = PhotoGalleryService()
