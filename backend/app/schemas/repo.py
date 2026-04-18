from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CustomerOut(BaseModel):
    id: str
    email: str
    name: str
    tier: str


class ProductOut(BaseModel):
    id: str
    name: str
    category: str
    return_window_days: int
    warranty_months: int


class OrderOut(BaseModel):
    id: str
    external_order_id: str
    customer_id: str
    product_id: str
    status: str
    amount: float
    return_deadline: Optional[datetime]
    refund_status: Optional[str]
    tracking_number: Optional[str]


class TicketOut(BaseModel):
    id: str
    external_ticket_id: str
    customer_email: str
    subject: str
    body: str
    status: str


class AgentRunOut(BaseModel):
    id: str
    ticket_id: str
    status: str
    final_decision: Optional[str]
    confidence_score: Optional[float]
    started_at: datetime
    ended_at: Optional[datetime]


class AgentStepOut(BaseModel):
    id: str
    agent_run_id: str
    step_number: int
    thought: Optional[str]
    action: Optional[str]
    status: str
    created_at: datetime


class ToolExecutionOut(BaseModel):
    id: str
    tool_name: str
    status: str
    error_message: Optional[str]
    latency_ms: Optional[int]


class DashboardMetrics(BaseModel):
    total_tickets: int
    resolved: int
    escalated: int
    failed: int