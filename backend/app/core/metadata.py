from .config import envs


APP_TITLE = "Resolvr - Autonomous Support Resolution Agent"
APP_VERSION = envs.APP_VERSION

APP_DESCRIPTION = f"""Resolvr is an autonomous support resolution agent that ingests 
customer tickets, understands intent, and takes real actions - like issuing refunds,
checking orders, or escalating cases - without human intervention. It combines multi-step
reasoning, tool orchestration, and robust failure handling to resolve support requests 
at scale with full auditability.
"""

APP_SUMMARY = APP_DESCRIPTION

APP_CONTACT = {
    "name": f"{APP_TITLE} Support",
    "email": envs.APP_SUPPORT_EMAIL,
}

APP_LICENSE_INFO = {
    "name": "Proprietary",
}

OPENAPI_TAGS = [
    {
        "name": "Tickets",
        "description": (
            "Manage and fetch support tickets, their status, and outcomes."
        )
    },
    {
        "name": "Dashboard",
        "description": (
            "Aggregated metrics for dashboard like total tickets, resolved, escalated."
        )
    },
    {
        "name": "Audit Logs",
        "description": (
            "Detailed agent reasoning, tool calls, and execution logs for each ticket."
        )
    },
    {
        "name": "System",
        "description": (
            "Health checks, system status, and utility endpoints."
        )
    }
]

OPENAPI_SERVERS = [
    {
        "url": envs.APP_BASE_URL.rstrip("/"),
        "description": f"{envs.ENVIRONMENT.capitalize()} environment",
    }
]
