"""
Comprehensive tests for Agent Evaluation System
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.agents.evaluation import (
    AgentEvaluator,
    EvaluationType,
    EvaluationStatus,
    EvaluationCriteria,
    EvaluationResult,
    HumanFeedback,
    evaluate_agent_response,
    collect_feedback,
    get_agent_performance
)

class TestAgentEvaluator:
    """Test the AgentEvaluator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.evaluator = AgentEvaluator()
    
    @pytest.mark.asyncio
    async def test_llm_judge_evaluation(self):
        """Test LLM-as-a-judge evaluation"""
        with patch('app.agents.evaluation.call_llm') as mock_llm:
            # Mock LLM responses
            mock_llm.side_effect = [
                "8",  # accuracy
                "7",  # relevance
                "9",  # helpfulness
                "6",  # creativity
                "8.5 - This is a good response that addresses the query well"  # overall
            ]
            
            result = await self.evaluator.evaluate_with_llm_judge(
                agent_name="test_agent",
                query="What is the best time to visit Japan?",
                response="Spring (March-May) is the best time to visit Japan for cherry blossoms and mild weather."
            )
            
            assert result.agent_name == "test_agent"
            assert result.evaluation_type == EvaluationType.LLM_AS_JUDGE
            assert result.criteria.accuracy == 8.0
            assert result.criteria.relevance == 7.0
            assert result.criteria.helpfulness == 9.0
            assert result.criteria.creativity == 6.0
            assert result.overall_score == 8.5
            assert "good response" in result.feedback.lower()
    
    @pytest.mark.asyncio
    async def test_human_feedback_collection(self):
        """Test human feedback collection"""
        feedback = await self.evaluator.collect_human_feedback(
            user_id="test_user",
            agent_name="test_agent",
            query="What is the best time to visit Japan?",
            response="Spring (March-May) is the best time to visit Japan for cherry blossoms and mild weather.",
            rating=4,
            feedback_text="Good response, but could be more detailed about specific months."
        )
        
        assert feedback.user_id == "test_user"
        assert feedback.agent_name == "test_agent"
        assert feedback.rating == 4
        assert "more detailed" in feedback.feedback_text
        assert len(self.evaluator.human_feedback) == 1
    
    @pytest.mark.asyncio
    async def test_human_in_loop_evaluation(self):
        """Test human-in-the-loop evaluation"""
        with patch('app.agents.evaluation.call_llm') as mock_llm:
            mock_llm.return_value = "7 - Decent response"
            
            pending_eval, human_feedback = await self.evaluator.evaluate_with_human_in_loop(
                user_id="test_user",
                agent_name="test_agent",
                query="What is the best time to visit Japan?",
                response="Spring is good for cherry blossoms."
            )
            
            assert pending_eval.evaluation_type == EvaluationType.HUMAN_IN_LOOP
            assert pending_eval.overall_score == 0.0  # Pending human feedback
            assert human_feedback is None
    
    @pytest.mark.asyncio
    async def test_complete_human_evaluation(self):
        """Test completing human-in-the-loop evaluation"""
        # First create a pending evaluation
        with patch('app.agents.evaluation.call_llm') as mock_llm:
            mock_llm.return_value = "7 - Decent response"
            
            pending_eval, _ = await self.evaluator.evaluate_with_human_in_loop(
                user_id="test_user",
                agent_name="test_agent",
                query="What is the best time to visit Japan?",
                response="Spring is good for cherry blossoms."
            )
            
            # Add to evaluation history
            self.evaluator.evaluation_history.append(pending_eval)
        
        # Create human feedback
        human_feedback = HumanFeedback(
            user_id="test_user",
            agent_name="test_agent",
            query="What is the best time to visit Japan?",
            response="Spring is good for cherry blossoms.",
            rating=4,
            feedback_text="Good but brief",
            timestamp=datetime.now()
        )
        
        # Complete the evaluation
        completed_eval = await self.evaluator.complete_human_evaluation(
            pending_eval.evaluation_id,
            human_feedback
        )
        
        assert completed_eval.evaluation_type == EvaluationType.HUMAN_IN_LOOP
        assert completed_eval.overall_score > 0
        assert "Good but brief" in completed_eval.feedback
    
    def test_get_agent_performance_summary(self):
        """Test getting agent performance summary"""
        # Add some mock evaluations
        for i in range(5):
            eval_result = EvaluationResult(
                evaluation_id=f"eval_{i}",
                agent_name="test_agent",
                evaluation_type=EvaluationType.LLM_AS_JUDGE,
                criteria=EvaluationCriteria(accuracy=8.0, relevance=7.0),
                overall_score=7.5 + i * 0.1,
                feedback=f"Test feedback {i}",
                timestamp=datetime.now() - timedelta(days=i),
                metadata={}
            )
            self.evaluator.evaluation_history.append(eval_result)
        
        performance = self.evaluator.get_agent_performance_summary("test_agent", 30)
        
        assert performance["agent_name"] == "test_agent"
        assert performance["total_evaluations"] == 5
        assert performance["average_score"] > 7.0
        assert performance["performance_trend"] in ["improving", "declining", "stable"]
    
    def test_extract_score(self):
        """Test score extraction from LLM response"""
        # Test various response formats
        assert self.evaluator._extract_score("8") == 8.0
        assert self.evaluator._extract_score("Score: 7.5") == 7.5
        assert self.evaluator._extract_score("I rate this 9 out of 10") == 9.0
        assert self.evaluator._extract_score("No score here") == 5.0  # Default
        assert self.evaluator._extract_score("15") == 10.0  # Clamped to max
        assert self.evaluator._extract_score("0") == 1.0  # Clamped to min
    
    def test_extract_feedback(self):
        """Test feedback extraction from LLM response"""
        response = "8.5 - This is a good response that addresses the query well"
        feedback = self.evaluator._extract_feedback(response)
        assert "good response" in feedback.lower()
        assert "8.5" not in feedback  # Score should be removed
    
    @pytest.mark.asyncio
    async def test_ab_test(self):
        """Test A/B testing functionality"""
        test_results = await self.evaluator.run_a_b_test(
            query="What is the best time to visit Japan?",
            agent_a="agent_v1",
            agent_b="agent_v2",
            test_duration_hours=1
        )
        
        assert test_results["test_id"].startswith("ab_test_")
        assert test_results["agent_a"] == "agent_v1"
        assert test_results["agent_b"] == "agent_v2"
        assert test_results["status"] == "running"

