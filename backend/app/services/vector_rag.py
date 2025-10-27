import os
import json
import uuid
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
import aiohttp
from dataclasses import dataclass
from sqlmodel import Session, select
from app.core.config import settings
from app.core.llm import call_llm
from app.models import Trip, Itinerary, ConversationMessage, User
from app import crud
from app.services.redis_cache import RedisCacheService

# Try to import vector database libraries
try:
    import faiss
    import sentence_transformers
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS and sentence-transformers not available. Install with: pip install faiss-cpu sentence-transformers")

@dataclass
class TravelContext:
    user_id: str
    trip_id: Optional[str] = None
    conversation_id: Optional[str] = None

@dataclass
class VectorSearchResult:
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    source_type: str  # 'trip', 'itinerary', 'conversation'

@dataclass
class RAGResult:
    response: str
    sources: List[str] = None
    images: List[Dict[str, Any]] = None
    suggestions: List[str] = None
    confidence: float = 1.0

class VectorTravelRAGService:
    def __init__(self):
        self.model = None
        self.index = None
        self.documents = []
        self.metadata = []
        self.session = None
        self.cache_service = RedisCacheService()
        
        if FAISS_AVAILABLE:
            try:
                # Initialize sentence transformer model
                self.model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
                # Initialize FAISS index
                self.index = faiss.IndexFlatIP(384)  # 384 is the dimension for all-MiniLM-L6-v2
            except Exception as e:
                print(f"Error initializing vector model: {e}")
                # Don't modify global variable here

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _build_vector_index(self, context: TravelContext, session: Session):
        """Build vector index from travel data"""
        if not self.model or not self.index:
            print("Vector model not available, skipping vector index")
            return []
        
        self.documents = []
        self.metadata = []
        
        # Get user's trips
        trips_query = select(Trip).where(Trip.owner_id == context.user_id)
        if context.trip_id:
            trips_query = trips_query.where(Trip.id == context.trip_id)
        
        trips = session.exec(trips_query).all()
        
        for trip in trips:
            # Add trip basic info
            trip_text = f"Trip: {trip.title} to {trip.destination}. Type: {trip.trip_type}. Budget: ${trip.budget}. Description: {trip.description or ''}"
            self.documents.append(trip_text)
            self.metadata.append({
                "type": "trip",
                "id": str(trip.id),
                "title": trip.title,
                "destination": trip.destination,
                "trip_type": trip.trip_type,
                "budget": trip.budget
            })
            
            # Parse and add detailed AI itinerary data
            if trip.ai_itinerary_data:
                try:
                    ai_data = json.loads(trip.ai_itinerary_data)
                    if 'itinerary' in ai_data and 'itinerary' in ai_data['itinerary']:
                        detailed_itinerary = ai_data['itinerary']['itinerary']
                        
                        # Add overview
                        if 'overview' in detailed_itinerary:
                            overview = detailed_itinerary['overview']
                            overview_text = f"Trip Overview: {overview.get('destination', '')} - {overview.get('duration', 0)} days, ${overview.get('total_estimated_cost', 0)} total cost, {overview.get('difficulty_level', '')} difficulty, best time: {overview.get('best_time_to_visit', '')}"
                            self.documents.append(overview_text)
                            self.metadata.append({
                                "type": "trip_overview",
                                "trip_id": str(trip.id),
                                "destination": overview.get('destination', ''),
                                "duration": overview.get('duration', 0),
                                "total_cost": overview.get('total_estimated_cost', 0),
                                "difficulty": overview.get('difficulty_level', '')
                            })
                        
                        # Add day-by-day details
                        if 'days' in detailed_itinerary:
                            for day in detailed_itinerary['days']:
                                day_text = f"Day {day.get('day', 0)}: {day.get('theme', '')} - Budget: ${day.get('daily_budget', 0)}. Tips: {day.get('daily_tips', '')}"
                                
                                # Add activities
                                if 'activities' in day:
                                    activities_text = []
                                    for activity in day['activities']:
                                        activity_desc = f"{activity.get('activity', '')} at {activity.get('location', '')} at {activity.get('time', '')} for {activity.get('duration', '')}"
                                        cost = activity.get('cost', 0)
                                        if isinstance(cost, (int, float)) and cost > 0:
                                            activity_desc += f" costing ${cost}"
                                        if activity.get('description'):
                                            activity_desc += f". {activity.get('description', '')}"
                                        activities_text.append(activity_desc)
                                    
                                    if activities_text:
                                        day_text += f" Activities: {'; '.join(activities_text)}"
                                
                                # Add meals
                                if 'meals' in day:
                                    meals_text = []
                                    for meal in day['meals']:
                                        meal_desc = f"{meal.get('meal_type', '')} at {meal.get('location', '')} at {meal.get('time', '')}"
                                        cost = meal.get('cost', 0)
                                        if isinstance(cost, (int, float)) and cost > 0:
                                            meal_desc += f" costing ${cost}"
                                        if meal.get('description'):
                                            meal_desc += f". {meal.get('description', '')}"
                                        meals_text.append(meal_desc)
                                    
                                    if meals_text:
                                        day_text += f" Meals: {'; '.join(meals_text)}"
                                
                                self.documents.append(day_text)
                                self.metadata.append({
                                    "type": "itinerary_day",
                                    "trip_id": str(trip.id),
                                    "day": day.get('day', 0),
                                    "theme": day.get('theme', ''),
                                    "daily_budget": day.get('daily_budget', 0),
                                    "activities": activities_text if 'activities' in day else [],
                                    "meals": meals_text if 'meals' in day else []
                                })
                                
                except Exception as e:
                    print(f"Error parsing AI itinerary data for trip {trip.id}: {e}")
        
        # Build FAISS index if we have documents
        if self.documents and self.model and self.index:
            try:
                # Generate embeddings
                embeddings = self.model.encode(self.documents)
                # Normalize embeddings for cosine similarity
                embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
                # Add to FAISS index
                self.index.add(embeddings.astype('float32'))
                print(f"Built vector index with {len(self.documents)} documents")
            except Exception as e:
                print(f"Error building vector index: {e}")
                self.model = None
                self.index = None

    async def _vector_search(self, query: str, user_id: str, top_k: int = 5) -> List[VectorSearchResult]:
        """Search for relevant documents using vector similarity with caching"""
        if not self.model or not self.index or not self.documents:
            return []
        
        try:
            # Check cache first
            cached_results = await self.cache_service.get_cached_vector_search(user_id, query)
            if cached_results:
                print(f"✅ Using cached vector search results for user {user_id}")
                return [VectorSearchResult(**result) for result in cached_results]
            
            # Encode query
            query_embedding = self.model.encode([query])
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
            
            # Search in FAISS index
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    results.append(VectorSearchResult(
                        content=self.documents[idx],
                        metadata=self.metadata[idx],
                        similarity_score=float(score),
                        source_type=self.metadata[idx].get('type', 'unknown')
                    ))
            
            # Cache the results
            if results:
                cache_data = [
                    {
                        "content": r.content,
                        "metadata": r.metadata,
                        "similarity_score": r.similarity_score,
                        "source_type": r.source_type
                    }
                    for r in results
                ]
                await self.cache_service.cache_vector_search(user_id, query, cache_data)
            
            return results
        except Exception as e:
            print(f"Error in vector search: {e}")
            return []

    async def query_with_context(
        self, user_query: str, travel_context: TravelContext, session: Session
    ) -> RAGResult:
        """Enhanced query with vector search and context with caching"""
        
        # Check for cached AI response first
        cached_response = await self.cache_service.get_cached_ai_response(
            travel_context.user_id, user_query
        )
        if cached_response:
            print(f"✅ Using cached AI response for user {travel_context.user_id}")
            return RAGResult(
                response=cached_response["response"],
                sources=cached_response["metadata"].get("sources", []),
                suggestions=cached_response["metadata"].get("suggestions", []),
                confidence=cached_response["metadata"].get("confidence", 0.8)
            )
        
        # Build vector index
        await self._build_vector_index(travel_context, session)
        
        # Perform vector search with caching
        search_results = await self._vector_search(user_query, travel_context.user_id, top_k=5)
        
        # Get conversation history
        conversation_history = await self._get_conversation_history(travel_context, session)
        
        # Generate response using retrieved context
        response = await self._generate_enhanced_response(
            user_query, search_results, conversation_history, travel_context
        )
        
        # Extract sources
        sources = [result.content[:100] + "..." for result in search_results[:3]]
        
        # Generate suggestions
        suggestions = await self._generate_suggestions(user_query, search_results)
        
        # Cache the AI response
        metadata = {
            "sources": sources,
            "suggestions": suggestions,
            "confidence": 0.9 if search_results else 0.5,
            "search_results_count": len(search_results)
        }
        await self.cache_service.cache_ai_response(
            travel_context.user_id, user_query, response, metadata
        )
        
        return RAGResult(
            response=response,
            sources=sources,
            suggestions=suggestions,
            confidence=0.9 if search_results else 0.5
        )

    async def _get_conversation_history(
        self, context: TravelContext, session: Session
    ) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        if not context.conversation_id:
            return []
        
        try:
            messages = session.exec(
                select(ConversationMessage)
                .where(ConversationMessage.conversation_id == context.conversation_id)
                .order_by(ConversationMessage.created_at.desc())
                .limit(10)
            ).all()
            
            return [
                {
                    "sender": msg.sender,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in reversed(messages)
            ]
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    async def _generate_enhanced_response(
        self,
        user_query: str,
        search_results: List[VectorSearchResult],
        conversation_history: List[Dict[str, Any]],
        context: TravelContext
    ) -> str:
        """Generate response using vector search results"""
        
        # Build context from search results
        context_parts = []
        
        if search_results:
            context_parts.append("Relevant Travel Information:")
            for result in search_results[:3]:  # Top 3 results
                context_parts.append(f"- {result.content}")
        
        if conversation_history:
            context_parts.append("\nRecent Conversation:")
            for msg in conversation_history[-3:]:  # Last 3 messages
                context_parts.append(f"- {msg['sender']}: {msg['content'][:100]}...")
        
        context_string = "\n".join(context_parts)
        
        # Create enhanced prompt
        prompt = f"""
        You are a helpful travel assistant with access to the user's detailed travel data.
        
        Context:
        {context_string}
        
        User Query: {user_query}
        
        IMPORTANT INSTRUCTIONS:
        1. If you have specific travel data about the user's trips, use it to provide personalized answers.
        2. If the user asks about their specific trips (duration, cost, activities), provide information from their data.
        3. If the user asks general travel questions (like "best time to visit Japan") and you don't have specific data about that destination, provide helpful general travel advice.
        4. For general travel questions, be informative and helpful even without specific user data.
        5. If they ask about photos/images, mention that you can help them find images.
        6. Always be conversational, helpful, and provide valuable travel information.
        
        Please provide a helpful response. If you have specific user data, use it. If not, provide general travel advice.
        """
        
        try:
            response = call_llm(prompt)
            return response
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'd be happy to help you with your travel plans! Could you tell me more about what you'd like to know?"

    async def _generate_suggestions(
        self, user_query: str, search_results: List[VectorSearchResult]
    ) -> List[str]:
        """Generate helpful suggestions based on query and results"""
        suggestions = []
        
        # Add context-aware suggestions
        if any("budget" in query.lower() for query in [user_query]):
            suggestions.extend([
                "Tell me about my trip costs",
                "What's my daily budget?",
                "Show me cost breakdown"
            ])
        
        if any("activity" in query.lower() for query in [user_query]):
            suggestions.extend([
                "What activities do I have planned?",
                "Show me my itinerary",
                "What should I do today?"
            ])
        
        if any("photo" in query.lower() or "image" in query.lower() for query in [user_query]):
            suggestions.extend([
                "Show me photos of this place",
                "Find images of my destination",
                "What does this location look like?"
            ])
        
        # Add general suggestions
        suggestions.extend([
            "Plan a new trip",
            "Tell me about my upcoming trips",
            "Help me with travel tips"
        ])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    async def invalidate_user_cache(self, user_id: str) -> None:
        """Invalidate all cache for a user when new trip is added"""
        await self.cache_service.invalidate_user_cache(user_id)
        print(f"🗑️ Invalidated all cache for user {user_id}")
    
    async def invalidate_vector_cache(self, user_id: str) -> None:
        """Invalidate only vector search cache for a user"""
        await self.cache_service.invalidate_vector_cache(user_id)
        print(f"🗑️ Invalidated vector cache for user {user_id}")
    
    async def get_cache_stats(self, user_id: str) -> Dict[str, Any]:
        """Get cache statistics for a user"""
        return await self.cache_service.get_cache_stats(user_id)
