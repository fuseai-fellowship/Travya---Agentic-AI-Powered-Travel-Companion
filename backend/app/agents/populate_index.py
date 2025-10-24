from sqlmodel import Session, select
from .tools import init_mock_vector_store, add_to_mock_vector_store
from app.core.config import settings
from ..core.db import engine
from ..models import User  # Adjust based on your models

def generate_embedding(text: str) -> list[float]:
    """Mock embedding generation."""
    import numpy as np
    return np.random.rand(768).tolist()  # Mock 768-dim embedding

def populate_index():
    """Populate mock vector store with user data embeddings."""
    init_mock_vector_store()
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for user in users:
            # Example: Embed user preferences or past trips
            user_data = f"User {user.email}: preferences={getattr(user, 'preferences', 'budget-friendly')}"
            embedding = generate_embedding(user_data)
            payload = {"email": user.email, "preferences": getattr(user, 'preferences', 'budget-friendly')}
            add_to_mock_vector_store(embedding, payload)
    print("Mock vector store populated.")

if __name__ == "__main__":
    populate_index()