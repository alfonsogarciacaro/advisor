import uuid
import datetime
from typing import Dict, Any, List, Optional
from app.services.storage_service import StorageService
from app.services.logger_service import LoggerService
from app.services.config_service import ConfigService
from app.models.plan import Plan, ResearchRun
from app.models.types import RiskProfile
from app.core.utils import sanitize_numpy


class PlanService:
    """
    Service for managing investment plans.

    Plans are the main organizational unit for the application.
    Each plan contains portfolio optimization results, research history,
    and user configuration.
    """

    def __init__(
        self,
        storage: StorageService,
        logger: LoggerService,
        config_service: ConfigService
    ):
        self.storage = storage
        self.logger = logger
        self.config_service = config_service
        self.collection = "plans"

    async def create_plan(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        risk_preference: RiskProfile = RiskProfile.MODERATE,
        initial_portfolio: Optional[List[Dict[str, Any]]] = None,
        initial_amount: Optional[float] = None,
        currency: str = "USD"
    ) -> str:
        """
        Create a new investment plan.

        Args:
            user_id: User identifier (use "default" for single-user mode)
            name: User-defined plan name
            description: Optional description
            risk_preference: Risk tolerance level
            initial_portfolio: Existing holdings (if any)
            initial_amount: Cash amount to invest (if any)
            currency: Currency code

        Returns:
            plan_id: The ID of the created plan
        """
        plan_id = str(uuid.uuid4())

        now = datetime.datetime.now(datetime.timezone.utc)

        plan = Plan(
            plan_id=plan_id,
            user_id=user_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
            risk_preference=risk_preference,
            initial_portfolio=initial_portfolio,
            initial_amount=initial_amount,
            research_history=[],
            optimization_result=None,
            recurring_investment=None,
            tax_accounts=None,
            notes=None
        )

        await self.storage.save(
            self.collection,
            plan_id,
            sanitize_numpy(plan.model_dump())
        )

        self.logger.info(f"Created plan '{name}' ({plan_id}) for user {user_id}")
        return plan_id

    async def get_plan(self, plan_id: str) -> Optional[Plan]:
        """
        Retrieve a plan by ID.

        Args:
            plan_id: Plan identifier

        Returns:
            Plan object if found, None otherwise
        """
        data = await self.storage.get(self.collection, plan_id)
        if not data:
            return None

        return Plan(**data)

    async def list_plans(self, user_id: str) -> List[Plan]:
        """
        List all plans for a user.

        Args:
            user_id: User identifier

        Returns:
            List of plans, sorted by updated_at descending
        """
        try:
            # Use storage service's list method with user_id filter
            items = await self.storage.list(
                self.collection,
                filters={"user_id": user_id}
            )

            user_plans = [Plan(**item) for item in items]

            # Sort by updated_at descending
            user_plans.sort(key=lambda p: p.updated_at, reverse=True)
            return user_plans

        except Exception as e:
            self.logger.error(f"Error listing plans for user {user_id}: {e}")
            return []

    async def update_plan(
        self,
        plan_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None,
        risk_preference: Optional[RiskProfile] = None,
        initial_portfolio: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Update plan metadata (name, description, notes, risk preference, initial_portfolio).

        Args:
            plan_id: Plan identifier
            name: New name (optional)
            description: New description (optional)
            notes: New notes (optional)
            risk_preference: New risk preference (optional)
            initial_portfolio: New initial portfolio holdings (optional)

        Returns:
            True if updated successfully, False otherwise
        """
        plan = await self.get_plan(plan_id)
        if not plan:
            self.logger.warning(f"Plan {plan_id} not found for update")
            return False

        # Update fields if provided
        if name is not None:
            plan.name = name
        if description is not None:
            plan.description = description
        if notes is not None:
            plan.notes = notes
        if risk_preference is not None:
            plan.risk_preference = risk_preference
        if initial_portfolio is not None:
            plan.initial_portfolio = initial_portfolio

        plan.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.storage.save(
            self.collection,
            plan_id,
            sanitize_numpy(plan.model_dump())
        )

        self.logger.info(f"Updated plan {plan_id}")
        return True

    async def attach_optimization_result(
        self,
        plan_id: str,
        optimization_result: Dict[str, Any]
    ) -> bool:
        """
        Attach an optimization result to a plan.

        This is called after portfolio optimization completes.

        Args:
            plan_id: Plan identifier
            optimization_result: Optimization result from PortfolioOptimizer

        Returns:
            True if attached successfully, False otherwise
        """
        plan = await self.get_plan(plan_id)
        if not plan:
            self.logger.warning(f"Plan {plan_id} not found for optimization result")
            return False

        plan.optimization_result = optimization_result
        plan.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.storage.save(
            self.collection,
            plan_id,
            sanitize_numpy(plan.model_dump())
        )

        self.logger.info(f"Attached optimization result to plan {plan_id}")
        return True

    async def add_research_run(
        self,
        plan_id: str,
        query: str,
        result_summary: str,
        scenarios: Optional[List[Dict[str, Any]]] = None,
        refined_forecasts: Optional[Dict[str, Any]] = None,
        follow_up_suggestions: Optional[List[str]] = None
    ) -> str:
        """
        Add a research agent run to the plan's history.

        Args:
            plan_id: Plan identifier
            query: The research query
            result_summary: Summary of the research results
            scenarios: Scenario forecasts (optional)
            refined_forecasts: Refined forecast data (optional)
            follow_up_suggestions: Follow-up questions for the user (optional)

        Returns:
            run_id: The ID of the created research run
        """
        plan = await self.get_plan(plan_id)
        if not plan:
            self.logger.warning(f"Plan {plan_id} not found for research run")
            raise ValueError(f"Plan {plan_id} not found")

        run_id = str(uuid.uuid4())

        research_run = ResearchRun(
            run_id=run_id,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            query=query,
            result_summary=result_summary,
            scenarios=scenarios,
            refined_forecasts=refined_forecasts,
            follow_up_suggestions=follow_up_suggestions
        )

        plan.research_history.append(research_run)
        plan.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.storage.save(
            self.collection,
            plan_id,
            sanitize_numpy(plan.model_dump())
        )

        self.logger.info(f"Added research run {run_id} to plan {plan_id}")
        return run_id

    async def delete_plan(self, plan_id: str, user_id: str) -> bool:
        """
        Delete a plan.

        Args:
            plan_id: Plan identifier
            user_id: User identifier (for authorization)

        Returns:
            True if deleted successfully, False otherwise
        """
        plan = await self.get_plan(plan_id)
        if not plan:
            return False

        # Verify ownership
        if plan.user_id != user_id:
            self.logger.warning(f"User {user_id} attempted to delete plan {plan_id} owned by {plan.user_id}")
            return False

        await self.storage.delete(self.collection, plan_id)

        self.logger.info(f"Deleted plan {plan_id}")
        return True
