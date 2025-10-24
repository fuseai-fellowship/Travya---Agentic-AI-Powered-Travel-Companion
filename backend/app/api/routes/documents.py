"""
Document management API endpoints for travel bookings and trip documents.
"""

import uuid
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
import io

from app.api.deps import CurrentUser, SessionDep
from app.models import Trip, Booking, TripCollaborator
from app.services.document_storage import document_storage_service, booking_document_service
from app.services.document_storage import DocumentInfo, DocumentUploadResponse
from sqlmodel import select

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    trip_id: Optional[uuid.UUID] = None,
    booking_id: Optional[uuid.UUID] = None,
    document_type: str = "general",
    tags: Optional[List[str]] = None
) -> Any:
    """Upload a document for a trip or booking."""
    
    # Validate access to trip if provided
    if trip_id:
        trip = session.get(Trip, trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        # Check if user has access to the trip
        if trip.owner_id != current_user.id:
            collaborator = session.exec(
                select(TripCollaborator).where(
                    TripCollaborator.trip_id == trip_id,
                    TripCollaborator.user_id == current_user.id
                )
            ).first()
            if not collaborator:
                raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Validate access to booking if provided
    if booking_id:
        booking = session.get(Booking, booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Check if user has access to the booking's trip
        trip = session.get(Trip, booking.trip_id)
        if trip.owner_id != current_user.id:
            collaborator = session.exec(
                select(TripCollaborator).where(
                    TripCollaborator.trip_id == booking.trip_id,
                    TripCollaborator.user_id == current_user.id
                )
            ).first()
            if not collaborator:
                raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Upload document
    try:
        result = await document_storage_service.upload_document(
            file=file,
            uploaded_by=str(current_user.id),
            trip_id=str(trip_id) if trip_id else None,
            booking_id=str(booking_id) if booking_id else None,
            document_type=document_type,
            tags=tags or []
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: CurrentUser,
    session: SessionDep
) -> Any:
    """Get document information."""
    
    document_info = await document_storage_service.get_document(document_id)
    if not document_info:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check access permissions
    if document_info.trip_id:
        trip = session.get(Trip, uuid.UUID(document_info.trip_id))
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        if trip.owner_id != current_user.id:
            collaborator = session.exec(
                select(TripCollaborator).where(
                    TripCollaborator.trip_id == trip.id,
                    TripCollaborator.user_id == current_user.id
                )
            ).first()
            if not collaborator:
                raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return document_info


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: CurrentUser,
    session: SessionDep
) -> Any:
    """Download document file."""
    
    document_info = await document_storage_service.get_document(document_id)
    if not document_info:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check access permissions
    if document_info.trip_id:
        trip = session.get(Trip, uuid.UUID(document_info.trip_id))
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        if trip.owner_id != current_user.id:
            collaborator = session.exec(
                select(TripCollaborator).where(
                    TripCollaborator.trip_id == trip.id,
                    TripCollaborator.user_id == current_user.id
                )
            ).first()
            if not collaborator:
                raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get file content
    file_content = await document_storage_service.get_document_file(document_id)
    if not file_content:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return file as streaming response
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=document_info.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={document_info.original_filename}"
        }
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: CurrentUser,
    session: SessionDep
) -> Any:
    """Delete a document."""
    
    document_info = await document_storage_service.get_document(document_id)
    if not document_info:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check access permissions - only owner or trip owner can delete
    if document_info.uploaded_by != str(current_user.id):
        if document_info.trip_id:
            trip = session.get(Trip, uuid.UUID(document_info.trip_id))
            if not trip or trip.owner_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not enough permissions")
        else:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Delete document
    success = await document_storage_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")
    
    return {"message": "Document deleted successfully"}


@router.get("/trip/{trip_id}")
async def get_trip_documents(
    trip_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    document_type: Optional[str] = Query(None, description="Filter by document type")
) -> Any:
    """Get all documents for a trip."""
    
    # Check trip access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == trip_id,
                TripCollaborator.user_id == current_user.id
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get documents
    documents = await document_storage_service.list_documents(
        trip_id=str(trip_id),
        document_type=document_type
    )
    
    return {"documents": documents, "count": len(documents)}


@router.get("/booking/{booking_id}")
async def get_booking_documents(
    booking_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    document_type: Optional[str] = Query(None, description="Filter by document type")
) -> Any:
    """Get all documents for a booking."""
    
    # Check booking access
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    trip = session.get(Trip, booking.trip_id)
    if trip.owner_id != current_user.id:
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == booking.trip_id,
                TripCollaborator.user_id == current_user.id
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get documents
    documents = await document_storage_service.list_documents(
        booking_id=str(booking_id),
        document_type=document_type
    )
    
    return {"documents": documents, "count": len(documents)}


@router.post("/booking/{booking_id}/upload", response_model=DocumentUploadResponse)
async def upload_booking_document(
    *,
    booking_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    file: UploadFile = File(...),
    document_type: str = "booking_confirmation"
) -> Any:
    """Upload a document for a specific booking."""
    
    # Check booking access
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    trip = session.get(Trip, booking.trip_id)
    if trip.owner_id != current_user.id:
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == booking.trip_id,
                TripCollaborator.user_id == current_user.id,
                TripCollaborator.permission.in_(["edit", "admin"])
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Upload document
    try:
        result = await booking_document_service.attach_document_to_booking(
            booking_id=str(booking_id),
            file=file,
            uploaded_by=str(current_user.id),
            document_type=document_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/trip/{trip_id}/upload", response_model=DocumentUploadResponse)
async def upload_trip_document(
    *,
    trip_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    file: UploadFile = File(...),
    document_type: str = "trip_document"
) -> Any:
    """Upload a document for a specific trip."""
    
    # Check trip access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == trip_id,
                TripCollaborator.user_id == current_user.id,
                TripCollaborator.permission.in_(["edit", "admin"])
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Upload document
    try:
        result = await booking_document_service.attach_document_to_trip(
            trip_id=str(trip_id),
            file=file,
            uploaded_by=str(current_user.id),
            document_type=document_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
