"""
Photo Gallery API Routes
Handles photo gallery generation and management for travel itineraries
"""

import uuid
from typing import Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Trip, PhotoGallery, PhotoGalleryCreate, PhotoGalleryPublic, PhotoGalleriesPublic,
    GalleryPlace, GalleryPlaceCreate, GalleryPlacesPublic,
    GalleryPhoto, GalleryPhotoCreate, GalleryPhotosPublic
)
from app.services.itinerary_parser import itinerary_parser_service
from app.services.photo_gallery import photo_gallery_service

router = APIRouter(prefix="/photo-gallery", tags=["photo-gallery"])


@router.post("/generate/{trip_id}", response_model=PhotoGalleryPublic)
async def generate_photo_gallery(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    trip_id: uuid.UUID,
    background_tasks: BackgroundTasks
) -> Any:
    """Generate a photo gallery for a trip's itinerary"""
    
    # Check if trip exists and user has access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this trip")
    
    # Check if gallery already exists
    existing_gallery = session.exec(
        select(PhotoGallery).where(PhotoGallery.trip_id == trip_id)
    ).first()
    
    if existing_gallery:
        raise HTTPException(status_code=400, detail="Photo gallery already exists for this trip")
    
    # Create initial gallery record
    gallery_data = PhotoGalleryCreate(
        trip_id=trip_id,
        title=f"Photo Gallery - {trip.title}",
        description=f"Automatically generated photo gallery for {trip.destination}",
        status="processing"
    )
    
    gallery = PhotoGallery.model_validate(gallery_data)
    session.add(gallery)
    session.commit()
    session.refresh(gallery)
    
    # Start background task to generate gallery
    background_tasks.add_task(
        _generate_gallery_background,
        session,
        gallery.id,
        trip.ai_itinerary_data or ""
    )
    
    return gallery


@router.get("/trip/{trip_id}", response_model=PhotoGalleriesPublic)
def get_trip_galleries(
    session: SessionDep,
    current_user: CurrentUser,
    trip_id: uuid.UUID
) -> Any:
    """Get all photo galleries for a trip"""
    
    # Check if trip exists and user has access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this trip")
    
    # Get galleries
    statement = select(PhotoGallery).where(PhotoGallery.trip_id == trip_id)
    galleries = session.exec(statement).all()
    
    count_statement = select(func.count()).select_from(PhotoGallery).where(PhotoGallery.trip_id == trip_id)
    count = session.exec(count_statement).one()
    
    return PhotoGalleriesPublic(data=galleries, count=count)


@router.get("/{gallery_id}", response_model=PhotoGalleryPublic)
def get_gallery(
    session: SessionDep,
    current_user: CurrentUser,
    gallery_id: uuid.UUID
) -> Any:
    """Get a specific photo gallery"""
    
    gallery = session.get(PhotoGallery, gallery_id)
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery not found")
    
    # Check if user has access to the trip
    trip = session.get(Trip, gallery.trip_id)
    if not trip or trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this trip")
    
    return gallery


@router.get("/{gallery_id}/places", response_model=GalleryPlacesPublic)
def get_gallery_places(
    session: SessionDep,
    current_user: CurrentUser,
    gallery_id: uuid.UUID
) -> Any:
    """Get all places in a gallery"""
    
    # Check gallery access
    gallery = session.get(PhotoGallery, gallery_id)
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery not found")
    
    trip = session.get(Trip, gallery.trip_id)
    if not trip or trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this trip")
    
    # Get places
    statement = select(GalleryPlace).where(GalleryPlace.gallery_id == gallery_id)
    places = session.exec(statement).all()
    
    count_statement = select(func.count()).select_from(GalleryPlace).where(GalleryPlace.gallery_id == gallery_id)
    count = session.exec(count_statement).one()
    
    return GalleryPlacesPublic(data=places, count=count)


@router.get("/{gallery_id}/places/{place_id}/photos", response_model=GalleryPhotosPublic)
def get_place_photos(
    session: SessionDep,
    current_user: CurrentUser,
    gallery_id: uuid.UUID,
    place_id: uuid.UUID
) -> Any:
    """Get all photos for a specific place"""
    
    # Check gallery access
    gallery = session.get(PhotoGallery, gallery_id)
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery not found")
    
    trip = session.get(Trip, gallery.trip_id)
    if not trip or trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this trip")
    
    # Check place exists in this gallery
    place = session.get(GalleryPlace, place_id)
    if not place or place.gallery_id != gallery_id:
        raise HTTPException(status_code=404, detail="Place not found in this gallery")
    
    # Get photos
    statement = select(GalleryPhoto).where(GalleryPhoto.place_id == place_id)
    photos = session.exec(statement).all()
    
    count_statement = select(func.count()).select_from(GalleryPhoto).where(GalleryPhoto.place_id == place_id)
    count = session.exec(count_statement).one()
    
    return GalleryPhotosPublic(data=photos, count=count)


