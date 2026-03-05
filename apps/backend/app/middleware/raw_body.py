from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RawBodyMiddleware:
    """Capture raw request bytes and replay the body for downstream handlers."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        body = await self._read_full_body(receive)
        scope.setdefault("state", {})["raw_body"] = body

        receive_once = self._build_replay_receive(body=body)
        await self._app(scope, receive_once, send)

    @staticmethod
    async def _read_full_body(receive: Receive) -> bytes:
        chunks: list[bytes] = []
        more_body = True
        while more_body:
            message = await receive()
            if message["type"] != "http.request":
                continue
            chunks.append(message.get("body", b""))
            more_body = bool(message.get("more_body", False))
        return b"".join(chunks)

    @staticmethod
    def _build_replay_receive(*, body: bytes) -> Callable[[], Awaitable[Message]]:
        sent = False

        async def _receive() -> Message:
            nonlocal sent
            if sent:
                return {"type": "http.request", "body": b"", "more_body": False}
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        return _receive
