"""Utility helpers for launching the Tauri overlay binary and exchanging
JSON messages with its frontend via WebSockets.

This module is intentionally lightweight and suitable for prototyping.
"""
from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from subprocess import Popen
from threading import Event, Thread
from typing import Any, Dict, Optional, Set

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise RuntimeError(
        "overlay_bridge requires the 'websockets' package. Install it with "
        "`uv add websockets` or `pip install websockets`."
    ) from exc


@dataclass
class BridgeConfig:
    """Runtime configuration for the overlay bridge."""

    host: str = "127.0.0.1"
    port: int = 4737
    startup_timeout: float = 5.0
    shutdown_timeout: float = 3.0
    env: Optional[Dict[str, str]] = None


class OverlayBridge(AbstractContextManager["OverlaySession"]):
    """Manage the overlay process lifecycle and WebSocket bridge."""

    def __init__(
        self,
        binary_path: Path,
        *,
        config: Optional[BridgeConfig] = None,
    ) -> None:
        self._binary_path = Path(binary_path).expanduser().resolve()
        self._config = config or BridgeConfig()
        self._loop = asyncio.new_event_loop()
        self._loop_thread = Thread(target=self._loop.run_forever, daemon=True)
        self._loop_thread.start()
        self._server_ready = Event()
        self._clients: Set[WebSocketServerProtocol] = set()
        self._process: Optional[Popen[bytes]] = None

    # ------------------------------------------------------------------
    # Context manager API
    # ------------------------------------------------------------------
    def __enter__(self) -> "OverlaySession":
        self._start_server()
        self._launch_process()
        return OverlaySession(self)

    def __exit__(self, exc_type, exc, tb) -> Optional[bool]:
        self.close()
        return None

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def send(self, payload: Dict[str, Any]) -> None:
        """Broadcast a JSON payload to all connected overlay clients."""

        async def _broadcast() -> None:
            if not self._clients:
                return
            message = json.dumps(payload)
            await asyncio.gather(
                *(client.send(message) for client in list(self._clients)),
                return_exceptions=True,
            )

        future = asyncio.run_coroutine_threadsafe(_broadcast(), self._loop)
        future.result(timeout=self._config.shutdown_timeout)

    def close(self) -> None:
        """Terminate the overlay process and stop the WebSocket server."""
        if self._process and self._process.poll() is None:
            if sys.platform == "win32":
                self._process.terminate()
            else:
                self._process.send_signal(signal.SIGTERM)
            try:
                self._process.wait(timeout=self._config.shutdown_timeout)
            except TimeoutError:
                self._process.kill()
        self._process = None

        async def _shutdown() -> None:
            for client in list(self._clients):
                await client.close()
            self._clients.clear()
            server = getattr(self, "_server", None)
            if server is not None:
                server.close()
                await server.wait_closed()

        future = asyncio.run_coroutine_threadsafe(_shutdown(), self._loop)
        try:
            future.result(timeout=self._config.shutdown_timeout)
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop_thread.join(timeout=1.0)

    # ------------------------------------------------------------------
    # Internal plumbing
    # ------------------------------------------------------------------
    def _start_server(self) -> None:
        async def handler(websocket: WebSocketServerProtocol) -> None:
            self._clients.add(websocket)
            try:
                async for message in websocket:
                    # Echo back any messages so callers can observe responses.
                    await websocket.send(message)
            finally:
                self._clients.discard(websocket)

        async def start() -> None:
            server = await websockets.serve(
                handler,
                self._config.host,
                self._config.port,
            )
            self._server = server
            self._server_ready.set()

        future = asyncio.run_coroutine_threadsafe(start(), self._loop)
        future.result(timeout=self._config.startup_timeout)

    def _launch_process(self) -> None:
        if not self._binary_path.exists():
            raise FileNotFoundError(f"Tauri binary not found: {self._binary_path}")

        env = os.environ.copy()
        env.update(
            {
                "OVERLAY_SOCKET": f"ws://{self._config.host}:{self._config.port}",
                **(self._config.env or {}),
            }
        )
        self._process = Popen([str(self._binary_path)], env=env)


class OverlaySession:
    """Proxy object exposed to callers when using the context manager."""

    def __init__(self, bridge: OverlayBridge) -> None:
        self._bridge = bridge

    def send(self, payload: Dict[str, Any]) -> None:
        self._bridge.send(payload)

    def close(self) -> None:
        self._bridge.close()

    # Allow usage both as context manager and simple helper.
    def __enter__(self) -> "OverlaySession":  # pragma: no cover - convenience
        return self

    def __exit__(self, exc_type, exc, tb) -> Optional[bool]:  # pragma: no cover
        self.close()
        return None
