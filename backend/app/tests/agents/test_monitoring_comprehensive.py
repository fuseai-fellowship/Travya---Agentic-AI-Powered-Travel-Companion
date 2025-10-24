"""
Comprehensive tests for Agent Monitoring System
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.agents.monitoring import (
    AgentMonitor,
    MetricType,
    AgentPerformance,
    ResourceUsage,
    ErrorEvent,
    track_agent_request,
    track_agent_error,
    track_agent_cost,
    get_agent_health
)

class TestAgentMonitor:
    """Test the AgentMonitor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = AgentMonitor()
        # Clear any existing data
        self.monitor.metrics.clear()
        self.monitor.performance_data.clear()
        self.monitor.error_events.clear()
        self.monitor.resource_usage.clear()
        self.monitor.agent_requests.clear()
        self.monitor.agent_response_times.clear()
        self.monitor.cost_tracking.clear()
    
    def test_track_request(self):
        """Test tracking agent requests"""
        self.monitor.track_request("test_agent", 1.5, success=True)
        
        assert len(self.monitor.agent_requests["test_agent"]) == 1
        assert len(self.monitor.agent_response_times["test_agent"]) == 1
        assert self.monitor.agent_response_times["test_agent"][0] == 1.5
        assert len(self.monitor.metrics) == 1
        
        # Check performance data is updated
        assert "test_agent" in self.monitor.performance_data
        perf = self.monitor.performance_data["test_agent"]
        assert perf.total_requests == 1
        assert perf.successful_requests == 1
        assert perf.failed_requests == 0
        assert perf.average_response_time == 1.5
    
    def test_track_error(self):
        """Test tracking agent errors"""
        self.monitor.track_error(
            agent_name="test_agent",
            error_type="validation_error",
            error_message="Invalid input",
            stack_trace="Traceback...",
            request_id="req_123",
            user_id="user_456"
        )
        
        assert len(self.monitor.error_events) == 1
        error = self.monitor.error_events[0]
        assert error.agent_name == "test_agent"
        assert error.error_type == "validation_error"
        assert error.error_message == "Invalid input"
        assert error.request_id == "req_123"
        assert error.user_id == "user_456"
        
        # Check performance data is updated
        assert "test_agent" in self.monitor.performance_data
        perf = self.monitor.performance_data["test_agent"]
        assert perf.failed_requests == 1
    
    def test_track_cost(self):
        """Test tracking agent costs"""
        self.monitor.track_cost("test_agent", 0.05, "llm_call")
        self.monitor.track_cost("test_agent", 0.02, "api_call")
        
        assert self.monitor.cost_tracking["test_agent_llm_call"] == 0.05
        assert self.monitor.cost_tracking["test_agent_api_call"] == 0.02
        
        # Check metrics
        cost_metrics = [m for m in self.monitor.metrics if m.metric_type == MetricType.COST]
        assert len(cost_metrics) == 2
    
    def test_track_usage(self):
        """Test tracking usage metrics"""
        self.monitor.track_usage(
            agent_name="test_agent",
            usage_type="requests_per_hour",
            value=10.5,
            metadata={"period": "last_hour"}
        )
        
        usage_metrics = [m for m in self.monitor.metrics if m.metric_type == MetricType.USAGE]
        assert len(usage_metrics) == 1
        assert usage_metrics[0].value == 10.5
        assert usage_metrics[0].metadata["period"] == "last_hour"
    
    def test_get_agent_performance(self):
        """Test getting agent performance"""
        # Add some test data
        self.monitor.track_request("test_agent", 1.0, success=True)
        self.monitor.track_request("test_agent", 2.0, success=True)
        self.monitor.track_request("test_agent", 1.5, success=False)
        
        perf = self.monitor.get_agent_performance("test_agent")
        
        assert perf is not None
        assert perf.agent_name == "test_agent"
        assert perf.total_requests == 3
        assert perf.successful_requests == 2
        assert perf.failed_requests == 1
        assert perf.success_rate == (2/3) * 100
        assert perf.error_rate == (1/3) * 100
        assert perf.average_response_time == 1.5
    
    def test_get_all_agents_performance(self):
        """Test getting performance for all agents"""
        # Add data for multiple agents
        self.monitor.track_request("agent1", 1.0, success=True)
        self.monitor.track_request("agent2", 2.0, success=True)
        
        all_perf = self.monitor.get_all_agents_performance()
        
        assert len(all_perf) == 2
        assert "agent1" in all_perf
        assert "agent2" in all_perf
    
    def test_get_error_summary(self):
        """Test getting error summary"""
        # Add some errors
        self.monitor.track_error("agent1", "type1", "Error 1")
        self.monitor.track_error("agent1", "type2", "Error 2")
        self.monitor.track_error("agent2", "type1", "Error 3")
        
        # Add some requests to calculate error rate
        self.monitor.track_request("agent1", 1.0, success=True)
        self.monitor.track_request("agent1", 1.0, success=True)
        
        error_summary = self.monitor.get_error_summary(24)
        
        assert error_summary["total_errors"] == 3
        assert error_summary["error_types"]["type1"] == 2
        assert error_summary["error_types"]["type2"] == 1
        assert "agent1" in error_summary["agents_with_errors"]
        assert "agent2" in error_summary["agents_with_errors"]
        assert error_summary["error_rate"] == (3/5) * 100  # 3 errors out of 5 total requests
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_resource_usage_summary(self, mock_disk, mock_memory, mock_cpu):
        """Test getting resource usage summary"""
        # Mock system resources
        mock_cpu.return_value = 45.5
        mock_memory.return_value = MagicMock(
            percent=67.8,
            used=1024 * 1024 * 1024,  # 1GB
            available=512 * 1024 * 1024  # 512MB
        )
        mock_disk.return_value = MagicMock(percent=23.4)
        
        # Add some resource usage data
        self.monitor.resource_usage.append(ResourceUsage(
            cpu_percent=45.5,
            memory_percent=67.8,
            memory_used_mb=1024,
            memory_available_mb=512,
            disk_usage_percent=23.4,
            network_io_bytes=0,
            timestamp=datetime.now()
        ))
        
        resource_summary = self.monitor.get_resource_usage_summary()
        
        assert resource_summary["cpu_percent"] == 45.5
        assert resource_summary["memory_percent"] == 67.8
        assert resource_summary["memory_used_mb"] == 1024
        assert resource_summary["memory_available_mb"] == 512
        assert resource_summary["disk_usage_percent"] == 23.4
    
    def test_get_cost_summary(self):
        """Test getting cost summary"""
        # Add some costs
        self.monitor.track_cost("agent1", 0.05, "llm_call")
        self.monitor.track_cost("agent1", 0.02, "api_call")
        self.monitor.track_cost("agent2", 0.03, "llm_call")
        
        cost_summary = self.monitor.get_cost_summary()
        
        assert cost_summary["total_cost"] == 0.10
        assert cost_summary["cost_by_agent"]["agent1_llm_call"] == 0.05
        assert cost_summary["cost_by_agent"]["agent1_api_call"] == 0.02
        assert cost_summary["cost_by_agent"]["agent2_llm_call"] == 0.03
        assert cost_summary["cost_breakdown"]["llm_calls"] == 0.08
        assert cost_summary["cost_breakdown"]["api_calls"] == 0.02
    
    def test_get_usage_analytics(self):
        """Test getting usage analytics"""
        # Add some usage data
        self.monitor.track_usage("agent1", "requests_per_hour", 10.0)
        self.monitor.track_usage("agent1", "requests_per_hour", 15.0)
        self.monitor.track_usage("agent2", "requests_per_hour", 8.0)
        
        # Add some costs
        self.monitor.track_cost("agent1", 0.05, "llm_call")
        self.monitor.track_cost("agent2", 0.03, "llm_call")
        
        analytics = self.monitor.get_usage_analytics(24)
        
        assert analytics["period_hours"] == 24
        assert analytics["total_agents"] == 2
        assert "agent1" in analytics["agent_usage"]
        assert "agent2" in analytics["agent_usage"]
        assert analytics["agent_usage"]["agent1"]["total_cost"] == 0.05
        assert analytics["agent_usage"]["agent2"]["total_cost"] == 0.03
    
    def test_get_health_status(self):
        """Test getting health status"""
        # Add some test data
        now = datetime.now()
        
        # Active agent (recent activity)
        self.monitor.track_request("active_agent", 1.0, success=True)
        
        # Inactive agent (old activity)
        old_time = now - timedelta(minutes=10)
        self.monitor.agent_requests["inactive_agent"] = [old_time]
        self.monitor.agent_response_times["inactive_agent"] = [1.0]
        self.monitor.performance_data["inactive_agent"] = AgentPerformance(
            agent_name="inactive_agent",
            total_requests=1,
            successful_requests=1,
            failed_requests=0,
            average_response_time=1.0,
            success_rate=100.0,
            error_rate=0.0,
            last_activity=old_time,
            peak_requests_per_minute=1,
            average_requests_per_hour=1.0
        )
        
        # High error agent
        self.monitor.track_request("error_agent", 1.0, success=True)
        self.monitor.track_request("error_agent", 1.0, success=False)
        self.monitor.track_request("error_agent", 1.0, success=False)
        self.monitor.track_request("error_agent", 1.0, success=False)
        
        health_status = self.monitor.get_health_status()
        
        assert health_status["total_agents"] == 3
        assert "active_agent" in health_status["active_agents"]
        assert "inactive_agent" in health_status["inactive_agents"]
        assert "error_agent" in health_status["high_error_agents"]
        assert health_status["overall_health_score"] < 100  # Should be reduced due to issues

