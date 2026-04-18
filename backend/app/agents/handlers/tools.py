from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Callable, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.clients.pg import get_pgdb
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.repositories import (
    CustomerRepo, EscalationRepo, OrderRepo, ProductRepo, RefundRepo, TicketRepo
)
from app.services.customer import CustomerService
from app.services.orders import OrderService
from app.services.product import ProductService
from app.services.tickets import TicketService

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.HANDLER,
        "category": LogCategory.HANDLER,
        "component": __name__,
    },
)


async def _run_sync_with_pg(op: Callable[[Session], dict[str, Any]]) -> dict[str, Any]:
    async for async_session in get_pgdb():
        return await async_session.run_sync(op)
    logger.error(
        "Unable to acquire database session",
        extra=extra_(operation="handler_db", status="failure"),
    )
    return {"status": "error", "message": "Unable to acquire database session"}


def _parse_uuid(value: str | None) -> Optional[UUID]:
    if not value:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _as_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _normalize_priority(priority: str) -> str:
    normalized = (priority or "").strip().lower()
    if normalized in {"low", "medium", "high", "urgent"}:
        return normalized
    return "medium"


def _evaluate_refund_eligibility(order: Any) -> dict[str, Any]:
    if order is None:
        return {"eligible": False, "reason": "Order not found"}

    if order.status != "delivered":
        return {
            "eligible": False,
            "reason": f"Order status '{order.status}' is not refundable",
        }

    if order.refund_status in {"pending", "refunded"}:
        return {
            "eligible": False,
            "reason": f"Refund already {order.refund_status}",
        }

    if order.return_deadline:
        deadline = order.return_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > deadline:
            return {
                "eligible": False,
                "reason": "Return window has expired",
            }

    return {"eligible": True, "reason": "Eligible under current return policy"}


async def handle_get_customer(
    customer_id: str | None, email: str | None
) -> dict[str, Any]:
    if not (customer_id or email):
        logger.warning(
            "Missing customer_id/email for customer lookup",
            extra=extra_(operation="handle_get_customer", status="failure"),
        )
        return {
            "status": "error",
            "message": "Either customer_id or email is required",
        }

    def _op(session: Session) -> dict[str, Any]:
        service = CustomerService(customer_repo=CustomerRepo(session))

        customer = None
        if customer_id:
            customer = service.get_customer_by_id(customer_id)

        if customer is None and email:
            customer = service.get_customer(email)

        if customer is None:
            return {"status": "not_found", "customer": None}

        return {
            "status": "found",
            "customer": {
                "customer_id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "tier": customer.tier,
            },
        }

    try:
        result = await _run_sync_with_pg(_op)
        logger.debug(
            "Customer lookup completed",
            extra=extra_(
                operation="handle_get_customer",
                status="success",
                customer_id=customer_id,
                email=email,
                result_status=result.get("status"),
            ),
        )
        return result
    except Exception:
        logger.exception(
            "Customer lookup failed",
            extra=extra_(
                operation="handle_get_customer",
                status="failure",
                customer_id=customer_id,
                email=email,
            ),
        )
        raise


async def handle_get_product(product_id: str) -> dict[str, Any]:
    def _op(session: Session) -> dict[str, Any]:
        service = ProductService(product_repo=ProductRepo(session))
        product = service.get_product(product_id)
        if product is None:
            return {"status": "not_found", "product": None}

        return {
            "status": "found",
            "product": {
                "product_id": product_id,
                "name": product.name,
                "category": product.category,
                "return_window_days": product.return_window_days,
                "warranty_months": product.warranty_months,
                "returnable": product.return_window_days > 0,
            },
        }

    try:
        result = await _run_sync_with_pg(_op)
        logger.debug(
            "Product lookup completed",
            extra=extra_(
                operation="handle_get_product",
                status="success",
                product_id=product_id,
                result_status=result.get("status"),
            ),
        )
        return result
    except Exception:
        logger.exception(
            "Product lookup failed",
            extra=extra_(operation="handle_get_product", status="failure", product_id=product_id),
        )
        raise


async def handle_get_order(order_id: str) -> dict[str, Any]:
    def _op(session: Session) -> dict[str, Any]:
        service = OrderService(order_repo=OrderRepo(session))
        order = service.get_order(order_id)
        if order is None:
            return {"status": "not_found", "order": None}

        return {
            "status": "found",
            "order": {
                "order_id": order.external_order_id,
                "customer_id": order.customer_id,
                "product_id": order.product_id,
                "status": order.status,
                "amount": order.amount,
                "return_deadline": _as_iso(order.return_deadline),
                "refund_status": order.refund_status,
                "tracking_number": order.tracking_number,
            },
        }

    try:
        result = await _run_sync_with_pg(_op)
        logger.debug(
            "Order lookup completed",
            extra=extra_(
                operation="handle_get_order",
                status="success",
                order_id=order_id,
                result_status=result.get("status"),
            ),
        )
        return result
    except Exception:
        logger.exception(
            "Order lookup failed",
            extra=extra_(operation="handle_get_order", status="failure", order_id=order_id),
        )
        raise