@router.post("/{gallery_id}/photos/{photo_id}/track-download")
async def track_photo_download(
    session: SessionDep,
    current_user: CurrentUser,
    gallery_id: uuid.UUID,
    photo_id: uuid.UUID
) -> Any:
    """Track photo download for Unsplash compliance"""
    
    # Check gallery access
    gallery = session.get(PhotoGallery, gallery_id)
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery not found")
    
    trip = session.get(Trip, gallery.trip_id)
    if not trip or trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this trip")
    
    # Get photo
    photo = session.get(GalleryPhoto, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Track download if not already tracked
    if not photo.download_tracked and photo.source == 'unsplash':
        try:
            await photo_gallery_service.download_photo(
                photo.url, 
                photo.photographer_name
            )
            photo.download_tracked = True
            session.add(photo)
            session.commit()
        except Exception as e:
            # Don't fail the request if tracking fails
            pass
    
    return {"message": "Download tracked"}


@router.delete("/{gallery_id}")
def delete_gallery(
    session: SessionDep,
    current_user: CurrentUser,
    gallery_id: uuid.UUID
) -> Any:
    """Delete a photo gallery"""
    
    gallery = session.get(PhotoGallery, gallery_id)
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery not found")
    
    trip = session.get(Trip, gallery.trip_id)
    if not trip or trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this trip")
    
    session.delete(gallery)
    session.commit()
    
    return {"message": "Gallery deleted"}


async def _generate_gallery_background(session, gallery_id: uuid.UUID, itinerary_data: str):
    """Background task to generate photo gallery"""
    try:
        # Update gallery status
        gallery = session.get(PhotoGallery, gallery_id)
        if not gallery:
            return
        
        # Parse itinerary to extract places
        extracted_places = await itinerary_parser_service.extract_places_from_itinerary(itinerary_data)
        
        if not extracted_places:
            gallery.status = "failed"
            session.add(gallery)
            session.commit()
            return
        
        # Convert to dict format for photo service
        places_data = [
            {
                "name": place.name,
                "type": place.type,
                "caption": place.caption,
                "search_query": place.search_query
            }
            for place in extracted_places
        ]
        
        # Fetch photos for places
        place_photos = await photo_gallery_service.fetch_photos_for_places(places_data, max_photos_per_place=6)
        
        total_places = len(place_photos)
        total_photos = sum(len(place.photos) for place in place_photos)
        
        # Save places and photos to database
        for i, place_photo in enumerate(place_photos):
            # Create place
            place_data = GalleryPlaceCreate(
                gallery_id=gallery_id,
                name=place_photo.name,
                place_type=place_photo.type,
                caption=place_photo.caption,
                search_query=place_photo.search_query,
                priority=total_places - i  # Higher priority for earlier places
            )
            
            place = GalleryPlace.model_validate(place_data)
            session.add(place)
            session.commit()
            session.refresh(place)
            
            # Create photos for this place
            for photo_source in place_photo.photos:
                photo_data = GalleryPhotoCreate(
                    place_id=place.id,
                    url=photo_source.url,
                    thumbnail_url=photo_source.thumbnail_url,
                    photographer_name=photo_source.photographer_name,
                    photographer_url=photo_source.photographer_url,
                    source=photo_source.source,
                    width=photo_source.width,
                    height=photo_source.height,
                    description=photo_source.description
                )
                
                photo = GalleryPhoto.model_validate(photo_data)
                session.add(photo)
        
        # Update gallery with final stats
        gallery.status = "completed"
        gallery.total_places = total_places
        gallery.total_photos = total_photos
        gallery.updated_at = datetime.utcnow()
        session.add(gallery)
        session.commit()
        
    except Exception as e:
        # Update gallery status to failed
        gallery = session.get(PhotoGallery, gallery_id)
        if gallery:
            gallery.status = "failed"
            session.add(gallery)
            session.commit()
        raise e
