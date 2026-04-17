from enum import Enum


class CustomerTier(Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    VIP = "vip"


class TicketStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    WAITING_FOR_CUSTOMER = "waiting_for_customer"
    FAILED = "failed"


class OrderStatus(Enum):
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class RefundStatus(Enum):
    NONE = "none"
    PENDING = "pending"
    REFUNDED = "refunded"


class AgentRunStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class ToolExecutionStatus(Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    MALFORMED = "malformed"
    FAILED = "failed"


class EscalationStatus(Enum):
    PENDING = "pending"
    RESOLVED = "resolved"