class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Clear global monitor data
        from app.agents.monitoring import monitor
        monitor.metrics.clear()
        monitor.performance_data.clear()
        monitor.error_events.clear()
        monitor.agent_requests.clear()
        monitor.agent_response_times.clear()
        monitor.cost_tracking.clear()
    
    def test_track_agent_request(self):
        """Test track_agent_request convenience function"""
        track_agent_request("test_agent", 1.5, success=True)
        
        from app.agents.monitoring import monitor
        assert len(monitor.agent_requests["test_agent"]) == 1
        assert len(monitor.agent_response_times["test_agent"]) == 1
    
    def test_track_agent_error(self):
        """Test track_agent_error convenience function"""
        track_agent_error("test_agent", "test_error", "Test error message")
        
        from app.agents.monitoring import monitor
        assert len(monitor.error_events) == 1
        assert monitor.error_events[0].agent_name == "test_agent"
        assert monitor.error_events[0].error_type == "test_error"
    
    def test_track_agent_cost(self):
        """Test track_agent_cost convenience function"""
        track_agent_cost("test_agent", 0.05, "llm_call")
        
        from app.agents.monitoring import monitor
        assert monitor.cost_tracking["test_agent_llm_call"] == 0.05
    
    def test_get_agent_health(self):
        """Test get_agent_health convenience function"""
        health = get_agent_health()
        
        assert "overall_health_score" in health
        assert "status" in health
        assert "active_agents" in health
        assert "inactive_agents" in health
        assert "total_agents" in health

