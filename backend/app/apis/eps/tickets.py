from fastapi import APIRouter, HTTPException, Path, Query, status, Depends

from app.core.dependencies import TicketServiceDep, TicketStatusFilter
from app.core.security import JWTBearer
from app.schemas.api import (
    RESTResponse, TicketDetailData, TicketListData, TicketStatusData,
    TicketStatusUpdateRequest, TicketSummary,
)
from ..docs import (
    TICKETS_GET_API_DOC,
    TICKETS_LIST_API_DOC,
    TICKETS_STATUS_GET_API_DOC,
    TICKETS_STATUS_UPDATE_API_DOC,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get(
    "/",
    dependencies=[Depends(JWTBearer())],
    response_model=RESTResponse[TicketListData],
    summary="List tickets"
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
    dependencies=[Depends(JWTBearer())],
    response_model=RESTResponse[TicketDetailData],
    summary="Get ticket details"
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
    dependencies=[Depends(JWTBearer())],
    response_model=RESTResponse[TicketStatusData],
    summary="Get ticket status"
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
    dependencies=[Depends(JWTBearer())],
    response_model=RESTResponse[TicketStatusData],
    summary="Update ticket status"
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


list_tickets.__doc__ = TICKETS_LIST_API_DOC
get_ticket.__doc__ = TICKETS_GET_API_DOC
get_ticket_status.__doc__ = TICKETS_STATUS_GET_API_DOC
update_ticket_status.__doc__ = TICKETS_STATUS_UPDATE_API_DOC
