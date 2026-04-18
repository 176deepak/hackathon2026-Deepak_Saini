import os
import queue
import threading
import logging
import logging.handlers
from pythonjsonlogger import jsonlogger
from concurrent_log_handler import ConcurrentTimedRotatingFileHandler
from typing import ClassVar

from .config import envs
from .request_context import get_request_id


_listener = None

class ColorFormatter(logging.Formatter):
    RESET: ClassVar[str] = "\033[0m"
    LEVEL_COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }

    def __init__(self, fmt: str, *, use_color: bool = False):
        super().__init__(fmt)
        self.use_color = use_color

    def format(self, record):
        original_levelname = record.levelname
        if self.use_color:
            color = self.LEVEL_COLORS.get(original_levelname)
            if color:
                record.levelname = f"{color}{original_levelname}{self.RESET}"

        try:
            return super().format(record)
        finally:
            record.levelname = original_levelname


class LogStatus:
    START = "start"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRYING = "retrying"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"
    

class LogLayer:
    HANDLER = "handler"
    AGENT = "agent"
    TOOL = "tool"
    SERVICE = "service"
    DB = "db"
    API = "api"
    EXCEPTION = "exception"
    LIFESPAN = "lifespan"
    MIDDLEWARE = "middleware"
    ROUTER = "router"
    CACHE = "cache"
    
    
class LogCategory:
    HANDLER = "handler"
    AGENT = "agent"
    TOOL_EXECUTION = "tool_execution"
    POLICY = "policy"
    DATABASE = "database"
    API = "api"
    EXCEPTION = "exception"
    LIFESPAN = "lifespan"
    MIDDLEWARE = "middleware"
    ROUTER = "router"
    CACHE = "cache"
    
    
class LogEvent:
    # Agent lifecycle
    AGENT_RUN_START = "agent_run_start"
    AGENT_RUN_COMPLETE = "agent_run_complete"
    AGENT_RUN_FAILED = "agent_run_failed"

    # Reasoning
    AGENT_THOUGHT = "agent_thought"
    AGENT_DECISION = "agent_decision"

    # Tool execution
    TOOL_CALL = "tool_call"
    TOOL_SUCCESS = "tool_success"
    TOOL_FAILURE = "tool_failure"
    TOOL_RETRY = "tool_retry"

    # Policy evaluation
    POLICY_CHECK = "policy_check"
    POLICY_DECISION = "policy_decision"

    # Actions
    ACTION_REFUND = "action_refund"
    ACTION_REPLY = "action_reply"
    ACTION_ESCALATE = "action_escalate"

    # Errors
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ERROR = "system_error"


class AccessLogFilter(logging.Filter):
    def filter(self, record):
        return record.name == "uvicorn.access"


class AppLogFilter(logging.Filter):
    def filter(self, record):
        return record.name != "uvicorn.access"


class EmitThreadFilter(logging.Filter):
    def filter(self, record):
        # This will capture the thread name at the time of EMISSION 
        # (which should be the QueueListener thread)
        record.emit_thread = threading.current_thread().name
        return True


class AppLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.setdefault("extra", {})
        extra.setdefault("environment", envs.ENVIRONMENT)
        extra.setdefault("version", envs.APP_VERSION)

        request_id = get_request_id()
        if request_id is not None:
            extra.setdefault("request_id", request_id)

        return msg, kwargs


def setup_logging():
    global _listener
    if _listener is not None:
        return _listener

    log_queue = queue.Queue(-1)

    os.makedirs(envs.APP_LOGS_DIR, exist_ok=True)

    # Formatters
    json_formatter = jsonlogger.JsonFormatter((
        "%(levelname)s %(asctime)s %(name)s %(lineno)d "
        "%(message)s %(process)d %(thread)d"
    ))

    console_formatter = logging.Formatter(
        "%(levelname)s - %(asctime)s - %(name)s - %(lineno)d - %(message)s"
    )

    console = logging.StreamHandler()
    use_color = envs.APP_LOG_COLOR and bool(
        getattr(console.stream, "isatty", lambda: False)()
    )
    console_formatter = ColorFormatter(
        "%(levelname)s - %(asctime)s - %(name)s - %(lineno)d - %(message)s",
        use_color=use_color,
    )
    console.setFormatter(console_formatter)
    console.setLevel(envs.APP_LOG_LEVEL)

    file_handler = ConcurrentTimedRotatingFileHandler(
        os.path.join(envs.APP_LOGS_DIR, "app.jsonl"),
        when="midnight",
        backupCount=2,
        encoding="utf-8",
    )
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(envs.APP_LOG_LEVEL)
    file_handler.addFilter(AppLogFilter())
    file_handler.addFilter(EmitThreadFilter())

    # Access logs handler
    access_file_handler = ConcurrentTimedRotatingFileHandler(
        os.path.join(envs.APP_LOGS_DIR, "access.jsonl"),
        when="midnight",
        backupCount=2,
        encoding="utf-8",
    )
    access_file_handler.setFormatter(json_formatter)
    access_file_handler.setLevel(logging.INFO)
    access_file_handler.addFilter(AccessLogFilter())

    # Queue handler (used by app and intercepted loggers)
    queue_handler = logging.handlers.QueueHandler(log_queue)

    # Configure Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(envs.APP_LOG_LEVEL)
    root_logger.handlers = [queue_handler]

    # Intercept Uvicorn loggers
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [queue_handler]
        logging_logger.propagate = False

    # Listener (background thread)
    _listener = logging.handlers.QueueListener(
        log_queue,
        console,
        file_handler,
        access_file_handler,
        respect_handler_level=True,
    )

    _listener.start()
    _listener._thread.name = "LoggingBackgroundThread"
    return _listener


def extra_(
    *,
    operation: str | None = None,
    status: str | None = None,
    event: str | None = None,
    **kwargs,
) -> dict:
    payload = {}

    request_id = kwargs.get("request_id")
    if request_id is None:
        request_id = get_request_id()
    if request_id is not None:
        payload["request_id"] = request_id

    if status:
        payload["status"] = status
    if operation:
        payload["operation"] = operation
    if event:
        payload["event"] = event

    payload.update(kwargs)

    if payload.get("request_id") is None:
        payload.pop("request_id", None)

    return payload
