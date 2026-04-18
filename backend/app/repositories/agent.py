from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import AgentRunStatus, ToolExecutionStatus
from app.models.models import AgentRun, AgentStep, ToolExecution
from app.repositories.base import (
    BaseAgentRunRepo, BaseAgentStepRepo, BaseToolExecutionRepo,
)
from app.schemas.repo import AgentRunOut


def _to_agent_run_out(run: AgentRun) -> AgentRunOut:
    return AgentRunOut(
        id=str(run.id),
        ticket_id=str(run.ticket_id),
        status=run.status.value if run.status else "",
        final_decision=run.final_decision,
        confidence_score=run.confidence_score,
        started_at=run.started_at,
        ended_at=run.ended_at,
    )


class AgentRunRepo(BaseAgentRunRepo):
    def __init__(self, db: Session):
        super().__init__(db)

    def create_run(self, ticket_id: str) -> AgentRunOut:
        run = AgentRun(
            ticket_id=UUID(ticket_id),
            status=AgentRunStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return _to_agent_run_out(run)

    def complete_run(
        self, run_id: str, status: str, decision: str, confidence: float
    ) -> None:
        run = self.db.scalar(select(AgentRun).where(AgentRun.id == UUID(run_id)))
        if run is None:
            return

        run.status = AgentRunStatus(status)
        run.final_decision = decision
        run.confidence_score = confidence
        run.ended_at = datetime.utcnow()
        run.total_steps = self.db.scalar(
            select(func.count()).select_from(AgentStep).where(AgentStep.agent_run_id == run.id)
        ) or 0
        run.total_tool_calls = self.db.scalar(
            select(func.count())
            .select_from(ToolExecution)
            .join(AgentStep, ToolExecution.agent_step_id == AgentStep.id)
            .where(AgentStep.agent_run_id == run.id)
        ) or 0
        self.db.add(run)
        self.db.commit()

    def fail_run(self, run_id: str, error: str) -> None:
        run = self.db.scalar(select(AgentRun).where(AgentRun.id == UUID(run_id)))
        if run is None:
            return

        run.status = AgentRunStatus.FAILED
        run.failure_reason = error
        run.ended_at = datetime.utcnow()
        self.db.add(run)
        self.db.commit()


class AgentStepRepo(BaseAgentStepRepo):
    def __init__(self, db: Session):
        super().__init__(db)

    def log_step(
        self,
        run_id: str,
        step_number: int,
        thought: str,
        action: str,
        input_payload: dict,
        output_payload: dict,
        status: str,
    ) -> None:
        step = AgentStep(
            agent_run_id=UUID(run_id),
            step_number=step_number,
            thought=thought,
            action_type=action,
            input_payload=input_payload,
            output_payload=output_payload,
            status=status,
        )
        self.db.add(step)
        self.db.commit()


class ToolExecutionRepo(BaseToolExecutionRepo):
    def __init__(self, db: Session):
        super().__init__(db)

    def log_tool_call(
        self,
        step_id: str,
        tool_name: str,
        request: dict,
        response: dict,
        status: str,
        error: str = None,
    ) -> None:
        execution = ToolExecution(
            agent_step_id=UUID(step_id),
            tool_name=tool_name,
            request_payload=request,
            response_payload=response,
            status=ToolExecutionStatus(status),
            error_message=error,
        )
        self.db.add(execution)
        self.db.commit()