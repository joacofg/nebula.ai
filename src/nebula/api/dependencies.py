from fastapi import Request

from nebula.core.container import ServiceContainer
from nebula.services.chat_service import ChatService


def get_container(request_or_app) -> ServiceContainer:
    app = request_or_app.app if isinstance(request_or_app, Request) else request_or_app
    return app.state.container


def get_chat_service(request: Request) -> ChatService:
    return get_container(request).chat_service
