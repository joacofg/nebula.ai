import json
import logging
from contextvars import ContextVar, Token
from datetime import UTC, datetime

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", request_id_context.get()),
        }
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(level: str) -> None:
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level.upper())
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level.upper())


def set_request_id(request_id: str) -> Token:
    return request_id_context.set(request_id)


def reset_request_id(token: Token) -> None:
    request_id_context.reset(token)
