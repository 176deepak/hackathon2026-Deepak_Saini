from datetime import datetime
from uuid import UUID
import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.models.enums import AgentRunStatus, ToolExecutionStatus
from app.models.models import AgentRun, AgentStep, Ticket, ToolExecution
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
        self._logger = AppLoggerAdapter(
            logging.getLogger(__name__),
            {
                "layer": LogLayer.DB,
                "category": LogCategory.DATABASE,
                "component": self.__class__.__name__,
            },
        )

    def create_run(self, ticket_id: str) -> AgentRunOut:
        try:
            run = AgentRun(
                ticket_id=UUID(ticket_id),
                status=AgentRunStatus.RUNNING,
                started_at=datetime.utcnow(),
            )
            self.db.add(run)
            self.db.commit()
            self.db.refresh(run)
            self._logger.info(
                "Agent run created",
                extra=extra_(
                    operation="repo_agent_run_create",
                    status="success",
                    ticket_uuid=ticket_id,
                    run_id=str(run.id),
                ),
            )
            return _to_agent_run_out(run)
        except Exception:
            self._logger.exception(
                "Failed to create agent run",
                extra=extra_(
                    operation="repo_agent_run_create",
                    status="failure",
                    ticket_uuid=ticket_id,
                ),
            )
            self.db.rollback()
            raise

    def complete_run(
        self, run_id: str, status: str, decision: str, confidence: float
    ) -> None:
        try:
            run = self.db.scalar(select(AgentRun).where(AgentRun.id == UUID(run_id)))
            if run is None:
                self._logger.warning(
                    "Run not found for completion",
                    extra=extra_(
                        operation="repo_agent_run_complete",
                        status="skipped",
                        run_id=run_id,
                    ),
                )
                return

            run.status = AgentRunStatus(status)
            run.final_decision = decision
            run.confidence_score = confidence
            run.ended_at = datetime.utcnow()
            run.total_steps = self.db.scalar(
                select(func.count()).select_from(AgentStep).where(
                    AgentStep.agent_run_id == run.id
                )
            ) or 0
            run.total_tool_calls = self.db.scalar(
                select(func.count())
                .select_from(ToolExecution)
                .join(AgentStep, ToolExecution.agent_step_id == AgentStep.id)
                .where(AgentStep.agent_run_id == run.id)
            ) or 0
            self.db.add(run)
            self.db.commit()
            self._logger.info(
                "Agent run completed",
                extra=extra_(
                    operation="repo_agent_run_complete",
                    status="success",
                    run_id=run_id,
                    final_status=status,
                    decision=decision,
                ),
            )
        except Exception:
            self._logger.exception(
                "Failed to complete agent run",
                extra=extra_(
                    operation="repo_agent_run_complete",
                    status="failure",
                    run_id=run_id,
                ),
            )
            self.db.rollback()
            raise

    def fail_run(self, run_id: str, error: str) -> None:
        try:
            run = self.db.scalar(select(AgentRun).where(AgentRun.id == UUID(run_id)))
            if run is None:
                self._logger.warning(
                    "Run not found for failure",
                    extra=extra_(
                        operation="repo_agent_run_fail",
                        status="skipped",
                        run_id=run_id,
                    ),
                )
                return

            run.status = AgentRunStatus.FAILED
            run.failure_reason = error
            run.ended_at = datetime.utcnow()
            self.db.add(run)
            self.db.commit()
            self._logger.warning(
                "Agent run failed",
                extra=extra_(
                    operation="repo_agent_run_fail",
                    status="success",
                    run_id=run_id,
                ),
            )
        except Exception:
            self._logger.exception(
                "Failed to mark agent run failed",
                extra=extra_(
                    operation="repo_agent_run_fail",
                    status="failure",
                    run_id=run_id,
                ),
            )
            self.db.rollback()
            raise

    def get_audit_timeline(self, ticket_ref: str) -> dict | None:
        ticket = self.db.scalar(
            select(Ticket).where(Ticket.external_ticket_id == ticket_ref.strip())
        )
        if ticket is None:
            try:
                ticket_uuid = UUID(ticket_ref)
            except ValueError:
                return None
            ticket = self.db.scalar(select(Ticket).where(Ticket.id == ticket_uuid))
            if ticket is None:
                return None

        runs = self.db.scalars(
            select(AgentRun)
            .where(AgentRun.ticket_id == ticket.id)
            .order_by(AgentRun.started_at.desc())
        ).all()

        run_items = []
        for run in runs:
            steps = self.db.scalars(
                select(AgentStep)
                .where(AgentStep.agent_run_id == run.id)
                .order_by(AgentStep.step_number.asc())
            ).all()

            step_items = []
            for step in steps:
                tool_calls = self.db.scalars(
                    select(ToolExecution).where(ToolExecution.agent_step_id == step.id)
                ).all()
                step_items.append(
                    {
                        "step_number": step.step_number,
                        "thought": step.thought,
                        "action": step.action_type,
                        "status": step.status,
                        "created_at": step.created_at,
                        "tool_calls": [
                            {
                                "tool_name": call.tool_name,
                                "status": call.status.value if call.status else "",
                                "error": call.error_message,
                                "created_at": call.created_at,
                            }
                            for call in tool_calls
                        ],
                    }
                )

            run_items.append(
                {
                    "run_id": str(run.id),
                    "status": run.status.value if run.status else "",
                    "final_decision": run.final_decision,
                    "confidence_score": run.confidence_score,
                    "started_at": run.started_at,
                    "ended_at": run.ended_at,
                    "steps": step_items,
                }
            )

        return {
            "ticket_id": ticket.external_ticket_id,
            "runs": run_items,
        }


