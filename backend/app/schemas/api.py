from datetime import datetime
from typing import Generic, Literal, TypeVar
from pydantic import BaseModel, Field


T = TypeVar("T")


class RESTResponse(BaseModel, Generic[T]):
    code: int = Field(description="HTTP status code")
    success: bool = Field(description="True if request succeeded, False otherwise")
    data: T|None = Field(default=None, description="Payload returned in the response")
    msg: str = Field(description="Detailed message about the response")


class TicketSummary(BaseModel):
    ticket_id: str
    customer_email: str
    subject: str
    status: str


class TicketListData(BaseModel):
    page: int
    limit: int
    total: int
    items: list[TicketSummary]


class TicketDetailData(BaseModel):
    ticket_id: str
    customer_email: str
    subject: str
    body: str
    status: str


class TicketStatusData(BaseModel):
    ticket_id: str
    status: str


class TicketStatusUpdateRequest(BaseModel):
    status: Literal[
        "pending",
        "processing",
        "resolved",
        "escalated",
        "waiting_for_customer",
        "failed",
    ]


class DashboardMetricsData(BaseModel):
    total_tickets: int
    resolved: int
    escalated: int
    failed: int


class DashboardRecentActivityItem(BaseModel):
    ticket_id: str
    status: str
    subject: str | None = None
    updated_at: datetime | None = None


class DashboardRecentActivityData(BaseModel):
    items: list[DashboardRecentActivityItem]


class AuditToolCallItem(BaseModel):
    tool_name: str
    status: str
    error: str | None = None
    created_at: datetime | None = None


class AuditStepItem(BaseModel):
    step_number: int
    thought: str | None = None
    action: str | None = None
    status: str
    created_at: datetime | None = None
    tool_calls: list[AuditToolCallItem]


class AuditRunItem(BaseModel):
    run_id: str
    status: str
    final_decision: str | None = None
    confidence_score: float | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    steps: list[AuditStepItem]


class AuditLogData(BaseModel):
    ticket_id: str
    runs: list[AuditRunItem]


class SystemHealthData(BaseModel):
    status: str
    database: str
    version: str
    timestamp: datetime


class SystemPingData(BaseModel):
    message: str


class AuthTokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
