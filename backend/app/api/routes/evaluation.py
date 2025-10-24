"""
Agent Evaluation API Routes

Provides endpoints for:
- Evaluating agent responses
- Collecting human feedback
- Viewing performance metrics
- Managing A/B tests
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.agents.evaluation import (
    evaluator, 
    evaluate_agent_response, 
    collect_feedback, 
    get_agent_performance,
    EvaluationType,
    EvaluationResult,
    HumanFeedback
)

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

# Request/Response Models
class EvaluationRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to evaluate")
    query: str = Field(..., description="User query that was processed")
    response: str = Field(..., description="Agent response to evaluate")
    evaluation_type: str = Field(default="llm_as_judge", description="Type of evaluation")
    criteria: Optional[List[str]] = Field(default=None, description="Specific criteria to evaluate")

class HumanFeedbackRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent")
    query: str = Field(..., description="User query")
    response: str = Field(..., description="Agent response")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = Field(default="", description="Optional feedback text")

class EvaluationResponse(BaseModel):
    evaluation_id: str
    agent_name: str
    evaluation_type: str
    overall_score: float
    criteria_scores: Dict[str, float]
    feedback: str
    timestamp: datetime
    metadata: Dict[str, Any]

class PerformanceSummaryResponse(BaseModel):
    agent_name: str
    period_days: int
    total_evaluations: int
    average_score: float
    performance_trend: str
    recent_evaluations: List[Dict[str, Any]]

class ABTestRequest(BaseModel):
    query: str = Field(..., description="Query to test")
    agent_a: str = Field(..., description="First agent to test")
    agent_b: str = Field(..., description="Second agent to test")
    test_duration_hours: int = Field(default=24, ge=1, le=168, description="Test duration in hours")

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_agent(
    request: EvaluationRequest,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks
):
    """Evaluate an agent response using specified evaluation type"""
    
    try:
        # Convert string to enum
        eval_type = EvaluationType(request.evaluation_type)
        
        # Run evaluation
        result = await evaluate_agent_response(
            agent_name=request.agent_name,
            query=request.query,
            response=request.response,
            evaluation_type=eval_type
        )
        
        # Convert criteria to dict for response
        criteria_scores = {
            "accuracy": result.criteria.accuracy,
            "relevance": result.criteria.relevance,
            "helpfulness": result.criteria.helpfulness,
            "creativity": result.criteria.creativity,
            "efficiency": result.criteria.efficiency,
            "user_satisfaction": result.criteria.user_satisfaction,
            "response_time": result.criteria.response_time,
            "cost_effectiveness": result.criteria.cost_effectiveness,
        }
        
        return EvaluationResponse(
            evaluation_id=result.evaluation_id,
            agent_name=result.agent_name,
            evaluation_type=result.evaluation_type.value,
            overall_score=result.overall_score,
            criteria_scores=criteria_scores,
            feedback=result.feedback,
            timestamp=result.timestamp,
            metadata=result.metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@router.post("/feedback", response_model=Dict[str, str])
async def submit_feedback(
    request: HumanFeedbackRequest,
    current_user: CurrentUser
):
    """Submit human feedback for agent evaluation"""
    
    try:
        feedback = await collect_feedback(
            user_id=str(current_user.id),
            agent_name=request.agent_name,
            query=request.query,
            response=request.response,
            rating=request.rating,
            feedback_text=request.feedback_text or ""
        )
        
        return {
            "message": "Feedback submitted successfully",
            "feedback_id": f"feedback_{feedback.timestamp.strftime('%Y%m%d_%H%M%S')}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@router.get("/performance/{agent_name}", response_model=PerformanceSummaryResponse)
async def get_agent_performance_metrics(
    agent_name: str,
    days: int = 30,
    current_user: CurrentUser = None
):
    """Get performance metrics for a specific agent"""
    
    try:
        performance = get_agent_performance(agent_name, days)
        return PerformanceSummaryResponse(**performance)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/performance", response_model=List[PerformanceSummaryResponse])
async def get_all_agents_performance(
    days: int = 30,
    current_user: CurrentUser = None
):
    """Get performance metrics for all agents"""
    
    try:
        # Get unique agent names from evaluation history
        agent_names = list(set([
            eval_result.agent_name 
            for eval_result in evaluator.evaluation_history
        ]))
        
        performance_list = []
        for agent_name in agent_names:
            performance = get_agent_performance(agent_name, days)
            performance_list.append(PerformanceSummaryResponse(**performance))
        
        return performance_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.post("/ab-test", response_model=Dict[str, Any])
async def start_ab_test(
    request: ABTestRequest,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks
):
    """Start an A/B test between two agents"""
    
    try:
        test_results = await evaluator.run_a_b_test(
            query=request.query,
            agent_a=request.agent_a,
            agent_b=request.agent_b,
            test_duration_hours=request.test_duration_hours
        )
        
        return test_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start A/B test: {str(e)}")

@router.get("/ab-test/{test_id}", response_model=Dict[str, Any])
async def get_ab_test_results(
    test_id: str,
    current_user: CurrentUser = None
):
    """Get results of an A/B test"""
    
    # In a real implementation, this would fetch from database
    # For now, return a mock response
    return {
        "test_id": test_id,
        "status": "completed",
        "message": "A/B test results would be fetched from database"
    }

@router.get("/evaluations", response_model=List[EvaluationResponse])
async def get_evaluation_history(
    agent_name: Optional[str] = None,
    limit: int = 50,
    current_user: CurrentUser = None
):
    """Get evaluation history for agents"""
    
    try:
        evaluations = evaluator.evaluation_history
        
        # Filter by agent name if specified
        if agent_name:
            evaluations = [e for e in evaluations if e.agent_name == agent_name]
        
        # Limit results
        evaluations = evaluations[-limit:] if limit > 0 else evaluations
        
        # Convert to response format
        response_list = []
        for eval_result in evaluations:
            criteria_scores = {
                "accuracy": eval_result.criteria.accuracy,
                "relevance": eval_result.criteria.relevance,
                "helpfulness": eval_result.criteria.helpfulness,
                "creativity": eval_result.criteria.creativity,
                "efficiency": eval_result.criteria.efficiency,
                "user_satisfaction": eval_result.criteria.user_satisfaction,
                "response_time": eval_result.criteria.response_time,
                "cost_effectiveness": eval_result.criteria.cost_effectiveness,
            }
            
            response_list.append(EvaluationResponse(
                evaluation_id=eval_result.evaluation_id,
                agent_name=eval_result.agent_name,
                evaluation_type=eval_result.evaluation_type.value,
                overall_score=eval_result.overall_score,
                criteria_scores=criteria_scores,
                feedback=eval_result.feedback,
                timestamp=eval_result.timestamp,
                metadata=eval_result.metadata
            ))
        
        return response_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evaluation history: {str(e)}")

@router.get("/feedback", response_model=List[Dict[str, Any]])
async def get_feedback_history(
    agent_name: Optional[str] = None,
    limit: int = 50,
    current_user: CurrentUser = None
):
    """Get human feedback history"""
    
    try:
        feedback_list = evaluator.human_feedback
        
        # Filter by agent name if specified
        if agent_name:
            feedback_list = [f for f in feedback_list if f.agent_name == agent_name]
        
        # Limit results
        feedback_list = feedback_list[-limit:] if limit > 0 else feedback_list
        
        # Convert to response format
        response_list = []
        for feedback in feedback_list:
            response_list.append({
                "user_id": feedback.user_id,
                "agent_name": feedback.agent_name,
                "query": feedback.query,
                "response": feedback.response,
                "rating": feedback.rating,
                "feedback_text": feedback.feedback_text,
                "timestamp": feedback.timestamp.isoformat()
            })
        
        return response_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feedback history: {str(e)}")

@router.get("/metrics", response_model=Dict[str, Any])
async def get_evaluation_metrics(
    current_user: CurrentUser = None
):
    """Get overall evaluation metrics and statistics"""
    
    try:
        total_evaluations = len(evaluator.evaluation_history)
        total_feedback = len(evaluator.human_feedback)
        
        if total_evaluations > 0:
            avg_score = sum(e.overall_score for e in evaluator.evaluation_history) / total_evaluations
        else:
            avg_score = 0.0
        
        # Agent performance breakdown
        agent_performance = {}
        for eval_result in evaluator.evaluation_history:
            agent_name = eval_result.agent_name
            if agent_name not in agent_performance:
                agent_performance[agent_name] = {
                    "total_evaluations": 0,
                    "total_score": 0.0,
                    "average_score": 0.0
                }
            
            agent_performance[agent_name]["total_evaluations"] += 1
            agent_performance[agent_name]["total_score"] += eval_result.overall_score
        
        # Calculate averages
        for agent_name, metrics in agent_performance.items():
            if metrics["total_evaluations"] > 0:
                metrics["average_score"] = metrics["total_score"] / metrics["total_evaluations"]
        
        return {
            "total_evaluations": total_evaluations,
            "total_human_feedback": total_feedback,
            "overall_average_score": round(avg_score, 2),
            "agent_performance": agent_performance,
            "evaluation_types": {
                "llm_as_judge": len([e for e in evaluator.evaluation_history if e.evaluation_type == EvaluationType.LLM_AS_JUDGE]),
                "human_in_loop": len([e for e in evaluator.evaluation_history if e.evaluation_type == EvaluationType.HUMAN_IN_LOOP]),
                "automated": len([e for e in evaluator.evaluation_history if e.evaluation_type == EvaluationType.AUTOMATED]),
                "a_b_test": len([e for e in evaluator.evaluation_history if e.evaluation_type == EvaluationType.A_B_TEST])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evaluation metrics: {str(e)}")
