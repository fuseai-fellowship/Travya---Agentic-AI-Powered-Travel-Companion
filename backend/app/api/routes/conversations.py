import uuid
from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Conversation, ConversationCreate, ConversationUpdate, ConversationPublic, ConversationsPublic,
    ConversationMessage, ConversationMessageCreate, ConversationMessagePublic, ConversationMessagesPublic
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ===== CONVERSATION ENDPOINTS =====

@router.get("", response_model=ConversationsPublic)
def read_conversations(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve user's conversations."""
    
    # Query for user's conversations
    statement = select(Conversation).where(Conversation.user_id == current_user.id)
    
    # Get count
    count_statement = select(func.count()).select_from(Conversation).where(Conversation.user_id == current_user.id)
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
def create_conversation_message(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    conversation_id: uuid.UUID,
    message_in: ConversationMessageCreate
) -> Any:
    """Create a new message in a conversation."""
    
    # Check conversation access
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Create message
    message = ConversationMessage.model_validate(
        message_in,
        update={"conversation_id": conversation_id}
    )
    session.add(message)
    
    # Update conversation's last_message and updated_at
    conversation.last_message = message_in.content[:100]  # Store first 100 chars
    conversation.updated_at = datetime.now()
    session.add(conversation)
    
    session.commit()
    session.refresh(message)
    return message

