import json
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.core.config import envs
from app.models import (
    Base, Customer, Product, Order, Ticket, CustomerTier, OrderStatus, RefundStatus
)

DATABASE_URL = (
    f"postgresql://{envs.PG_DB_USER}:{envs.PG_DB_PASSWORD}@"
    f"{envs.PG_DB_HOST}:{envs.PG_DB_PORT}/{envs.PG_DB_NAME}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_datetime(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seed_customers(session, customers_data):
    existing = {
        c.external_customer_id: c
        for c in session.query(Customer).all()
    }

    for c in customers_data:
        if c["customer_id"] in existing:
            continue

        customer = Customer(
            external_customer_id=c["customer_id"],
            name=c["name"],
            email=c["email"],
            phone=c["phone"],
            tier=CustomerTier(c["tier"]),
            total_orders=c["total_orders"],
            total_spent=c["total_spent"],
            member_since=parse_datetime(c["member_since"]),
            has_return_exception="exception" in c["notes"].lower(),
            risk_flag="chargeback" in c["notes"].lower(),
            notes=c["notes"]
        )
        session.add(customer)

    session.commit()


def seed_products(session, products_data):
    existing = {
        p.external_product_id: p
        for p in session.query(Product).all()
    }

    for p in products_data:
        if p["product_id"] in existing:
            continue

        product = Product(
            external_product_id=p["product_id"],
            name=p["name"],
            category=p["category"],
            price=p["price"],
            warranty_months=p["warranty_months"],
            return_window_days=p["return_window_days"],
            is_returnable=p["returnable"],
            requires_seal_intact="seal" in p["notes"].lower(),
            is_high_value=p["price"] > 200,
            notes=p["notes"]
        )
        session.add(product)

    session.commit()


def seed_orders(session, orders_data):
    customers = {
        c.external_customer_id: c.id
        for c in session.query(Customer).all()
    }

    products = {
        p.external_product_id: p.id
        for p in session.query(Product).all()
    }

    existing = {
        o.external_order_id: o
        for o in session.query(Order).all()
    }

    for o in orders_data:
        if o["order_id"] in existing:
            continue

        order = Order(
            external_order_id=o["order_id"],
            customer_id=customers.get(o["customer_id"]),
            product_id=products.get(o["product_id"]),
            quantity=o["quantity"],
            amount=o["amount"],
            status=OrderStatus(o["status"]),
            order_date=parse_datetime(o["order_date"]),
            delivery_date=parse_datetime(o["delivery_date"]),
            return_deadline=parse_datetime(o["return_deadline"]),
            refund_status=RefundStatus(o["refund_status"]) if o["refund_status"] \
                else RefundStatus.NONE,
            tracking_number=(
                o["notes"].split("Tracking: ")[-1] if "Tracking:" in o["notes"] \
                    else None
            ),
            is_registered_device="registered" in o["notes"].lower(),
            notes=o["notes"]
        )
        session.add(order)

    session.commit()


def seed_tickets(session, tickets_data):
    customers = {
        c.email: c.id
        for c in session.query(Customer).all()
    }

    existing = {
        t.external_ticket_id: t
        for t in session.query(Ticket).all()
    }

    for t in tickets_data:
        if t["ticket_id"] in existing:
            continue

        ticket = Ticket(
            external_ticket_id=t["ticket_id"],
            customer_email=t["customer_email"],
            customer_id=customers.get(t["customer_email"]),
            subject=t["subject"],
            body=t["body"],
            source=t["source"],
            priority="high" if t["tier"] == 3 else "medium",
            created_at=parse_datetime(t["created_at"]),
            expected_action=t["expected_action"]
        )
        session.add(ticket)

    session.commit()


def run_seed():
    session = SessionLocal()

    customers = load_json("data/customers.json")
    products = load_json("data/products.json")
    orders = load_json("data/orders.json")
    tickets = load_json("data/tickets.json")

    print("Seeding customers...")
    seed_customers(session, customers)

    print("Seeding products...")
    seed_products(session, products)

    print("Seeding orders...")
    seed_orders(session, orders)

    print("Seeding tickets...")
    seed_tickets(session, tickets)

    print("Seeding complete!")


if __name__ == "__main__":
    run_seed()