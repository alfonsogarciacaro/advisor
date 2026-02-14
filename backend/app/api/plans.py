from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.services.plan_service import PlanService
from app.services.research_agent import ResearchAgent
from app.models.plan import Plan
from app.models.types import RiskProfile
from app.core.dependencies import get_plan_service, get_logger, get_research_agent, get_current_user
from app.services.logger_service import LoggerService
from app.models.auth import User

router = APIRouter()


class PlanCreateRequest(BaseModel):
    """Request to create a new plan"""
    name: str
    description: Optional[str] = None
    risk_preference: RiskProfile = RiskProfile.MODERATE
    initial_portfolio: Optional[List[Dict[str, Any]]] = None
    initial_amount: Optional[float] = None
    currency: str = "USD"
    user_id: str = "default"  # Default user for single-user mode


class PlanUpdateRequest(BaseModel):
    """Request to update plan metadata"""
    name: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    risk_preference: Optional[RiskProfile] = None


class PortfolioUpdateRequest(BaseModel):
    """Request to update plan's initial portfolio"""
    initial_portfolio: List[Dict[str, Any]]


class ResearchRequest(BaseModel):
    """Request to run research agent on a plan"""
    query: str


@router.post("/plans", response_model=Dict[str, str])
async def create_plan(
    request: PlanCreateRequest,
    current_user: User = Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    Create a new investment plan.

    A plan represents an investment strategy with portfolio allocation,
    optimization results, and research history.
    """
    try:
        plan_id = await plan_service.create_plan(
            user_id=request.user_id,
            name=request.name,
            description=request.description,
            risk_preference=request.risk_preference,
            initial_portfolio=request.initial_portfolio,
            initial_amount=request.initial_amount,
            currency=request.currency
        )
        return {"plan_id": plan_id, "status": "created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans", response_model=List[Plan])
async def list_plans(
    user_id: str = "default",
    current_user: User = Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    List all plans for a user.

    Returns plans sorted by updated_at descending (most recent first).
    """
    try:
        plans = await plan_service.list_plans(user_id)
        return plans
    except Exception as e:
        logger.error(f"Error listing plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/{plan_id}", response_model=Plan)
async def get_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    Get a specific plan by ID.
    """
    plan = await plan_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.put("/plans/{plan_id}", response_model=Dict[str, str])
async def update_plan(
    plan_id: str,
    request: PlanUpdateRequest,
    current_user: User = Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    Update plan metadata (name, description, notes, risk preference).
    """
    try:
        success = await plan_service.update_plan(
            plan_id=plan_id,
            name=request.name,
            description=request.description,
            notes=request.notes,
            risk_preference=request.risk_preference
        )
        if not success:
            raise HTTPException(status_code=404, detail="Plan not found")
        return {"plan_id": plan_id, "status": "updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/plans/{plan_id}/portfolio", response_model=Dict[str, str])
async def update_plan_portfolio(
    plan_id: str,
    request: PortfolioUpdateRequest,
    current_user: User = Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    Update the initial portfolio holdings for a plan.
    """
    try:
        success = await plan_service.update_plan(
            plan_id,
            initial_portfolio=request.initial_portfolio
        )
        if not success:
            raise HTTPException(status_code=404, detail="Plan not found")
        return {"plan_id": plan_id, "status": "updated"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating plan portfolio {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/plans/{plan_id}", response_model=Dict[str, str])
async def delete_plan(
    plan_id: str,
    user_id: str = "default",
    current_user: User = Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    Delete a plan.
    """
    try:
        success = await plan_service.delete_plan(plan_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Plan not found or unauthorized")
        return {"plan_id": plan_id, "status": "deleted"}
    except Exception as e:
        logger.error(f"Error deleting plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/research")
async def run_research_on_plan(
    plan_id: str,
    request: ResearchRequest,
    current_user: User = Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
    research_agent: ResearchAgent = Depends(get_research_agent),
    logger: LoggerService = Depends(get_logger)
):
    """
    Run the research agent on a plan with existing portfolio context.

    This allows for follow-up analysis on an optimized portfolio.
    """
    try:
        # Get the plan
        plan = await plan_service.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        # Prepare plan context for research agent
        plan_context = {
            "plan_name": plan.name,
            "risk_preference": plan.risk_preference,
            "optimization_result": plan.optimization_result.model_dump() if plan.optimization_result else None,
            "initial_amount": plan.initial_amount
        }

        # Run research agent with plan context
        initial_state = research_agent.get_initial_state({
            "query": request.query,
            "plan_context": plan_context
        })

        # Execute the research graph
        graph = research_agent.build_graph()
        result = await graph.ainvoke(initial_state)

        # Extract results
        summary = result.get("summary", "")
        scenarios = result.get("scenarios", {})
        refined_forecasts = result.get("refined_forecasts", {})

        # Convert scenarios to list if needed
        scenarios_list = []
        if scenarios:
            # Flatten scenarios structure
            for ticker, cases in scenarios.items():
                for case_name, case_data in cases.items():
                    scenarios_list.append({
                        "ticker": ticker,
                        "case": case_name,
                        **case_data
                    })

        # Generate follow-up suggestions from LLM if available
        follow_up_suggestions = None
        if research_agent.llm_service:
            try:
                suggestions_prompt = f"""Based on this research analysis:

Query: {request.query}

Summary:
{summary}

Suggest 3-4 follow-up questions that would help the investor understand this topic better.
Return as JSON with key "suggestions" containing a list of questions."""
                response = await research_agent.llm_service.generate_json(suggestions_prompt)
                follow_up_suggestions = response.get("suggestions", [])
            except Exception as e:
                logger.warning(f"Failed to generate follow-up suggestions: {e}")

        # Save research run to plan
        run_id = await plan_service.add_research_run(
            plan_id=plan_id,
            query=request.query,
            result_summary=summary,
            scenarios=scenarios_list,
            refined_forecasts=refined_forecasts,
            follow_up_suggestions=follow_up_suggestions
        )

        return {
            "run_id": run_id,
            "summary": summary,
            "scenarios": scenarios_list,
            "refined_forecasts": refined_forecasts,
            "follow_up_suggestions": follow_up_suggestions
        }

    except Exception as e:
        logger.error(f"Error running research on plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
