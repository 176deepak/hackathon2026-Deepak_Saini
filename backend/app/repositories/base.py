from abc import ABC, abstractmethod
from typing import Optional, List
from app.schemas.repo import (
    CustomerOut, ProductOut, OrderOut, TicketOut, AgentRunOut, DashboardMetrics
)


class BaseRepo(ABC):
    """Base Repo Skeleton"""

    def __init__(self, db):
        self.db = db
        

class BaseCustomerRepo(BaseRepo):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[CustomerOut]:
        pass

    @abstractmethod
    def get_by_external_id(self, external_id: str) -> Optional[CustomerOut]:
        pass
    
    
class BaseProductRepo(BaseRepo):
    @abstractmethod
    def get_by_external_id(self, product_id: str) -> Optional[ProductOut]:
        pass
    
    
class BaseOrderRepo(BaseRepo):

    @abstractmethod
    def get_by_external_id(self, order_id: str) -> Optional[OrderOut]:
        pass

    @abstractmethod
    def get_by_customer(self, customer_id: str) -> list[OrderOut]:
        pass

    @abstractmethod
    def update_status(self, order_id: str, status: str) -> None:
        pass

    @abstractmethod
    def update_refund_status(self, order_id: str, status: str) -> None:
        pass
    

class BaseTicketRepo(BaseRepo):

    @abstractmethod
    def get_by_id(self, ticket_id: str) -> Optional[TicketOut]:
        pass

    @abstractmethod
    def get_all_pending(self) -> List[TicketOut]:
        pass

    @abstractmethod
    def update_status(self, ticket_id: str, status: str) -> None:
        pass
    
    
class BaseAgentRunRepo(BaseRepo):
    @abstractmethod
    def create_run(self, ticket_id: str) -> AgentRunOut:
        pass

    @abstractmethod
    def complete_run(
        self, run_id: str, status: str, decision: str, confidence: float
    ) -> None:
        pass

    @abstractmethod
    def fail_run(self, run_id: str, error: str) -> None:
        pass
    
    
class BaseAgentStepRepo(BaseRepo):

    @abstractmethod
    def log_step(
        self,
        run_id: str,
        step_number: int,
        thought: str,
        action: str,
        input_payload: dict,
        output_payload: dict,
        status: str
    ) -> None:
        pass
    
    
class BaseToolExecutionRepo(BaseRepo):

    @abstractmethod
    def log_tool_call(
        self,
        step_id: str,
        tool_name: str,
        request: dict,
        response: dict,
        status: str,
        error: str = None
    ) -> None:
        pass
    
    
class BaseRefundRepo(BaseRepo):

    @abstractmethod
    def create_refund(
        self, order_id: str, amount: float, reason: str, initiated_by: str
    ) -> None:
        pass
    
    
class BaseEscalationRepo(BaseRepo):

    @abstractmethod
    def create_escalation(
        self, ticket_id: str, run_id: str, reason: str, summary: str, priority: str
    ) -> None:
        pass
    
    
class BaseDashboardRepo(BaseRepo):

    @abstractmethod
    def get_metrics(self) -> DashboardMetrics:
        pass