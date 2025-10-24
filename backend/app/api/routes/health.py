from datetime import datetime
from typing import Dict, Any
import asyncio
import httpx
import redis
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import SessionDep
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def basic_health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check(session: SessionDep) -> Dict[str, Any]:
    """Detailed health check with all dependencies."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "services": {}
    }
    
    # Check database
    try:
        from sqlalchemy import text
        start_time = datetime.utcnow()
        result = session.execute(text("SELECT 1"))
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        health_status["services"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(response_time, 2)
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        start_time = datetime.utcnow()
        redis_client.ping()
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        health_status["services"]["redis"] = {
            "status": "healthy",
            "response_time_ms": round(response_time, 2)
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check external APIs (non-blocking)
    external_apis = {}
    
    # Check Google Maps API
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start_time = datetime.utcnow()
            response = await client.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params={"query": "test", "key": settings.GOOGLE_MAPS_API_KEY}
            )
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                external_apis["google_maps"] = {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2)
                }
            else:
                external_apis["google_maps"] = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        external_apis["google_maps"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Amadeus API
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start_time = datetime.utcnow()
            response = await client.get(
                "https://test.api.amadeus.com/v1/security/oauth2/token",
                params={
                    "grant_type": "client_credentials",
                    "client_id": settings.AMADEUS_CLIENT_ID,
                    "client_secret": settings.AMADEUS_CLIENT_SECRET
                }
            )
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if response.status_code in [200, 400]:  # 400 is expected for invalid credentials
                external_apis["amadeus"] = {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2)
                }
            else:
                external_apis["amadeus"] = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        external_apis["amadeus"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    health_status["services"]["external_apis"] = external_apis
    
    # Check AI services
    try:
        from app.core.llm import call_llm
        start_time = datetime.utcnow()
        # Simple test call (call_llm is not async)
        test_response = call_llm("Test health check")
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        health_status["services"]["ai_llm"] = {
            "status": "healthy",
            "response_time_ms": round(response_time, 2)
        }
    except Exception as e:
        health_status["services"]["ai_llm"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/ready")
async def readiness_check(session: SessionDep) -> Dict[str, Any]:
    """Kubernetes readiness probe endpoint."""
    try:
        # Check critical dependencies
        from sqlalchemy import text
        await session.execute(text("SELECT 1"))
        
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Kubernetes liveness probe endpoint."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
