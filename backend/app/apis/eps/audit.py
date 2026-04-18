from fastapi import APIRouter, HTTPException, Path, status

from app.core.dependencies import AuditServiceDep
from app.schemas.api import (
    AuditLogData, AuditRunItem, AuditStepItem, AuditToolCallItem, RESTResponse
)
from ..docs import AUDIT_API_DOC


router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get(
    "/{ticket_id}",
    response_model=RESTResponse[AuditLogData],
    summary="Get ticket audit timeline",
    description=(
        "Get complete run, step, and tool-call timeline for a ticket using external id or UUID."
    ),
)
async def get_audit_logs(
    audit_service: AuditServiceDep,
    ticket_id: str = Path(..., description="External ticket id (e.g. TKT-001) or UUID"),
):
    timeline = await audit_service.get_audit_timeline(ticket_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    payload = AuditLogData(
        ticket_id=timeline["ticket_id"],
        runs=[
            AuditRunItem(
                run_id=run["run_id"],
                status=run["status"],
                final_decision=run["final_decision"],
                confidence_score=run["confidence_score"],
                started_at=run["started_at"],
                ended_at=run["ended_at"],
                steps=[
                    AuditStepItem(
                        step_number=step["step_number"],
                        thought=step["thought"],
                        action=step["action"],
                        status=step["status"],
                        created_at=step["created_at"],
                        tool_calls=[
                            AuditToolCallItem(
                                tool_name=call["tool_name"],
                                status=call["status"],
                                error=call["error"],
                                created_at=call["created_at"],
                            )
                            for call in step["tool_calls"]
                        ],
                    )
                    for step in run["steps"]
                ],
            )
            for run in timeline["runs"]
        ],
    )

    return RESTResponse(
        code=status.HTTP_200_OK,
        success=True,
        data=payload,
        msg="Audit logs fetched successfully",
    )


get_audit_logs.__doc__ = AUDIT_API_DOC