class AgentStepRepo(BaseAgentStepRepo):
    def __init__(self, db: Session):
        super().__init__(db)
        self._logger = AppLoggerAdapter(
            logging.getLogger(__name__),
            {
                "layer": LogLayer.DB,
                "category": LogCategory.DATABASE,
                "component": self.__class__.__name__,
            },
        )

    def log_step(
        self,
        run_id: str,
        step_number: int,
        thought: str,
        action: str,
        input_payload: dict,
        output_payload: dict,
        status: str,
    ) -> str:
        try:
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
            self.db.refresh(step)
            self._logger.debug(
                "Agent step logged",
                extra=extra_(
                    operation="repo_agent_step_log",
                    status="success",
                    run_id=run_id,
                    step_number=step_number,
                    step_id=str(step.id),
                ),
            )
            return str(step.id)
        except Exception:
            self._logger.exception(
                "Failed to log agent step",
                extra=extra_(
                    operation="repo_agent_step_log",
                    status="failure",
                    run_id=run_id,
                    step_number=step_number,
                ),
            )
            self.db.rollback()
            raise


class ToolExecutionRepo(BaseToolExecutionRepo):
    def __init__(self, db: Session):
        super().__init__(db)
        self._logger = AppLoggerAdapter(
            logging.getLogger(__name__),
            {
                "layer": LogLayer.DB,
                "category": LogCategory.DATABASE,
                "component": self.__class__.__name__,
            },
        )

    def log_tool_call(
        self,
        step_id: str,
        tool_name: str,
        request: dict,
        response: dict,
        status: str,
        error: str = None,
    ) -> None:
        try:
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
            self._logger.debug(
                "Tool execution logged",
                extra=extra_(
                    operation="repo_tool_execution_log",
                    status="success",
                    step_id=step_id,
                    tool_name=tool_name,
                    tool_status=status,
                ),
            )
        except Exception:
            self._logger.exception(
                "Failed to log tool execution",
                extra=extra_(
                    operation="repo_tool_execution_log",
                    status="failure",
                    step_id=step_id,
                    tool_name=tool_name,
                ),
            )
            self.db.rollback()
            raise
