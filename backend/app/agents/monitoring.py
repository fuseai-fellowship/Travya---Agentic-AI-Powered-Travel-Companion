"""
Agent Monitoring and Analytics System

This module provides comprehensive monitoring capabilities for AI agents including:
- Real-time performance tracking
- Resource usage monitoring
- Error tracking and alerting
- Usage analytics
- Cost tracking
- Performance dashboards
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

from app.core.config import settings
from app.agents.sessions import memory_manager

logger = logging.getLogger(__name__)

class MetricType(Enum):
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    ERROR = "error"
    USAGE = "usage"
    COST = "cost"

@dataclass
class AgentMetric:
    """Individual metric for an agent"""
    agent_name: str
    metric_type: MetricType
    metric_name: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class AgentPerformance:
    """Performance metrics for an agent"""
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

@dataclass
class ResourceUsage:
    """Resource usage metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    network_io_bytes: int
    timestamp: datetime

@dataclass
class ErrorEvent:
    """Error event tracking"""
    agent_name: str
    error_type: str
    error_message: str
    stack_trace: str
    timestamp: datetime
    request_id: Optional[str] = None
    user_id: Optional[str] = None

class AgentMonitor:
    """Main monitoring class for AI agents"""
    
    def __init__(self):
        self.metrics: List[AgentMetric] = []
        self.performance_data: Dict[str, AgentPerformance] = {}
        self.error_events: List[ErrorEvent] = []
        self.resource_usage: List[ResourceUsage] = []
        self.agent_requests: Dict[str, List[datetime]] = {}
        self.agent_response_times: Dict[str, List[float]] = {}
        self.cost_tracking: Dict[str, float] = {}
        
        # Initialize monitoring task (start manually when needed)
        self._monitoring_task = None
        # Don't start monitoring automatically to avoid event loop issues
    
    def _start_monitoring(self):
        """Start background monitoring tasks"""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._monitor_resources())
    
    async def _monitor_resources(self):
        """Background task to monitor system resources"""
        while True:
            try:
                # Monitor system resources
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                resource_usage = ResourceUsage(
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / (1024 * 1024),
                    memory_available_mb=memory.available / (1024 * 1024),
                    disk_usage_percent=disk.percent,
                    network_io_bytes=0,  # Would need to track network I/O
                    timestamp=datetime.now()
                )
                
                self.resource_usage.append(resource_usage)
                
                # Keep only last 1000 resource measurements
                if len(self.resource_usage) > 1000:
                    self.resource_usage = self.resource_usage[-1000:]
                
                # Clean up old metrics (keep last 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
                self.error_events = [e for e in self.error_events if e.timestamp > cutoff_time]
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(60)
    
    def track_request(self, agent_name: str, response_time: float, success: bool = True):
        """Track a request to an agent"""
        now = datetime.now()
        
        # Track request timestamp
        if agent_name not in self.agent_requests:
            self.agent_requests[agent_name] = []
        self.agent_requests[agent_name].append(now)
        
        # Track response time
        if agent_name not in self.agent_response_times:
            self.agent_response_times[agent_name] = []
        self.agent_response_times[agent_name].append(response_time)
        
        # Create performance metric
        metric = AgentMetric(
            agent_name=agent_name,
            metric_type=MetricType.PERFORMANCE,
            metric_name="response_time",
            value=response_time,
            timestamp=now,
            metadata={"success": success}
        )
        self.metrics.append(metric)
        
        # Update performance data
        self._update_performance_data(agent_name)
    
    def track_error(self, agent_name: str, error_type: str, error_message: str, 
                   stack_trace: str = "", request_id: str = None, user_id: str = None):
        """Track an error event"""
        error_event = ErrorEvent(
            agent_name=agent_name,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            timestamp=datetime.now(),
            request_id=request_id,
            user_id=user_id
        )
        
        self.error_events.append(error_event)
        
        # Create error metric
        metric = AgentMetric(
            agent_name=agent_name,
            metric_type=MetricType.ERROR,
            metric_name="error_count",
            value=1.0,
            timestamp=datetime.now(),
            metadata={
                "error_type": error_type,
                "error_message": error_message
            }
        )
        self.metrics.append(metric)
        
        # Update performance data
        self._update_performance_data(agent_name)
    
    def track_cost(self, agent_name: str, cost: float, operation: str = "llm_call"):
        """Track cost for agent operations"""
        cost_key = f"{agent_name}_{operation}"
        if cost_key not in self.cost_tracking:
            self.cost_tracking[cost_key] = 0.0
        self.cost_tracking[cost_key] += cost
        
        # Create cost metric
        metric = AgentMetric(
            agent_name=agent_name,
            metric_type=MetricType.COST,
            metric_name="operation_cost",
            value=cost,
            timestamp=datetime.now(),
            metadata={"operation": operation}
        )
        self.metrics.append(metric)
    
    def track_usage(self, agent_name: str, usage_type: str, value: float, metadata: Dict[str, Any] = None):
        """Track usage metrics for an agent"""
        metric = AgentMetric(
            agent_name=agent_name,
            metric_type=MetricType.USAGE,
            metric_name=usage_type,
            value=value,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.metrics.append(metric)
    
    def _update_performance_data(self, agent_name: str):
        """Update performance data for an agent"""
        now = datetime.now()
        
        # Get requests from last hour
        hour_ago = now - timedelta(hours=1)
        recent_requests = [
            req_time for req_time in self.agent_requests.get(agent_name, [])
            if req_time > hour_ago
        ]
        
        # Get response times
        response_times = self.agent_response_times.get(agent_name, [])
        
        # Get errors from last hour
        recent_errors = [
            error for error in self.error_events
            if error.agent_name == agent_name and error.timestamp > hour_ago
        ]
        
        # Calculate metrics
        total_requests = len(recent_requests)
        successful_requests = total_requests - len(recent_errors)
        failed_requests = len(recent_errors)
        
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        average_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate peak requests per minute
        if recent_requests:
            minute_counts = {}
            for req_time in recent_requests:
                minute_key = req_time.replace(second=0, microsecond=0)
                minute_counts[minute_key] = minute_counts.get(minute_key, 0) + 1
            peak_requests_per_minute = max(minute_counts.values()) if minute_counts else 0
        else:
            peak_requests_per_minute = 0
        
        # Calculate average requests per hour
        hours = max(1, (now - min(recent_requests)).total_seconds() / 3600) if recent_requests else 1
        average_requests_per_hour = total_requests / hours
        
        # Update performance data
        self.performance_data[agent_name] = AgentPerformance(
            agent_name=agent_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=average_response_time,
            success_rate=success_rate,
            error_rate=error_rate,
            last_activity=max(recent_requests) if recent_requests else now,
            peak_requests_per_minute=peak_requests_per_minute,
            average_requests_per_hour=average_requests_per_hour
        )
    
    def get_agent_performance(self, agent_name: str) -> Optional[AgentPerformance]:
        """Get performance data for a specific agent"""
        return self.performance_data.get(agent_name)
    
    def get_all_agents_performance(self) -> Dict[str, AgentPerformance]:
        """Get performance data for all agents"""
        return self.performance_data.copy()
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_events if e.timestamp > cutoff_time]
        
        if not recent_errors:
            return {
                "total_errors": 0,
                "error_rate": 0.0,
                "error_types": {},
                "agents_with_errors": [],
                "recent_errors": []
            }
        
        # Count errors by type
        error_types = {}
        agents_with_errors = set()
        
        for error in recent_errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            agents_with_errors.add(error.agent_name)
        
        # Calculate error rate
        total_requests = sum(perf.total_requests for perf in self.performance_data.values())
        error_rate = (len(recent_errors) / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_errors": len(recent_errors),
            "error_rate": round(error_rate, 2),
            "error_types": error_types,
            "agents_with_errors": list(agents_with_errors),
            "recent_errors": [
                {
                    "agent_name": error.agent_name,
                    "error_type": error.error_type,
                    "error_message": error.error_message,
                    "timestamp": error.timestamp.isoformat()
                }
                for error in recent_errors[-10:]  # Last 10 errors
            ]
        }
    
    def get_resource_usage_summary(self) -> Dict[str, Any]:
        """Get current resource usage summary"""
        if not self.resource_usage:
            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "memory_used_mb": 0.0,
                "memory_available_mb": 0.0,
                "disk_usage_percent": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        
        latest = self.resource_usage[-1]
        return {
            "cpu_percent": latest.cpu_percent,
            "memory_percent": latest.memory_percent,
            "memory_used_mb": latest.memory_used_mb,
            "memory_available_mb": latest.memory_available_mb,
            "disk_usage_percent": latest.disk_usage_percent,
            "timestamp": latest.timestamp.isoformat()
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for all agents"""
        total_cost = sum(self.cost_tracking.values())
        
        return {
            "total_cost": round(total_cost, 4),
            "cost_by_agent": {
                agent: round(cost, 4) 
                for agent, cost in self.cost_tracking.items()
            },
            "cost_breakdown": {
                "llm_calls": sum(cost for key, cost in self.cost_tracking.items() if "llm_call" in key),
                "api_calls": sum(cost for key, cost in self.cost_tracking.items() if "api_call" in key),
                "storage": sum(cost for key, cost in self.cost_tracking.items() if "storage" in key),
                "other": sum(cost for key, cost in self.cost_tracking.items() if not any(x in key for x in ["llm_call", "api_call", "storage"]))
            }
        }
    
    def get_usage_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get usage analytics for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter metrics by time period
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
        
        # Group by agent
        agent_usage = {}
        for metric in recent_metrics:
            if metric.agent_name not in agent_usage:
                agent_usage[metric.agent_name] = {
                    "total_requests": 0,
                    "total_cost": 0.0,
                    "metrics": {}
                }
            
            if metric.metric_type == MetricType.USAGE:
                agent_usage[metric.agent_name]["total_requests"] += int(metric.value)
            elif metric.metric_type == MetricType.COST:
                agent_usage[metric.agent_name]["total_cost"] += metric.value
            
            # Track specific metrics
            metric_name = metric.metric_name
            if metric_name not in agent_usage[metric.agent_name]["metrics"]:
                agent_usage[metric.agent_name]["metrics"][metric_name] = []
            agent_usage[metric.agent_name]["metrics"][metric_name].append(metric.value)
        
        # Calculate averages
        for agent_data in agent_usage.values():
            for metric_name, values in agent_data["metrics"].items():
                if values:
                    agent_data["metrics"][f"{metric_name}_avg"] = sum(values) / len(values)
                    agent_data["metrics"][f"{metric_name}_max"] = max(values)
                    agent_data["metrics"][f"{metric_name}_min"] = min(values)
        
        return {
            "period_hours": hours,
            "total_agents": len(agent_usage),
            "agent_usage": agent_usage,
            "summary": {
                "total_requests": sum(data["total_requests"] for data in agent_usage.values()),
                "total_cost": sum(data["total_cost"] for data in agent_usage.values()),
                "most_active_agent": max(agent_usage.items(), key=lambda x: x[1]["total_requests"])[0] if agent_usage else None
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of the agent system"""
        now = datetime.now()
        
        # Check if agents are responding
        active_agents = []
        inactive_agents = []
        
        for agent_name, perf in self.performance_data.items():
            if perf.last_activity > now - timedelta(minutes=5):
                active_agents.append(agent_name)
            else:
                inactive_agents.append(agent_name)
        
        # Check error rates
        high_error_agents = [
            agent_name for agent_name, perf in self.performance_data.items()
            if perf.error_rate > 10.0  # More than 10% error rate
        ]
        
        # Check resource usage
        resource_status = self.get_resource_usage_summary()
        resource_issues = []
        
        if resource_status["cpu_percent"] > 80:
            resource_issues.append("High CPU usage")
        if resource_status["memory_percent"] > 90:
            resource_issues.append("High memory usage")
        if resource_status["disk_usage_percent"] > 90:
            resource_issues.append("High disk usage")
        
        # Overall health score
        health_score = 100
        if inactive_agents:
            health_score -= len(inactive_agents) * 20
        if high_error_agents:
            health_score -= len(high_error_agents) * 15
        if resource_issues:
            health_score -= len(resource_issues) * 10
        
        health_score = max(0, health_score)
        
        return {
            "overall_health_score": health_score,
            "status": "healthy" if health_score > 80 else "degraded" if health_score > 50 else "critical",
            "active_agents": active_agents,
            "inactive_agents": inactive_agents,
            "high_error_agents": high_error_agents,
            "resource_issues": resource_issues,
            "total_agents": len(self.performance_data),
            "timestamp": now.isoformat()
        }

# Global monitor instance
monitor = AgentMonitor()

# Convenience functions
def track_agent_request(agent_name: str, response_time: float, success: bool = True):
    """Convenience function to track agent request"""
    monitor.track_request(agent_name, response_time, success)

def track_agent_error(agent_name: str, error_type: str, error_message: str, 
                     stack_trace: str = "", request_id: str = None, user_id: str = None):
    """Convenience function to track agent error"""
    monitor.track_error(agent_name, error_type, error_message, stack_trace, request_id, user_id)

def track_agent_cost(agent_name: str, cost: float, operation: str = "llm_call"):
    """Convenience function to track agent cost"""
    monitor.track_cost(agent_name, cost, operation)

def get_agent_health() -> Dict[str, Any]:
    """Convenience function to get agent health status"""
    return monitor.get_health_status()
