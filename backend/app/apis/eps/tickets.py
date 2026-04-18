from fastapi import APIRouter, HTTPException, Path, Query, status

from app.core.dependencies import TicketServiceDep, TicketStatusFilter
from app.schemas.api import (
    RESTResponse, TicketDetailData, TicketListData, TicketStatusData, 
    TicketStatusUpdateRequest, TicketSummary,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get(
    "/",
    response_model=RESTResponse[TicketListData],
    summary="List tickets",
    description="List support tickets with optional status filter and pagination.",
)
async def list_tickets(
    ticket_service: TicketServiceDep,
    page: int = Query(default=1, ge=1, description="1-based page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: TicketStatusFilter | None = Query(
        default=None,
        alias="status",
        description="Optional ticket status filter",
    ),
):
    items, total = await ticket_service.list_tickets(
        page=page,
        limit=limit,
        status=status_filter,
    )

    payload = TicketListData(
        page=page,
        limit=limit,
        total=total,
        items=[
            TicketSummary(
                ticket_id=item.external_ticket_id,
                customer_email=item.customer_email,
                subject=item.subject,
                status=item.status,
            )
            for item in items
        ],
    )

    return RESTResponse(
        code=status.HTTP_200_OK,
        success=True,
        data=payload,
        msg="Tickets fetched successfully",
    )


@router.get(
    "/{ticket_id}",
    response_model=RESTResponse[TicketDetailData],
    summary="Get ticket details",
    description="Get full ticket details by external ticket id or internal UUID.",
)
async def get_ticket(
    ticket_service: TicketServiceDep,
    ticket_id: str = Path(..., description="External ticket id (e.g. TKT-001) or UUID"),
):
    ticket = await ticket_service.get_ticket_by_reference(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return RESTResponse(
        code=status.HTTP_200_OK,
        success=True,
        data=TicketDetailData(
            ticket_id=ticket.external_ticket_id,
            customer_email=ticket.customer_email,
            subject=ticket.subject,
            body=ticket.body,
            status=ticket.status,
        ),
        msg="Ticket fetched successfully",
    )


@router.get(
    "/{ticket_id}/status",
    response_model=RESTResponse[TicketStatusData],
    summary="Get ticket status",
    description="Get ticket processing status by external ticket id or internal UUID.",
)
async def get_ticket_status(
    ticket_service: TicketServiceDep,
    ticket_id: str = Path(..., description="External ticket id (e.g. TKT-001) or UUID"),
):
    ticket = await ticket_service.get_ticket_by_reference(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return RESTResponse(
        code=status.HTTP_200_OK,
        success=True,
        data=TicketStatusData(
            ticket_id=ticket.external_ticket_id,
            status=ticket.status,
        ),
        msg="Ticket status fetched successfully",
    )


@router.patch(
    "/{ticket_id}/status",
    response_model=RESTResponse[TicketStatusData],
    summary="Update ticket status",
    description="Update ticket workflow status by external ticket id or internal UUID.",
)
async def update_ticket_status(
    payload: TicketStatusUpdateRequest,
    ticket_service: TicketServiceDep,
    ticket_id: str = Path(..., description="External ticket id (e.g. TKT-001) or UUID"),
):
    ticket = await ticket_service.update_status_by_reference(ticket_id, payload.status)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return RESTResponse(
        code=status.HTTP_200_OK,
        success=True,
        data=TicketStatusData(
            ticket_id=ticket.external_ticket_id,
            status=ticket.status,
        ),
        msg="Ticket status updated successfully",
    )
