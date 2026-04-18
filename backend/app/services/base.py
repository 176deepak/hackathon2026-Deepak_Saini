from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from app.schemas.repo import (
    CustomerOut, OrderOut, TicketOut, AgentRunOut, DashboardMetrics
)


class BaseService(ABC):
    """Base service class"""

    def __init__(self, **repos):
        """
        Accepts repositories as keyword arguments

        Example:
            BaseService(customer_repo=..., order_repo=...)
        """
        for name, repo in repos.items():
            setattr(self, name, repo)

    @staticmethod
    def _validate_non_empty(value: str, field_name: str) -> None:
        if not value or not value.strip():
            raise ValueError(f"{field_name} cannot be empty")

    @staticmethod
    def _safe_str(value: str | None) -> str:
        return value.strip() if isinstance(value, str) else ""


class BaseChunkCreationService(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def _load_kb_file(self, filepath:str):
        """Load knowledge base file

        Args:
            filepath: Knowledge base filepath

        Returns:
            Document: Langchain Document object
        """
        pass

    @abstractmethod
    def create_chunks(self, filepath: str, chunk_size: int, overlapping: int) -> list:
        """Create chunks from knowledge base files

        Args:
            filepath: Knowledge base filepath

        Returns:
            list: List of chunks
        """    
        pass


class BaseVectorIndexService(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    async def update_index(self, chunks):
        pass

    @abstractmethod
    async def query_index(self, chunks, rerank):
        pass
    
    
class BaseCustomerService(BaseService):
    @abstractmethod
    def get_customer(self, email: str) -> Optional[CustomerOut]:
        pass
    
    @abstractmethod
    def get_customer_by_id(self, customer_id: str) -> Optional[CustomerOut]:
        pass
    
    
class BaseOrderService(BaseService):
    @abstractmethod
    def get_order(self, order_id: str) -> Optional[OrderOut]:
        pass

    @abstractmethod
    def get_orders_by_customer(self, customer_id: str) -> List[OrderOut]:
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> None:
        pass

    @abstractmethod
    def mark_refunded(self, order_id: str) -> None:
        pass
    
    
class BaseTicketService(BaseService):
    @abstractmethod
    def get_ticket(self, ticket_id: str) -> Optional[TicketOut]:
        pass

    @abstractmethod
    def get_pending_tickets(self) -> List[TicketOut]:
        pass

    @abstractmethod
    def mark_processing(self, ticket_id: str) -> None:
        pass

    @abstractmethod
    def mark_resolved(self, ticket_id: str) -> None:
        pass

    @abstractmethod
    def mark_escalated(self, ticket_id: str) -> None:
        pass

    @abstractmethod
    def mark_failed(self, ticket_id: str) -> None:
        pass
    
    
class BaseAgentRunService(BaseService):
    @abstractmethod
    def start_run(self, ticket_id: str) -> AgentRunOut:
        pass

    @abstractmethod
    def complete_run(
        self,
        run_id: str,
        decision: str,
        confidence: float
    ) -> None:
        pass

    @abstractmethod
    def fail_run(self, run_id: str, error: str) -> None:
        pass
    
    
class BaseAgentStepService(BaseService):
    @abstractmethod
    def log_step(
        self,
        run_id: str,
        step_number: int,
        thought: str,
        action: str,
        input_payload: Dict[str, Any],
        output_payload: Dict[str, Any],
        status: str
    ) -> None:
        pass
    
    
class BaseToolExecutionService(BaseService):
    @abstractmethod
    def log_tool_execution(
        self,
        step_id: str,
        tool_name: str,
        request: Dict[str, Any],
        response: Dict[str, Any],
        status: str,
        error: Optional[str] = None
    ) -> None:
        pass
    
    
class BasePolicyService(BaseService):
    @abstractmethod
    def evaluate_refund(
        self,
        order: OrderOut,
        customer: CustomerOut
    ) -> Dict[str, Any]:
        """
        Returns:
        {
            "eligible": bool,
            "reason": str
        }
        """
        pass

    @abstractmethod
    def evaluate_return_window(
        self,
        order: OrderOut
    ) -> bool:
        pass

    @abstractmethod
    def detect_fraud_or_risk(
        self,
        customer: CustomerOut,
        ticket: TicketOut
    ) -> bool:
        pass
    
    
class BaseRefundService(BaseService):
    @abstractmethod
    def issue_refund(
        self,
        order_id: str,
        amount: float,
        reason: str
    ) -> None:
        pass
    
    
class BaseEscalationService(BaseService):
    @abstractmethod
    def escalate(
        self,
        ticket_id: str,
        run_id: str,
        reason: str,
        summary: str,
        priority: str
    ) -> None:
        pass
    
    
class BaseCommunicationService(BaseService):
    @abstractmethod
    def send_reply(
        self,
        ticket_id: str,
        message: str
    ) -> None:
        pass
    
    
class BaseDashboardService(BaseService):
    @abstractmethod
    def get_metrics(self) -> DashboardMetrics:
        pass
    
    
class BaseAgentService(BaseService):
    @abstractmethod
    def process_ticket(self, ticket_id: str) -> None:
        pass

    @abstractmethod
    def process_all_tickets(self) -> None:
        pass