class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.mark.asyncio
    async def test_evaluate_agent_response(self):
        """Test evaluate_agent_response convenience function"""
        with patch('app.agents.evaluation.call_llm') as mock_llm:
            mock_llm.return_value = "8 - Good response"
            
            result = await evaluate_agent_response(
                agent_name="test_agent",
                query="Test query",
                response="Test response",
                evaluation_type=EvaluationType.LLM_AS_JUDGE
            )
            
            assert result.agent_name == "test_agent"
            assert result.evaluation_type == EvaluationType.LLM_AS_JUDGE
    
    @pytest.mark.asyncio
    async def test_collect_feedback(self):
        """Test collect_feedback convenience function"""
        with patch('app.agents.evaluation.memory_manager') as mock_memory:
            feedback = await collect_feedback(
                user_id="test_user",
                agent_name="test_agent",
                query="Test query",
                response="Test response",
                rating=4,
                feedback_text="Good response"
            )
            
            assert feedback.user_id == "test_user"
            assert feedback.rating == 4
            mock_memory.store_user_feedback.assert_called_once()
    
    def test_get_agent_performance(self):
        """Test get_agent_performance convenience function"""
        # This will use the global evaluator instance
        performance = get_agent_performance("test_agent", 30)
        assert "agent_name" in performance
        assert "total_evaluations" in performance

class TestEvaluationIntegration:
    """Test evaluation system integration"""
    
    @pytest.mark.asyncio
    async def test_evaluation_workflow(self):
        """Test complete evaluation workflow"""
        evaluator = AgentEvaluator()
        
        # Step 1: LLM evaluation
        with patch('app.agents.evaluation.call_llm') as mock_llm:
            mock_llm.side_effect = ["8", "7", "9", "6", "8 - Good response"]
            
            llm_result = await evaluator.evaluate_with_llm_judge(
                agent_name="test_agent",
                query="What is the best time to visit Japan?",
                response="Spring (March-May) is the best time to visit Japan for cherry blossoms and mild weather."
            )
            
            assert llm_result.overall_score == 8.0
        
        # Step 2: Human feedback
        human_feedback = await evaluator.collect_human_feedback(
            user_id="test_user",
            agent_name="test_agent",
            query="What is the best time to visit Japan?",
            response="Spring (March-May) is the best time to visit Japan for cherry blossoms and mild weather.",
            rating=4,
            feedback_text="Good response, very helpful"
        )
        
        assert human_feedback.rating == 4
        
        # Step 3: Performance summary
        performance = evaluator.get_agent_performance_summary("test_agent", 30)
        assert performance["total_evaluations"] >= 1
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in evaluation"""
        evaluator = AgentEvaluator()
        
        # Test with LLM error
        with patch('app.agents.evaluation.call_llm', side_effect=Exception("LLM Error")):
            result = await evaluator.evaluate_with_llm_judge(
                agent_name="test_agent",
                query="Test query",
                response="Test response"
            )
            
            # Should still return a result with default scores
            assert result.agent_name == "test_agent"
            assert result.overall_score >= 0
    
    def test_evaluation_criteria(self):
        """Test EvaluationCriteria dataclass"""
        criteria = EvaluationCriteria(
            accuracy=8.0,
            relevance=7.0,
            helpfulness=9.0,
            creativity=6.0
        )
        
        assert criteria.accuracy == 8.0
        assert criteria.relevance == 7.0
        assert criteria.helpfulness == 9.0
        assert criteria.creativity == 6.0
        assert criteria.efficiency == 0.0  # Default value
    
    def test_human_feedback_dataclass(self):
        """Test HumanFeedback dataclass"""
        feedback = HumanFeedback(
            user_id="test_user",
            agent_name="test_agent",
            query="Test query",
            response="Test response",
            rating=4,
            feedback_text="Good response",
            timestamp=datetime.now()
        )
        
        assert feedback.user_id == "test_user"
        assert feedback.agent_name == "test_agent"
        assert feedback.rating == 4
        assert feedback.feedback_text == "Good response"

if __name__ == "__main__":
    pytest.main([__file__])