class TestMonitoringIntegration:
    """Test monitoring system integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = AgentMonitor()
        # Clear any existing data
        self.monitor.metrics.clear()
        self.monitor.performance_data.clear()
        self.monitor.error_events.clear()
        self.monitor.agent_requests.clear()
        self.monitor.agent_response_times.clear()
        self.monitor.cost_tracking.clear()
    
    def test_complete_monitoring_workflow(self):
        """Test complete monitoring workflow"""
        # Track various metrics
        self.monitor.track_request("agent1", 1.0, success=True)
        self.monitor.track_request("agent1", 1.5, success=True)
        self.monitor.track_request("agent1", 2.0, success=False)
        
        self.monitor.track_error("agent1", "validation_error", "Invalid input")
        
        self.monitor.track_cost("agent1", 0.05, "llm_call")
        self.monitor.track_cost("agent1", 0.02, "api_call")
        
        self.monitor.track_usage("agent1", "requests_per_hour", 10.0)
        
        # Get performance data
        perf = self.monitor.get_agent_performance("agent1")
        assert perf.total_requests == 3
        assert perf.successful_requests == 2
        assert perf.failed_requests == 1
        
        # Get error summary
        error_summary = self.monitor.get_error_summary(24)
        assert error_summary["total_errors"] == 1
        
        # Get cost summary
        cost_summary = self.monitor.get_cost_summary()
        assert cost_summary["total_cost"] == 0.07
        
        # Get health status
        health = self.monitor.get_health_status()
        assert health["total_agents"] == 1
    
    def test_metric_cleanup(self):
        """Test that old metrics are cleaned up"""
        # Add old metrics
        old_time = datetime.now() - timedelta(hours=25)
        old_metric = MagicMock()
        old_metric.timestamp = old_time
        self.monitor.metrics.append(old_metric)
        
        # Add recent metrics
        recent_time = datetime.now() - timedelta(hours=1)
        recent_metric = MagicMock()
        recent_metric.timestamp = recent_time
        self.monitor.metrics.append(recent_metric)
        
        # Simulate cleanup (normally done by background task)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.monitor.metrics = [m for m in self.monitor.metrics if m.timestamp > cutoff_time]
        
        # Only recent metric should remain
        assert len(self.monitor.metrics) == 1
    
    def test_performance_calculation(self):
        """Test performance calculation accuracy"""
        # Add multiple requests with known values
        response_times = [1.0, 2.0, 3.0, 4.0, 5.0]
        for i, rt in enumerate(response_times):
            self.monitor.track_request("test_agent", rt, success=(i < 4))  # 4 success, 1 failure
        
        perf = self.monitor.get_agent_performance("test_agent")
        
        assert perf.total_requests == 5
        assert perf.successful_requests == 4
        assert perf.failed_requests == 1
        assert perf.success_rate == 80.0
        assert perf.error_rate == 20.0
        assert perf.average_response_time == 3.0  # (1+2+3+4+5)/5
    
    def test_error_tracking(self):
        """Test error tracking and categorization"""
        # Add different types of errors
        self.monitor.track_error("agent1", "validation_error", "Invalid input")
        self.monitor.track_error("agent1", "network_error", "Connection timeout")
        self.monitor.track_error("agent2", "validation_error", "Missing field")
        
        error_summary = self.monitor.get_error_summary(24)
        
        assert error_summary["total_errors"] == 3
        assert error_summary["error_types"]["validation_error"] == 2
        assert error_summary["error_types"]["network_error"] == 1
        assert len(error_summary["agents_with_errors"]) == 2

if __name__ == "__main__":
    pytest.main([__file__])
