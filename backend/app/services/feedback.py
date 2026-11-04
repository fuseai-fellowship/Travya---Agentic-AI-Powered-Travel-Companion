"""Thumbs/ratings on generated plans and assistant answers; feeds offline evaluation."""

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import NotFound
from app.models import Conversation, Feedback, FeedbackTarget, Message, User
from app.repositories import FeedbackRepository, TripRepository
from app.schemas.content import FeedbackCreate


async def submit_feedback(session: AsyncSession, user: User, data: FeedbackCreate) -> Feedback:
    if data.target_type == FeedbackTarget.trip_plan:
        await TripRepository(session, user.id).get(data.target_id)
    else:
        owned = await session.exec(
            select(Message.id)
            .join(Conversation, col(Conversation.id) == col(Message.conversation_id))
            .where(Message.id == data.target_id, Conversation.user_id == user.id)
        )
        if owned.first() is None:
            raise NotFound("Message not found")
    repo = FeedbackRepository(session, user.id)
    existing = await repo.all(
        col(Feedback.target_type) == data.target_type, col(Feedback.target_id) == data.target_id
    )
    if existing:
        feedback = await repo.update(existing[0], {"rating": data.rating, "comment": data.comment})
    else:
        feedback = await repo.add(Feedback(user_id=user.id, **data.model_dump()))
    await session.commit()
    return feedback
