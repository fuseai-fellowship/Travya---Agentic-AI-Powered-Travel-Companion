"""
Document storage service for travel bookings and trip documents.
Supports file uploads, document management, and cloud storage integration.
"""

import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import aiofiles
from fastapi import UploadFile, HTTPException
from pydantic import BaseModel
import mimetypes
from app.core.config import settings


# ===== DATA MODELS =====

class DocumentInfo(BaseModel):
    id: str
    filename: str
    original_filename: str
    content_type: str
    size: int
    upload_date: datetime
    uploaded_by: str
    trip_id: Optional[str] = None
    booking_id: Optional[str] = None
    document_type: str  # booking_confirmation, receipt, passport, visa, etc.
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    url: str
    size: int
    content_type: str


# ===== DOCUMENT STORAGE SERVICE =====

class DocumentStorageService:
    def __init__(self):
        self.storage_path = Path(settings.DOCUMENT_STORAGE_PATH or "./uploads")
        self.max_file_size = settings.MAX_FILE_SIZE or 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx', 
            '.xls', '.xlsx', '.txt', '.csv', '.zip', '.rar'
        }
        self.allowed_mime_types = {
            'application/pdf',
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain', 'text/csv',
            'application/zip', 'application/x-rar-compressed'
        }
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_document(
        self,
        file: UploadFile,
        uploaded_by: str,
        trip_id: Optional[str] = None,
        booking_id: Optional[str] = None,
        document_type: str = "general",
        tags: List[str] = None
    ) -> DocumentUploadResponse:
        """Upload a document and return document information."""
        
        if tags is None:
            tags = []
        
        # Validate file
        await self._validate_file(file)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create directory structure: uploads/trip_id/booking_id/
        if trip_id:
            trip_dir = self.storage_path / trip_id
            trip_dir.mkdir(exist_ok=True)
            
            if booking_id:
                booking_dir = trip_dir / booking_id
                booking_dir.mkdir(exist_ok=True)
                file_path = booking_dir / unique_filename
            else:
                file_path = trip_dir / unique_filename
        else:
            file_path = self.storage_path / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Get file info
        file_size = len(content)
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Create document info
        document_info = DocumentInfo(
            id=document_id,
            filename=unique_filename,
            original_filename=file.filename,
            content_type=content_type,
            size=file_size,
            upload_date=datetime.utcnow(),
            uploaded_by=uploaded_by,
            trip_id=trip_id,
            booking_id=booking_id,
            document_type=document_type,
            tags=tags,
            metadata={
                "file_path": str(file_path),
                "storage_type": "local"
            }
        )
        
        # Save document metadata (in a real implementation, this would go to database)
        await self._save_document_metadata(document_info)
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=unique_filename,
            url=f"/api/v1/documents/{document_id}",
            size=file_size,
            content_type=content_type
        )
    
    async def get_document(self, document_id: str) -> Optional[DocumentInfo]:
        """Get document information by ID."""
        # In a real implementation, this would query the database
        return await self._get_document_metadata(document_id)
    
    async def get_document_file(self, document_id: str) -> Optional[bytes]:
        """Get document file content by ID."""
        document_info = await self.get_document(document_id)
        if not document_info:
            return None
        
        file_path = Path(document_info.metadata.get("file_path"))
        if not file_path.exists():
            return None
        
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and its file."""
        document_info = await self.get_document(document_id)
        if not document_info:
            return False
        
        # Delete file
        file_path = Path(document_info.metadata.get("file_path"))
        if file_path.exists():
            file_path.unlink()
        
        # Delete metadata
        await self._delete_document_metadata(document_id)
        return True
    
    async def list_documents(
        self,
        trip_id: Optional[str] = None,
        booking_id: Optional[str] = None,
        document_type: Optional[str] = None,
        uploaded_by: Optional[str] = None
    ) -> List[DocumentInfo]:
        """List documents with optional filtering."""
        # In a real implementation, this would query the database
        return await self._list_document_metadata(
            trip_id=trip_id,
            booking_id=booking_id,
            document_type=document_type,
            uploaded_by=uploaded_by
        )
    
    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        # Check file size
        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {self.max_file_size / (1024*1024):.1f}MB"
            )
        
        # Check file extension
        if file.filename:
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in self.allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
                )
        
        # Check MIME type
        if file.content_type and file.content_type not in self.allowed_mime_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Content type: {file.content_type}"
            )
    
    async def _save_document_metadata(self, document_info: DocumentInfo) -> None:
        """Save document metadata to storage."""
        # In a real implementation, this would save to database
        # For now, we'll use a simple file-based storage
        metadata_file = self.storage_path / f"{document_info.id}.json"
        async with aiofiles.open(metadata_file, 'w') as f:
            await f.write(document_info.model_dump_json())
    
    async def _get_document_metadata(self, document_id: str) -> Optional[DocumentInfo]:
        """Get document metadata from storage."""
        # In a real implementation, this would query the database
        metadata_file = self.storage_path / f"{document_id}.json"
        if not metadata_file.exists():
            return None
        
        async with aiofiles.open(metadata_file, 'r') as f:
            content = await f.read()
            return DocumentInfo.model_validate_json(content)
    
    async def _delete_document_metadata(self, document_id: str) -> None:
        """Delete document metadata from storage."""
        # In a real implementation, this would delete from database
        metadata_file = self.storage_path / f"{document_id}.json"
        if metadata_file.exists():
            metadata_file.unlink()
    
    async def _list_document_metadata(
        self,
        trip_id: Optional[str] = None,
        booking_id: Optional[str] = None,
        document_type: Optional[str] = None,
        uploaded_by: Optional[str] = None
    ) -> List[DocumentInfo]:
        """List document metadata with filtering."""
        # In a real implementation, this would query the database
        documents = []
        
        # Simple file-based listing (not efficient for production)
        for metadata_file in self.storage_path.glob("*.json"):
            try:
                async with aiofiles.open(metadata_file, 'r') as f:
                    content = await f.read()
                    doc_info = DocumentInfo.model_validate_json(content)
                    
                    # Apply filters
                    if trip_id and doc_info.trip_id != trip_id:
                        continue
                    if booking_id and doc_info.booking_id != booking_id:
                        continue
                    if document_type and doc_info.document_type != document_type:
                        continue
                    if uploaded_by and doc_info.uploaded_by != uploaded_by:
                        continue
                    
                    documents.append(doc_info)
            except Exception:
                continue
        
        return documents


# ===== BOOKING DOCUMENT INTEGRATION =====

class BookingDocumentService:
    def __init__(self, document_storage: DocumentStorageService):
        self.document_storage = document_storage
    
    async def attach_document_to_booking(
        self,
        booking_id: str,
        file: UploadFile,
        uploaded_by: str,
        document_type: str = "booking_confirmation"
    ) -> DocumentUploadResponse:
        """Attach a document to a specific booking."""
        return await self.document_storage.upload_document(
            file=file,
            uploaded_by=uploaded_by,
            booking_id=booking_id,
            document_type=document_type,
            tags=["booking", "confirmation"]
        )
    
    async def get_booking_documents(self, booking_id: str) -> List[DocumentInfo]:
        """Get all documents for a specific booking."""
        return await self.document_storage.list_documents(booking_id=booking_id)
    
    async def attach_document_to_trip(
        self,
        trip_id: str,
        file: UploadFile,
        uploaded_by: str,
        document_type: str = "trip_document"
    ) -> DocumentUploadResponse:
        """Attach a document to a trip."""
        return await self.document_storage.upload_document(
            file=file,
            uploaded_by=uploaded_by,
            trip_id=trip_id,
            document_type=document_type,
            tags=["trip", "document"]
        )
    
    async def get_trip_documents(self, trip_id: str) -> List[DocumentInfo]:
        """Get all documents for a specific trip."""
        return await self.document_storage.list_documents(trip_id=trip_id)


# ===== SERVICE INSTANCES =====

document_storage_service = DocumentStorageService()
booking_document_service = BookingDocumentService(document_storage_service)
