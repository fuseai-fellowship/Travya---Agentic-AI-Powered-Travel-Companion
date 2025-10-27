"""
RAG Image Retrieval Service for Travel Chat

This service provides RAG-based image retrieval from photo galleries for the chat system.
It can search and retrieve relevant images from user's trip photo galleries based on natural language queries.
"""

import os
import uuid
import aiohttp
import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json
from dataclasses import dataclass
from sqlmodel import select, Session
from app.core.config import settings
from app.models import PhotoGallery, GalleryPlace, GalleryPhoto, Trip
import logging

logger = logging.getLogger(__name__)

@dataclass
class ChatImage:
    """Represents an image retrieved for chat display"""
    id: str
    url: str
    thumbnail_url: str
    title: str
    description: Optional[str] = None
    place_name: str = ""
    place_type: str = ""
    photographer_name: Optional[str] = None
    photographer_url: Optional[str] = None
    source: str = "gallery"
    width: Optional[int] = None
    height: Optional[int] = None
    relevance_score: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "title": self.title,
            "description": self.description,
            "place_name": self.place_name,
            "place_type": self.place_type,
            "photographer_name": self.photographer_name,
            "photographer_url": self.photographer_url,
            "source": self.source,
            "width": self.width,
            "height": self.height,
            "relevance_score": self.relevance_score
        }

