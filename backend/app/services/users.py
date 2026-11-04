"""Local user profiles mirrored from Firebase, account settings and account deletion."""

from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import Principal, delete_firebase_user
from app.integrations.ports import ObjectStorage
from app.models import User
from app.schemas.content import MeUpdate
from app.services.documents import DocumentService


async def get_or_create_user(session: AsyncSession, principal: Principal) -> User:
    stmt = select(User).where(User.firebase_uid == principal.uid)
    user = (await session.exec(stmt)).first()
    if user is None:
        user = User(
            firebase_uid=principal.uid,
            email=principal.email,
            display_name=principal.name,
            is_anonymous=principal.is_anonymous,
        )
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:  # two first requests raced; the other one created the row
            await session.rollback()
            user = (await session.exec(stmt)).one()
        return user
    # An anonymous demo account keeps its uid when upgraded to email or Google sign-in.
    if (user.email, user.is_anonymous) != (principal.email, principal.is_anonymous):
        user.email = principal.email
        user.is_anonymous = principal.is_anonymous
        user.display_name = user.display_name or principal.name
        session.add(user)
        await session.commit()
    return user


async def update_me(session: AsyncSession, user: User, data: MeUpdate) -> User:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_account(session: AsyncSession, user: User, storage: ObjectStorage) -> None:
    """Deletes files, every row the user owns (database cascades) and the Firebase account."""
    await DocumentService(session, user, storage).delete_all()
    await session.delete(user)
    await session.commit()
    await delete_firebase_user(user.firebase_uid)