async def handle_check_refund_eligibility(order_id: str) -> dict[str, Any]:
    def _op(session: Session) -> dict[str, Any]:
        service = OrderService(order_repo=OrderRepo(session))
        order = service.get_order(order_id)
        return _evaluate_refund_eligibility(order=order)

    try:
        result = await _run_sync_with_pg(_op)
        logger.info(
            "Refund eligibility evaluated",
            extra=extra_(
                operation="handle_check_refund_eligibility",
                status="success",
                order_id=order_id,
                eligible=result.get("eligible"),
            ),
        )
        return result
    except Exception:
        logger.exception(
            "Refund eligibility evaluation failed",
            extra=extra_(
                operation="handle_check_refund_eligibility",
                status="failure",
                order_id=order_id,
            ),
        )
        raise


async def handle_issue_refund(order_id: str, amount: float) -> dict[str, Any]:
    if amount <= 0:
        logger.warning(
            "Invalid refund amount",
            extra=extra_(
                operation="handle_issue_refund",
                status="failure",
                order_id=order_id,
                amount=amount,
            ),
        )
        return {
            "status": "failed",
            "message": "Refund amount must be greater than 0",
        }

    def _op(session: Session) -> dict[str, Any]:
        order_service = OrderService(order_repo=OrderRepo(session))
        refund_repo = RefundRepo(session)

        order = order_service.get_order(order_id)
        if order is None:
            return {"status": "failed", "message": "Order not found"}

        if amount > order.amount:
            return {
                "status": "failed",
                "message": "Refund amount cannot exceed order amount",
            }

        eligibility = _evaluate_refund_eligibility(order=order)
        if not eligibility.get("eligible", False):
            return {
                "status": "failed",
                "message": f"Order is not eligible: {eligibility.get('reason')}",
            }

        refund_repo.create_refund(
            order_id=order.id,
            amount=amount,
            reason="refund issued by support agent",
            initiated_by="agent",
        )
        order_service.mark_refunded(order_id)

        return {
            "status": "success",
            "message": "Refund processed successfully",
        }

    try:
        result = await _run_sync_with_pg(_op)
        logger.info(
            "Refund attempt completed",
            extra=extra_(
                operation="handle_issue_refund",
                status="success" if result.get("status") == "success" else "failure",
                order_id=order_id,
                amount=amount,
                result_status=result.get("status"),
            ),
        )
        return result
    except Exception:
        logger.exception(
            "Refund attempt failed",
            extra=extra_(
                operation="handle_issue_refund",
                status="failure",
                order_id=order_id,
                amount=amount,
            ),
        )
        raise


async def handle_send_reply(ticket_id: str, message: str) -> dict[str, Any]:
    if not message or not message.strip():
        logger.warning(
            "Empty reply message rejected",
            extra=extra_(
                operation="handle_send_reply",
                status="failure",
                ticket_id=ticket_id,
            ),
        )
        return {"status": "failed", "message": "Message cannot be empty"}

    def _op(session: Session) -> dict[str, Any]:
        ticket_repo = TicketRepo(session)
        sent = ticket_repo.create_message(
            ticket_ref=ticket_id,
            sender_type="agent",
            message=message.strip(),
        )
        if not sent:
            return {"status": "failed", "message": "Ticket not found"}
        return {"status": "sent"}

    try:
        result = await _run_sync_with_pg(_op)
        logger.info(
            "Reply send attempt completed",
            extra=extra_(
                operation="handle_send_reply",
                status="success" if result.get("status") == "sent" else "failure",
                ticket_id=ticket_id,
                result_status=result.get("status"),
            ),
        )
        return result
    except Exception:
        logger.exception(
            "Reply send attempt failed",
            extra=extra_(operation="handle_send_reply", status="failure", ticket_id=ticket_id),
        )
        raise


async def handle_escalate(
    ticket_id: str,
    summary: str,
    priority: str,
    run_id: str | None,
) -> dict[str, Any]:
    def _op(session: Session) -> dict[str, Any]:
        ticket_repo = TicketRepo(session)
        ticket = ticket_repo.get_by_reference(ticket_id)
        if ticket is None:
            return {"status": "failed", "message": "Ticket not found"}

        ticket_service = TicketService(ticket_repo=ticket_repo)
        ticket_service.mark_escalated(ticket.id)

        parsed_run_id = _parse_uuid(run_id)
        if parsed_run_id is not None:
            escalation_repo = EscalationRepo(session)
            escalation_repo.create_escalation(
                ticket_id=ticket.id,
                run_id=str(parsed_run_id),
                reason="Agent requested manual intervention",
                summary=(summary or "").strip() or "No summary provided",
                priority=_normalize_priority(priority),
            )

        return {
            "status": "escalated",
            "assigned_to": "human_agent",
            "ticket_id": ticket.external_ticket_id,
        }

    try:
        result = await _run_sync_with_pg(_op)
        logger.warning(
            "Escalation completed",
            extra=extra_(
                operation="handle_escalate",
                status="success" if result.get("status") == "escalated" else "failure",
                ticket_id=ticket_id,
                priority=priority,
                run_id=run_id,
                result_status=result.get("status"),
            ),
        )
        return result
    except Exception:
        logger.exception(
            "Escalation failed",
            extra=extra_(
                operation="handle_escalate",
                status="failure",
                ticket_id=ticket_id,
                priority=priority,
                run_id=run_id,
            ),
        )
        raise
