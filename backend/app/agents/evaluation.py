"""
Agent Evaluation System

This module implements comprehensive agent evaluation including:
- Human-in-the-loop evaluation
- LLM-as-a-judge evaluation
- Performance metrics tracking
- A/B testing capabilities
- Feedback collection and analysis
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from app.core.config import settings
from app.core.llm import call_llm
from app.agents.sessions import memory_manager

logger = logging.getLogger(__name__)

class EvaluationType(Enum):
    HUMAN_IN_LOOP = "human_in_loop"
    LLM_AS_JUDGE = "llm_as_judge"
    AUTOMATED = "automated"
    A_B_TEST = "a_b_test"

class EvaluationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class EvaluationCriteria:
    """Criteria for evaluating agent performance"""
    accuracy: float = 0.0
    relevance: float = 0.0
    helpfulness: float = 0.0
    creativity: float = 0.0
    efficiency: float = 0.0
    user_satisfaction: float = 0.0
    response_time: float = 0.0
    cost_effectiveness: float = 0.0

@dataclass
class EvaluationResult:
    """Result of an agent evaluation"""
    evaluation_id: str
    agent_name: str
    evaluation_type: EvaluationType
    criteria: EvaluationCriteria
    overall_score: float
    feedback: str
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class HumanFeedback:
    """Human feedback for agent evaluation"""
    user_id: str
    agent_name: str
    query: str
    response: str
    rating: int  # 1-5 scale
    feedback_text: str
    timestamp: datetime

class AgentEvaluator:
    """Main class for evaluating agent performance"""
    
    def __init__(self):
        self.evaluation_history: List[EvaluationResult] = []
        self.human_feedback: List[HumanFeedback] = []
        self.llm_judge_prompts = self._load_judge_prompts()
    
    def _load_judge_prompts(self) -> Dict[str, str]:
        """Load LLM judge prompts for different evaluation types"""
        return {
            "accuracy": """
            Evaluate the accuracy of this AI agent response on a scale of 1-10.
            Consider: factual correctness, logical consistency, and adherence to instructions.
            
            Query: {query}
            Response: {response}
            
            Rate accuracy (1-10):""",
            
            "relevance": """
            Evaluate the relevance of this AI agent response on a scale of 1-10.
            Consider: how well the response addresses the query, completeness, and appropriateness.
            
            Query: {query}
            Response: {response}
            
            Rate relevance (1-10):""",
            
            "helpfulness": """
            Evaluate the helpfulness of this AI agent response on a scale of 1-10.
            Consider: practical value, actionable advice, and user benefit.
            
            Query: {query}
            Response: {response}
            
            Rate helpfulness (1-10):""",
            
            "creativity": """
            Evaluate the creativity of this AI agent response on a scale of 1-10.
            Consider: originality, innovative solutions, and unique insights.
            
            Query: {query}
            Response: {response}
            
            Rate creativity (1-10):""",
            
            "overall": """
            Evaluate this AI agent response overall on a scale of 1-10.
            Consider: accuracy, relevance, helpfulness, creativity, and user satisfaction.
            
            Query: {query}
            Response: {response}
            
            Provide an overall rating (1-10) and brief explanation:"""
        }
    
    async def evaluate_with_llm_judge(
        self, 
        agent_name: str, 
        query: str, 
        response: str,
        criteria: List[str] = None
    ) -> EvaluationResult:
        """Evaluate agent response using LLM as judge"""
        if criteria is None:
            criteria = ["accuracy", "relevance", "helpfulness", "creativity"]
        
        evaluation_criteria = EvaluationCriteria()
        feedback_parts = []
        
        # Evaluate each criterion
        for criterion in criteria:
            if criterion in self.llm_judge_prompts:
                prompt = self.llm_judge_prompts[criterion].format(
                    query=query, response=response
                )
                
                try:
                    judge_response = call_llm(prompt)
                    score = self._extract_score(judge_response)
                    setattr(evaluation_criteria, criterion, score)
                    feedback_parts.append(f"{criterion}: {score}/10")
                except Exception as e:
                    logger.error(f"Error evaluating {criterion}: {e}")
                    setattr(evaluation_criteria, criterion, 0.0)
        
        # Overall evaluation
        try:
            overall_prompt = self.llm_judge_prompts["overall"].format(
                query=query, response=response
            )
            overall_response = call_llm(overall_prompt)
            overall_score = self._extract_score(overall_response)
            overall_feedback = self._extract_feedback(overall_response)
        except Exception as e:
            logger.error(f"Error in overall evaluation: {e}")
            overall_score = sum([
                evaluation_criteria.accuracy,
                evaluation_criteria.relevance,
                evaluation_criteria.helpfulness,
                evaluation_criteria.creativity
            ]) / len(criteria)
            overall_feedback = "Evaluation completed with partial criteria"
        
        # Calculate overall score
        overall_score = max(overall_score, evaluation_criteria.accuracy, 
                           evaluation_criteria.relevance, evaluation_criteria.helpfulness)
        
        evaluation_result = EvaluationResult(
            evaluation_id=f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{agent_name}",
            agent_name=agent_name,
            evaluation_type=EvaluationType.LLM_AS_JUDGE,
            criteria=evaluation_criteria,
            overall_score=overall_score,
            feedback=f"LLM Judge: {overall_feedback}. Details: {'; '.join(feedback_parts)}",
            timestamp=datetime.now(),
            metadata={
                "query": query,
                "response": response,
                "criteria_evaluated": criteria
            }
        )
        
        self.evaluation_history.append(evaluation_result)
        return evaluation_result
    
    async def collect_human_feedback(
        self,
        user_id: str,
        agent_name: str,
        query: str,
        response: str,
        rating: int,
        feedback_text: str = ""
    ) -> HumanFeedback:
        """Collect human feedback for agent evaluation"""
        feedback = HumanFeedback(
            user_id=user_id,
            agent_name=agent_name,
            query=query,
            response=response,
            rating=rating,
            feedback_text=feedback_text,
            timestamp=datetime.now()
        )
        
        self.human_feedback.append(feedback)
        
        # Store in memory for analysis
        await memory_manager.store_user_feedback(
            user_id, agent_name, query, response, rating, feedback_text
        )
        
        return feedback
    
    async def evaluate_with_human_in_loop(
        self,
        user_id: str,
        agent_name: str,
        query: str,
        response: str
    ) -> Tuple[EvaluationResult, HumanFeedback]:
        """Evaluate agent with human-in-the-loop feedback"""
        
        # First, get LLM evaluation
        llm_evaluation = await self.evaluate_with_llm_judge(
            agent_name, query, response
        )
        
        # Create a pending evaluation that requires human feedback
        pending_evaluation = EvaluationResult(
            evaluation_id=f"pending_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{agent_name}",
            agent_name=agent_name,
            evaluation_type=EvaluationType.HUMAN_IN_LOOP,
            criteria=EvaluationCriteria(),
            overall_score=0.0,
            feedback="Pending human feedback",
            timestamp=datetime.now(),
            metadata={
                "query": query,
                "response": response,
                "status": "pending_human_feedback",
                "llm_evaluation": asdict(llm_evaluation)
            }
        )
        
        return pending_evaluation, None
    
    async def complete_human_evaluation(
        self,
        evaluation_id: str,
        human_feedback: HumanFeedback
    ) -> EvaluationResult:
        """Complete human-in-the-loop evaluation with feedback"""
        
        # Find the pending evaluation
        pending_eval = None
        for eval_result in self.evaluation_history:
            if eval_result.evaluation_id == evaluation_id:
                pending_eval = eval_result
                break
        
        if not pending_eval:
            raise ValueError(f"Evaluation {evaluation_id} not found")
        
        # Create completed evaluation combining LLM and human feedback
        llm_eval = pending_eval.metadata.get("llm_evaluation", {})
        
        # Weight human feedback more heavily
        human_weight = 0.7
        llm_weight = 0.3
        
        overall_score = (
            human_feedback.rating * 2 * human_weight +  # Convert 1-5 to 1-10 scale
            llm_eval.get("overall_score", 5) * llm_weight
        )
        
        completed_evaluation = EvaluationResult(
            evaluation_id=evaluation_id,
            agent_name=pending_eval.agent_name,
            evaluation_type=EvaluationType.HUMAN_IN_LOOP,
            criteria=EvaluationCriteria(
                accuracy=llm_eval.get("criteria", {}).get("accuracy", 0) * llm_weight + 
                        human_feedback.rating * 2 * human_weight,
                relevance=llm_eval.get("criteria", {}).get("relevance", 0) * llm_weight + 
                         human_feedback.rating * 2 * human_weight,
                helpfulness=llm_eval.get("criteria", {}).get("helpfulness", 0) * llm_weight + 
                           human_feedback.rating * 2 * human_weight,
                user_satisfaction=human_feedback.rating * 2,  # Pure human rating
            ),
            overall_score=overall_score,
            feedback=f"Human Feedback: {human_feedback.feedback_text}. LLM: {llm_eval.get('feedback', '')}",
            timestamp=datetime.now(),
            metadata={
                "query": pending_eval.metadata["query"],
                "response": pending_eval.metadata["response"],
                "human_feedback": asdict(human_feedback),
                "llm_evaluation": llm_eval,
                "status": "completed"
            }
        )
        
        # Update the evaluation in history
        for i, eval_result in enumerate(self.evaluation_history):
            if eval_result.evaluation_id == evaluation_id:
                self.evaluation_history[i] = completed_evaluation
                break
        
        return completed_evaluation
    
    async def run_a_b_test(
        self,
        query: str,
        agent_a: str,
        agent_b: str,
        test_duration_hours: int = 24
    ) -> Dict[str, Any]:
        """Run A/B test between two agents"""
        
        # This would typically involve routing queries to different agents
        # and collecting performance metrics over time
        
        test_id = f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=test_duration_hours)
        
        # Mock A/B test results for now
        # In production, this would collect real metrics
        test_results = {
            "test_id": test_id,
            "query": query,
            "agent_a": agent_a,
            "agent_b": agent_b,
            "start_time": start_time,
            "end_time": end_time,
            "status": "running",
            "metrics": {
                agent_a: {
                    "response_count": 0,
                    "average_score": 0.0,
                    "user_satisfaction": 0.0,
                    "response_time": 0.0
                },
                agent_b: {
                    "response_count": 0,
                    "average_score": 0.0,
                    "user_satisfaction": 0.0,
                    "response_time": 0.0
                }
            }
        }
        
        return test_results
    
    def get_agent_performance_summary(
        self, 
        agent_name: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get performance summary for an agent over specified days"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        agent_evaluations = [
            eval_result for eval_result in self.evaluation_history
            if eval_result.agent_name == agent_name and eval_result.timestamp >= cutoff_date
        ]
        
        if not agent_evaluations:
            return {
                "agent_name": agent_name,
                "period_days": days,
                "total_evaluations": 0,
                "average_score": 0.0,
                "performance_trend": "no_data"
            }
        
        scores = [eval_result.overall_score for eval_result in agent_evaluations]
        average_score = sum(scores) / len(scores)
        
        # Calculate trend
        if len(scores) >= 2:
            recent_scores = scores[-len(scores)//2:]
            older_scores = scores[:len(scores)//2]
            recent_avg = sum(recent_scores) / len(recent_scores)
            older_avg = sum(older_scores) / len(older_scores)
            
            if recent_avg > older_avg * 1.05:
                trend = "improving"
            elif recent_avg < older_avg * 0.95:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "agent_name": agent_name,
            "period_days": days,
            "total_evaluations": len(agent_evaluations),
            "average_score": round(average_score, 2),
            "performance_trend": trend,
            "recent_evaluations": [
                {
                    "timestamp": eval_result.timestamp.isoformat(),
                    "score": eval_result.overall_score,
                    "feedback": eval_result.feedback[:100] + "..." if len(eval_result.feedback) > 100 else eval_result.feedback
                }
                for eval_result in agent_evaluations[-5:]  # Last 5 evaluations
            ]
        }
    
    def _extract_score(self, response: str) -> float:
        """Extract numerical score from LLM response"""
        import re
        
        # Look for numbers in the response
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', response)
        if numbers:
            score = float(numbers[0])
            # Ensure score is in 1-10 range
            return max(1.0, min(10.0, score))
        
        return 5.0  # Default neutral score
    
    def _extract_feedback(self, response: str) -> str:
        """Extract feedback text from LLM response"""
        # Remove score numbers and return the rest
        import re
        cleaned = re.sub(r'\b\d+(?:\.\d+)?\b', '', response)
        cleaned = cleaned.strip()
        return cleaned if cleaned else "No detailed feedback provided"

# Global evaluator instance
evaluator = AgentEvaluator()

# Convenience functions
async def evaluate_agent_response(
    agent_name: str,
    query: str,
    response: str,
    evaluation_type: EvaluationType = EvaluationType.LLM_AS_JUDGE
) -> EvaluationResult:
    """Convenience function to evaluate agent response"""
    if evaluation_type == EvaluationType.LLM_AS_JUDGE:
        return await evaluator.evaluate_with_llm_judge(agent_name, query, response)
    elif evaluation_type == EvaluationType.HUMAN_IN_LOOP:
        return await evaluator.evaluate_with_human_in_loop("", agent_name, query, response)
    else:
        raise ValueError(f"Unsupported evaluation type: {evaluation_type}")

async def collect_feedback(
    user_id: str,
    agent_name: str,
    query: str,
    response: str,
    rating: int,
    feedback_text: str = ""
) -> HumanFeedback:
    """Convenience function to collect human feedback"""
    return await evaluator.collect_human_feedback(
        user_id, agent_name, query, response, rating, feedback_text
    )

def get_agent_performance(agent_name: str, days: int = 30) -> Dict[str, Any]:
    """Convenience function to get agent performance"""
    return evaluator.get_agent_performance_summary(agent_name, days)
