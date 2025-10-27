import uuid
from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import func, select, or_

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Conversation, ConversationCreate, ConversationUpdate, ConversationPublic, ConversationsPublic,
    ConversationMessage, ConversationMessageCreate, ConversationMessagePublic, ConversationMessagesPublic
)
from app.services.image_scraping import rag_image_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ===== CONVERSATION ENDPOINTS =====

@router.get("", response_model=ConversationsPublic)
def read_conversations(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in conversation titles and content"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived status"),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite status"),
) -> Any:
    """Retrieve user's conversations with enhanced filtering."""
    
    # Query for user's conversations
    statement = select(Conversation).where(Conversation.user_id == current_user.id)
    
    # Add search filter
    if search:
        statement = statement.where(
            or_(
                Conversation.title.ilike(f"%{search}%"),
                Conversation.last_message.ilike(f"%{search}%"),
                Conversation.context.ilike(f"%{search}%")
            )
        )
    
    # Add archive filter
    if is_archived is not None:
        statement = statement.where(Conversation.is_archived == is_archived)
    
    # Add favorite filter
    if is_favorite is not None:
        statement = statement.where(Conversation.is_favorite == is_favorite)
    
    # Get count
    count_statement = select(func.count()).select_from(Conversation).where(Conversation.user_id == current_user.id)
    if search:
        count_statement = count_statement.where(
            or_(
                Conversation.title.ilike(f"%{search}%"),
                Conversation.last_message.ilike(f"%{search}%"),
                Conversation.context.ilike(f"%{search}%")
            )
        )
    if is_archived is not None:
        count_statement = count_statement.where(Conversation.is_archived == is_archived)
    if is_favorite is not None:
        count_statement = count_statement.where(Conversation.is_favorite == is_favorite)
    
    count = session.exec(count_statement).one()
    
    # Get conversations ordered by updated_at desc
    conversations = session.exec(
        statement.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
    ).all()
    
    return ConversationsPublic(data=conversations, count=count)


@router.get("/{conversation_id}", response_model=ConversationPublic)
def read_conversation(
    session: SessionDep,
    current_user: CurrentUser,
    conversation_id: uuid.UUID
) -> Any:
    """Retrieve a specific conversation."""
    
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if user owns this conversation
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return conversation


@router.post("", response_model=ConversationPublic)
def create_conversation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    conversation_in: ConversationCreate
) -> Any:
    """Create a new conversation."""
    
    conversation = Conversation.model_validate(
        conversation_in,
        update={"user_id": current_user.id}
    )
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


@router.put("/{conversation_id}", response_model=ConversationPublic)
def update_conversation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    conversation_id: uuid.UUID,
    conversation_in: ConversationUpdate
) -> Any:
    """Update a conversation."""
    
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_dict = conversation_in.model_dump(exclude_unset=True)
    conversation.sqlmodel_update(update_dict)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


@router.delete("/{conversation_id}")
def delete_conversation(
    session: SessionDep,
    current_user: CurrentUser,
    conversation_id: uuid.UUID
) -> Any:
    """Delete a conversation and all its messages."""
    
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    session.delete(conversation)
    session.commit()
    return {"ok": True}


# ===== CONVERSATION MESSAGE ENDPOINTS =====

@router.get("/{conversation_id}/messages", response_model=ConversationMessagesPublic)
def read_conversation_messages(
    session: SessionDep,
    current_user: CurrentUser,
    conversation_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve messages for a conversation."""
    
    # Check conversation access
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Query for messages
    statement = select(ConversationMessage).where(
        ConversationMessage.conversation_id == conversation_id
    )
    
    # Get count
    count_statement = select(func.count()).select_from(ConversationMessage).where(
        ConversationMessage.conversation_id == conversation_id
    )
    count = session.exec(count_statement).one()
    
    # Get messages ordered by created_at
    messages = session.exec(
        statement.order_by(ConversationMessage.created_at).offset(skip).limit(limit)
    ).all()
    
    return ConversationMessagesPublic(data=messages, count=count)


@router.post("/{conversation_id}/messages", response_model=ConversationMessagePublic)
async def create_conversation_message(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    conversation_id: uuid.UUID,
    message_in: ConversationMessageCreate
) -> Any:
    """Create a new message in a conversation with RAG image support."""
    
    # Check conversation access
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Create user message
    user_message = ConversationMessage.model_validate(
        message_in,
        update={"conversation_id": conversation_id}
    )
    session.add(user_message)
    
    # Check if this is an image query and generate response
    response_content = message_in.content
    response_images = []
    
    if rag_image_service.is_image_query(message_in.content):
        try:
            async with rag_image_service as rag_service:
                response_text, images = await rag_service.retrieve_images_for_chat(
                    message_in.content,
                    str(current_user.id),
                    session,
                    limit=6
                )
                response_content = response_text
                response_images = [img.to_dict() for img in images]
        except Exception as e:
            # If RAG fails, fall back to a simple response
            response_content = "I can help you find images from your trips! Try asking something like 'show me images of my trip to Annapurna Circuit' or 'display photos from my travel'"
            response_images = []
    
    # Create AI response message
    ai_message = ConversationMessage(
        conversation_id=conversation_id,
        content=response_content,
        role="assistant",
        images=response_images if response_images else None
    )
    session.add(ai_message)
    
    # Update conversation's last_message and updated_at
    conversation.last_message = message_in.content[:100]  # Store first 100 chars
    conversation.updated_at = datetime.now()
    session.add(conversation)
    
    session.commit()
    session.refresh(user_message)
    session.refresh(ai_message)
    
    # Return the AI response (the one with images)
    return ai_message

