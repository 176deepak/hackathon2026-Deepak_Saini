import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base

from .enums import (
    AgentRunStatus, CustomerTier, EscalationStatus, OrderStatus, RefundStatus, 
    TicketStatus, ToolExecutionStatus
)

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_customer_id = Column(String, unique=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String)

    tier = Column(SQLEnum(CustomerTier), default=CustomerTier.STANDARD)

    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)

    member_since = Column(DateTime)

    has_return_exception = Column(Boolean, default=False)
    risk_flag = Column(Boolean, default=False)

    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_product_id = Column(String, unique=True, index=True)

    name = Column(String, nullable=False)
    category = Column(String)

    price = Column(Float)

    warranty_months = Column(Integer)
    return_window_days = Column(Integer)

    is_returnable = Column(Boolean, default=True)

    requires_seal_intact = Column(Boolean, default=False)
    is_high_value = Column(Boolean, default=False)

    notes = Column(Text)


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_order_id = Column(String, unique=True, index=True)

    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))

    quantity = Column(Integer)
    amount = Column(Float)

    status = Column(SQLEnum(OrderStatus))

    order_date = Column(DateTime)
    delivery_date = Column(DateTime)

    return_deadline = Column(DateTime)

    refund_status = Column(SQLEnum(RefundStatus), default=RefundStatus.NONE)

    tracking_number = Column(String)

    is_registered_device = Column(Boolean, default=False)

    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer")
    product = relationship("Product")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_ticket_id = Column(String, unique=True, index=True)

    customer_email = Column(String, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)

    subject = Column(String)
    body = Column(Text)

    source = Column(String)

    priority = Column(String)

    status = Column(SQLEnum(TicketStatus), default=TicketStatus.PENDING)

    category = Column(String)

    detected_intent = Column(JSONB)

    requires_clarification = Column(Boolean, default=False)

    contains_threat = Column(Boolean, default=False)
    contains_fraud_signal = Column(Boolean, default=False)

    created_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    expected_action = Column(String)

    customer = relationship("Customer")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"))

    status = Column(SQLEnum(AgentRunStatus))

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)

    final_decision = Column(String)
    confidence_score = Column(Float)

    failure_reason = Column(Text)

    total_steps = Column(Integer)
    total_tool_calls = Column(Integer)

    ticket = relationship("Ticket")


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"))

    step_number = Column(Integer)

    thought = Column(Text)
    decision = Column(Text)

    action_type = Column(String)
    tool_name = Column(String)

    input_payload = Column(JSONB)
    output_payload = Column(JSONB)

    status = Column(String)

    latency_ms = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    agent_run = relationship("AgentRun")


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    agent_step_id = Column(UUID(as_uuid=True), ForeignKey("agent_steps.id"))

    tool_name = Column(String)

    request_payload = Column(JSONB)
    response_payload = Column(JSONB)

    status = Column(SQLEnum(ToolExecutionStatus))

    error_message = Column(Text)

    retry_count = Column(Integer, default=0)

    latency_ms = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    agent_step = relationship("AgentStep")


class PolicyEvaluation(Base):
    __tablename__ = "policy_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"))
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))

    is_within_return_window = Column(Boolean)
    is_under_warranty = Column(Boolean)

    is_returnable = Column(Boolean)

    is_exception_applied = Column(Boolean)

    decision = Column(String)
    reason = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))

    amount = Column(Float)

    status = Column(String)

    initiated_by = Column(String)

    reason = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"))
    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"))

    reason = Column(Text)
    summary = Column(Text)

    priority = Column(String)

    assigned_to = Column(String)

    status = Column(SQLEnum(EscalationStatus), default=EscalationStatus.PENDING)

    created_at = Column(DateTime, default=datetime.utcnow)


class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"))

    sender_type = Column(String)

    message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


class DeadLetterQueue(Base):
    __tablename__ = "dead_letter_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"))

    reason = Column(Text)

    payload_json = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow)
