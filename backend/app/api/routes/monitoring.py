"""
Agent Monitoring API Routes

Provides endpoints for:
- Real-time agent performance monitoring
- Resource usage tracking
- Error monitoring and alerting
- Usage analytics
- Health status checks
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.agents.monitoring import (
    monitor,
    track_agent_request,
    track_agent_error,
    track_agent_cost,
    get_agent_health
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Request/Response Models
class PerformanceResponse(BaseModel):
    agent_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    success_rate: float
    error_rate: float
    last_activity: datetime
    peak_requests_per_minute: int
    average_requests_per_hour: float

class ErrorSummaryResponse(BaseModel):
    total_errors: int
    error_rate: float
    error_types: Dict[str, int]
    agents_with_errors: List[str]
    recent_errors: List[Dict[str, Any]]

class ResourceUsageResponse(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    timestamp: str

class CostSummaryResponse(BaseModel):
    total_cost: float
    cost_by_agent: Dict[str, float]
    cost_breakdown: Dict[str, float]

class UsageAnalyticsResponse(BaseModel):
    period_hours: int
    total_agents: int
    agent_usage: Dict[str, Any]
    summary: Dict[str, Any]

class HealthStatusResponse(BaseModel):
    overall_health_score: int
    status: str
    active_agents: List[str]
    inactive_agents: List[str]
    high_error_agents: List[str]
    resource_issues: List[str]
    total_agents: int
    timestamp: str

@router.get("/performance", response_model=List[PerformanceResponse])
async def get_all_agents_performance(
    current_user: CurrentUser = None
):
    """Get performance metrics for all agents"""
    try:
        performance_data = monitor.get_all_agents_performance()
        
        response_list = []
        for agent_name, perf in performance_data.items():
            response_list.append(PerformanceResponse(
                agent_name=perf.agent_name,
                total_requests=perf.total_requests,
                successful_requests=perf.successful_requests,
                failed_requests=perf.failed_requests,
                average_response_time=perf.average_response_time,
                success_rate=perf.success_rate,
                error_rate=perf.error_rate,
                last_activity=perf.last_activity,
                peak_requests_per_minute=perf.peak_requests_per_minute,
                average_requests_per_hour=perf.average_requests_per_hour
            ))
        
        return response_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/performance/{agent_name}", response_model=PerformanceResponse)
async def get_agent_performance(
    agent_name: str,
    current_user: CurrentUser = None
):
    """Get performance metrics for a specific agent"""
    try:
        performance = monitor.get_agent_performance(agent_name)
        
        if not performance:
            raise HTTPException(status_code=404, detail=f"No performance data found for agent: {agent_name}")
        
        return PerformanceResponse(
            agent_name=performance.agent_name,
            total_requests=performance.total_requests,
            successful_requests=performance.successful_requests,
            failed_requests=performance.failed_requests,
            average_response_time=performance.average_response_time,
            success_rate=performance.success_rate,
            error_rate=performance.error_rate,
            last_activity=performance.last_activity,
            peak_requests_per_minute=performance.peak_requests_per_minute,
            average_requests_per_hour=performance.average_requests_per_hour
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/errors", response_model=ErrorSummaryResponse)
async def get_error_summary(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back for errors"),
    current_user: CurrentUser = None
):
    """Get error summary for the specified time period"""
    try:
        error_summary = monitor.get_error_summary(hours)
        return ErrorSummaryResponse(**error_summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get error summary: {str(e)}")

@router.get("/resources", response_model=ResourceUsageResponse)
async def get_resource_usage(
    current_user: CurrentUser = None
):
    """Get current system resource usage"""
    try:
        resource_usage = monitor.get_resource_usage_summary()
        return ResourceUsageResponse(**resource_usage)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resource usage: {str(e)}")

@router.get("/costs", response_model=CostSummaryResponse)
async def get_cost_summary(
    current_user: CurrentUser = None
):
    """Get cost summary for all agents"""
    try:
        cost_summary = monitor.get_cost_summary()
        return CostSummaryResponse(**cost_summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost summary: {str(e)}")

@router.get("/analytics", response_model=UsageAnalyticsResponse)
async def get_usage_analytics(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back for analytics"),
    current_user: CurrentUser = None
):
    """Get usage analytics for the specified time period"""
    try:
        analytics = monitor.get_usage_analytics(hours)
        return UsageAnalyticsResponse(**analytics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage analytics: {str(e)}")

@router.get("/health", response_model=HealthStatusResponse)
async def get_health_status(
    current_user: CurrentUser = None
):
    """Get overall health status of the agent system"""
    try:
        health_status = get_agent_health()
        return HealthStatusResponse(**health_status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")

@router.get("/metrics", response_model=Dict[str, Any])
async def get_all_metrics(
    current_user: CurrentUser = None
):
    """Get comprehensive metrics dashboard data"""
    try:
        # Get all metrics
        performance_data = monitor.get_all_agents_performance()
        error_summary = monitor.get_error_summary(24)
        resource_usage = monitor.get_resource_usage_summary()
        cost_summary = monitor.get_cost_summary()
        usage_analytics = monitor.get_usage_analytics(24)
        health_status = get_agent_health()
        
        return {
            "performance": {
                agent_name: {
                    "total_requests": perf.total_requests,
                    "success_rate": perf.success_rate,
                    "error_rate": perf.error_rate,
                    "average_response_time": perf.average_response_time,
                    "last_activity": perf.last_activity.isoformat()
                }
                for agent_name, perf in performance_data.items()
            },
            "errors": error_summary,
            "resources": resource_usage,
            "costs": cost_summary,
            "analytics": usage_analytics,
            "health": health_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@router.post("/track/request", response_model=Dict[str, str])
async def track_request(
    agent_name: str,
    response_time: float,
    success: bool = True,
    current_user: CurrentUser = None
):
    """Track a request to an agent (for testing/monitoring)"""
    try:
        track_agent_request(agent_name, response_time, success)
        return {"message": "Request tracked successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track request: {str(e)}")

@router.post("/track/error", response_model=Dict[str, str])
async def track_error(
    agent_name: str,
    error_type: str,
    error_message: str,
    stack_trace: str = "",
    request_id: str = None,
    current_user: CurrentUser = None
):
    """Track an error event (for testing/monitoring)"""
    try:
        track_agent_error(agent_name, error_type, error_message, stack_trace, request_id)
        return {"message": "Error tracked successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track error: {str(e)}")

@router.post("/track/cost", response_model=Dict[str, str])
async def track_cost(
    agent_name: str,
    cost: float,
    operation: str = "llm_call",
    current_user: CurrentUser = None
):
    """Track cost for agent operations (for testing/monitoring)"""
    try:
        track_agent_cost(agent_name, cost, operation)
        return {"message": "Cost tracked successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track cost: {str(e)}")

@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_alerts(
    current_user: CurrentUser = None
):
    """Get current alerts and warnings"""
    try:
        alerts = []
        
        # Check health status for alerts
        health_status = get_agent_health()
        
        if health_status["status"] == "critical":
            alerts.append({
                "type": "critical",
                "message": "System health is critical",
                "timestamp": datetime.now().isoformat(),
                "details": health_status
            })
        elif health_status["status"] == "degraded":
            alerts.append({
                "type": "warning",
                "message": "System health is degraded",
                "timestamp": datetime.now().isoformat(),
                "details": health_status
            })
        
        # Check for high error rates
        error_summary = monitor.get_error_summary(1)  # Last hour
        if error_summary["error_rate"] > 5.0:  # More than 5% error rate
            alerts.append({
                "type": "warning",
                "message": f"High error rate detected: {error_summary['error_rate']}%",
                "timestamp": datetime.now().isoformat(),
                "details": error_summary
            })
        
        # Check resource usage
        resource_usage = monitor.get_resource_usage_summary()
        if resource_usage["cpu_percent"] > 80:
            alerts.append({
                "type": "warning",
                "message": f"High CPU usage: {resource_usage['cpu_percent']}%",
                "timestamp": datetime.now().isoformat(),
                "details": resource_usage
            })
        
        if resource_usage["memory_percent"] > 90:
            alerts.append({
                "type": "warning",
                "message": f"High memory usage: {resource_usage['memory_percent']}%",
                "timestamp": datetime.now().isoformat(),
                "details": resource_usage
            })
        
        # Check for inactive agents
        if health_status["inactive_agents"]:
            alerts.append({
                "type": "info",
                "message": f"Inactive agents detected: {', '.join(health_status['inactive_agents'])}",
                "timestamp": datetime.now().isoformat(),
                "details": {"inactive_agents": health_status["inactive_agents"]}
            })
        
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")
