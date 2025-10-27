import json
import hashlib
import redis
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from app.core.config import settings

class RedisCacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.cache_ttl = 3600  # 1 hour default TTL
        self.vector_cache_ttl = 1800  # 30 minutes for vector search results
        self.response_cache_ttl = 600  # 10 minutes for AI responses
    
    def _generate_cache_key(self, prefix: str, data: Any) -> str:
        """Generate a consistent cache key from data"""
        if isinstance(data, dict):
            # Sort dict keys for consistent hashing
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        # Create hash of the data
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def _generate_user_cache_key(self, user_id: str, prefix: str, data: Any) -> str:
        """Generate cache key with user context"""
        base_key = self._generate_cache_key(prefix, data)
        return f"user:{user_id}:{base_key}"
    
    async def cache_vector_search(
        self, 
        user_id: str, 
        query: str, 
        search_results: List[Dict[str, Any]]
    ) -> None:
        """Cache vector search results"""
        cache_key = self._generate_user_cache_key(
            user_id, 
            "vector_search", 
            {"query": query.lower().strip()}
        )
        
        try:
            # Store search results with metadata
            cache_data = {
                "query": query,
                "results": search_results,
                "cached_at": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            self.redis_client.setex(
                cache_key,
                self.vector_cache_ttl,
                json.dumps(cache_data)
            )
            print(f"✅ Cached vector search for user {user_id}")
            
        except Exception as e:
            print(f"Error caching vector search: {e}")
    
    async def get_cached_vector_search(
        self, 
        user_id: str, 
        query: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached vector search results"""
        cache_key = self._generate_user_cache_key(
            user_id, 
            "vector_search", 
            {"query": query.lower().strip()}
        )
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                print(f"✅ Found cached vector search for user {user_id}")
                return data.get("results", [])
        except Exception as e:
            print(f"Error retrieving cached vector search: {e}")
        
        return None
    
    async def cache_ai_response(
        self,
        user_id: str,
        query: str,
        response: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Cache AI response"""
        cache_key = self._generate_user_cache_key(
            user_id,
            "ai_response",
            {"query": query.lower().strip()}
        )
        
        try:
            cache_data = {
                "query": query,
                "response": response,
                "metadata": metadata,
                "cached_at": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            self.redis_client.setex(
                cache_key,
                self.response_cache_ttl,
                json.dumps(cache_data)
            )
            print(f"✅ Cached AI response for user {user_id}")
            
        except Exception as e:
            print(f"Error caching AI response: {e}")
    
    async def get_cached_ai_response(
        self,
        user_id: str,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached AI response"""
        cache_key = self._generate_user_cache_key(
            user_id,
            "ai_response",
            {"query": query.lower().strip()}
        )
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                print(f"✅ Found cached AI response for user {user_id}")
                return data
        except Exception as e:
            print(f"Error retrieving cached AI response: {e}")
        
        return None
    
    async def invalidate_user_cache(self, user_id: str) -> None:
        """Invalidate all cache for a user (when new trip is added)"""
        try:
            # Get all keys for this user
            pattern = f"user:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                print(f"✅ Invalidated {len(keys)} cache entries for user {user_id}")
            else:
                print(f"ℹ️ No cache entries found for user {user_id}")
                
        except Exception as e:
            print(f"Error invalidating user cache: {e}")
    
    async def invalidate_vector_cache(self, user_id: str) -> None:
        """Invalidate only vector search cache for a user"""
        try:
            pattern = f"user:{user_id}:vector_search:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                print(f"✅ Invalidated {len(keys)} vector cache entries for user {user_id}")
            else:
                print(f"ℹ️ No vector cache entries found for user {user_id}")
                
        except Exception as e:
            print(f"Error invalidating vector cache: {e}")
    
    async def get_cache_stats(self, user_id: str) -> Dict[str, Any]:
        """Get cache statistics for a user"""
        try:
            pattern = f"user:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            
            stats = {
                "total_keys": len(keys),
                "vector_search_keys": len([k for k in keys if "vector_search" in k]),
                "ai_response_keys": len([k for k in keys if "ai_response" in k]),
                "keys": keys[:10]  # Show first 10 keys
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {"error": str(e)}
    
    async def clear_all_cache(self) -> None:
        """Clear all cache (use with caution)"""
        try:
            self.redis_client.flushdb()
            print("✅ Cleared all cache")
        except Exception as e:
            print(f"Error clearing cache: {e}")
    
    async def health_check(self) -> bool:
        """Check if Redis is healthy"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            print(f"Redis health check failed: {e}")
            return False