class RAGImageRetrievalService:
    """Service for RAG-based image retrieval from photo galleries"""
    
    def __init__(self):
        self.session = None
        
        # Keywords for image-related queries
        self.image_keywords = [
            "show", "display", "see", "view", "image", "photo", "picture", "gallery",
            "photos", "pictures", "images", "visual", "visuals", "sight", "sights"
        ]
        
        # Keywords for trip-related queries
        self.trip_keywords = [
            "trip", "travel", "journey", "adventure", "vacation", "holiday", "tour",
            "destination", "place", "location", "visit", "explore", "discover"
        ]
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def is_image_query(self, query: str) -> bool:
        """Check if the query is asking for images"""
        query_lower = query.lower()
        
        # Check for image-related keywords
        has_image_keywords = any(keyword in query_lower for keyword in self.image_keywords)
        
        # Check for trip-related keywords
        has_trip_keywords = any(keyword in query_lower for keyword in self.trip_keywords)
        
        return has_image_keywords and has_trip_keywords
    
    async def retrieve_images_for_chat(
        self, 
        query: str, 
        user_id: str, 
        session: Session,
        limit: int = 6
    ) -> Tuple[str, List[ChatImage]]:
        """
        Retrieve relevant images for a chat query
        
        Returns:
            Tuple of (response_text, list_of_images)
        """
        try:
            if not self.is_image_query(query):
                return "I can help you find images from your trips! Try asking something like 'show me images of my trip to Annapurna Circuit' or 'display photos from my travel'", []
            
            # Extract trip information from query
            trip_info = self._extract_trip_info(query)
            
            # Find relevant trips
            trips = await self._find_relevant_trips(trip_info, user_id, session)
            
            if not trips:
                return "I couldn't find any trips matching your request. Make sure you have photo galleries for your trips!", []
            
            # Retrieve images from photo galleries
            images = await self._retrieve_gallery_images(trips, query, session, limit)
            
            if not images:
                return "I found your trips but couldn't locate any photo galleries. Try generating photo galleries for your trips first!", []
            
            # Generate response text
            response_text = self._generate_response_text(trips, images, query)
            
            return response_text, images
            
        except Exception as e:
            logger.error(f"Error retrieving images for chat: {e}")
            return "Sorry, I encountered an error while retrieving your images. Please try again.", []
    
    def _extract_trip_info(self, query: str) -> dict:
        """Extract trip information from the query"""
        query_lower = query.lower()
        
        # Common trip destinations and keywords
        trip_patterns = {
            "annapurna": ["annapurna", "circuit", "trek", "himalayas", "nepal"],
            "pokhara": ["pokhara", "lakeside", "phewa"],
            "kathmandu": ["kathmandu", "valley", "temples"],
            "ghandruk": ["ghandruk", "village", "gurung"],
            "mountains": ["mountain", "peak", "summit", "range", "hills"],
            "lakes": ["lake", "water", "pond", "river"],
            "cities": ["city", "town", "urban", "downtown"],
            "nature": ["nature", "natural", "outdoor", "landscape", "scenic"]
        }
        
        extracted_info = {
            "destinations": [],
            "activities": [],
            "types": []
        }
        
        for category, keywords in trip_patterns.items():
            for keyword in keywords:
                if keyword in query_lower:
                    if category in ["annapurna", "pokhara", "kathmandu", "ghandruk"]:
                        extracted_info["destinations"].append(category)
                    elif category in ["mountains", "lakes", "cities", "nature"]:
                        extracted_info["types"].append(category)
        
        return extracted_info
    
    async def _find_relevant_trips(self, trip_info: dict, user_id: str, session: Session) -> List[Trip]:
        """Find trips relevant to the query"""
        try:
            # Base query for user's trips
            query = select(Trip).where(Trip.owner_id == user_id)
            
            # If specific destinations are mentioned, filter by destination
            if trip_info["destinations"]:
                destination_filters = []
                for dest in trip_info["destinations"]:
                    destination_filters.append(Trip.destination.ilike(f"%{dest}%"))
                
                if destination_filters:
                    from sqlmodel import or_
                    query = query.where(or_(*destination_filters))
            
            trips = session.exec(query).all()
            
            # If no specific trips found, return all user trips
            if not trips:
                trips = session.exec(select(Trip).where(Trip.owner_id == user_id)).all()
            
            return trips[:5]  # Limit to 5 most recent trips
            
        except Exception as e:
            logger.error(f"Error finding relevant trips: {e}")
            return []
    
    async def _retrieve_gallery_images(
        self, 
        trips: List[Trip], 
        query: str, 
        session: Session, 
        limit: int
    ) -> List[ChatImage]:
        """Retrieve images from photo galleries"""
        try:
            all_images = []
            
            for trip in trips:
                # Get photo gallery for this trip
                gallery = session.exec(
                    select(PhotoGallery).where(PhotoGallery.trip_id == trip.id)
                ).first()
                
                if not gallery:
                    continue
                
                # Get places and photos
                places = session.exec(
                    select(GalleryPlace).where(GalleryPlace.gallery_id == gallery.id)
                ).all()
                
                for place in places:
                    # Get photos for this place
                    photos = session.exec(
                        select(GalleryPhoto).where(GalleryPhoto.place_id == place.id)
                    ).all()
                    
                    for photo in photos:
                        # Calculate relevance score
                        relevance_score = self._calculate_relevance_score(
                            query, place, photo
                        )
                        
                        chat_image = ChatImage(
                            id=str(photo.id),
                            url=photo.url,
                            thumbnail_url=photo.thumbnail_url,
                            title=f"{place.name} - {trip.destination}",
                            description=photo.description,
                            place_name=place.name,
                            place_type=place.place_type,
                            photographer_name=photo.photographer_name,
                            photographer_url=photo.photographer_url,
                            source="gallery",
                            width=photo.width,
                            height=photo.height,
                            relevance_score=relevance_score
                        )
                        
                        all_images.append(chat_image)
            
            # Sort by relevance score and limit results
            all_images.sort(key=lambda x: x.relevance_score, reverse=True)
            return all_images[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving gallery images: {e}")
            return []
    
    def _calculate_relevance_score(self, query: str, place: GalleryPlace, photo: GalleryPhoto) -> float:
        """Calculate relevance score for an image based on the query"""
        query_lower = query.lower()
        score = 0.0
        
        # Check place name relevance
        place_name_lower = place.name.lower()
        if any(word in place_name_lower for word in query_lower.split()):
            score += 0.5
        
        # Check place type relevance
        place_type_lower = place.place_type.lower()
        if any(word in place_type_lower for word in query_lower.split()):
            score += 0.3
        
        # Check photo description relevance
        if photo.description:
            desc_lower = photo.description.lower()
            if any(word in desc_lower for word in query_lower.split()):
                score += 0.2
        
        # Boost score for specific keywords
        if "annapurna" in query_lower and "annapurna" in place_name_lower:
            score += 0.4
        if "pokhara" in query_lower and "pokhara" in place_name_lower:
            score += 0.4
        if "ghandruk" in query_lower and "ghandruk" in place_name_lower:
            score += 0.4
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _generate_response_text(self, trips: List[Trip], images: List[ChatImage], query: str) -> str:
        """Generate a natural response text for the images"""
        if not images:
            return "I couldn't find any images matching your request."
        
        trip_names = [trip.destination for trip in trips[:2]]  # Limit to 2 trip names
        place_names = list(set([img.place_name for img in images[:3]]))  # Limit to 3 place names
        
        if len(trip_names) == 1:
            trip_text = f"your trip to {trip_names[0]}"
        else:
            trip_text = "your trips"
        
        if len(place_names) == 1:
            place_text = f"from {place_names[0]}"
        elif len(place_names) == 2:
            place_text = f"from {place_names[0]} and {place_names[1]}"
        else:
            place_text = f"from {', '.join(place_names[:-1])}, and {place_names[-1]}"
        
        return f"Here are some beautiful images from {trip_text} {place_text}. I found {len(images)} photos that match your request!"
    
    async def get_trip_images_summary(self, trip_id: str, session: Session) -> dict:
        """Get a summary of images available for a trip"""
        try:
            gallery = session.exec(
                select(PhotoGallery).where(PhotoGallery.trip_id == trip_id)
            ).first()
            
            if not gallery:
                return {"total_images": 0, "places": [], "message": "No photo gallery found for this trip"}
            
            places = session.exec(
                select(GalleryPlace).where(GalleryPlace.gallery_id == gallery.id)
            ).all()
            
            place_summaries = []
            total_images = 0
            
            for place in places:
                photo_count = session.exec(
                    select(GalleryPhoto).where(GalleryPhoto.place_id == place.id)
                ).all()
                
                place_summaries.append({
                    "name": place.name,
                    "type": place.place_type,
                    "photo_count": len(photo_count)
                })
                total_images += len(photo_count)
            
            return {
                "total_images": total_images,
                "places": place_summaries,
                "message": f"Found {total_images} images across {len(places)} places"
            }
            
        except Exception as e:
            logger.error(f"Error getting trip images summary: {e}")
            return {"total_images": 0, "places": [], "message": "Error retrieving image summary"}

# Global service instance
rag_image_service = RAGImageRetrievalService()
