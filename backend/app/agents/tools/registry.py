from .common import search_knowledge_base
from .customer import get_customer
from .orders import get_product, get_order
from .tickets import check_refund_eligibility, issue_refund, send_reply, escalate


ticket_agent_tools = [
    search_knowledge_base,
    get_customer,
    get_product,
    get_order,
    check_refund_eligibility,
    issue_refund,
    send_reply,
    escalate
]
ticket_agent_tools_mapper = {tool.name:tool for tool in ticket_agent_tools}
