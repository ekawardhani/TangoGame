import asyncio
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import websockets

from gameconfig import BASE_DIR, http_port, ws_port
from gamestate import clients_lock, connected_clients, latest_state, state_lock


def run_http_server() -> None:
    """Serve the game HTML and card images from the project folder."""
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    ThreadingHTTPServer(("127.0.0.1", http_port), Handler).serve_forever()


async def ws_handler(websocket):
    with clients_lock:
        connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        with clients_lock:
            connected_clients.discard(websocket)


async def broadcast_loop() -> None:
    """Send the current game state to all connected browser clients."""
    while True:
        with state_lock:
            payload = json.dumps(latest_state)
            latest_state["message"] = ""
        with clients_lock:
            clients = list(connected_clients)
        for ws in clients:
            try:
                await ws.send(payload)
            except Exception:
                pass
        await asyncio.sleep(0.05)


async def ws_main() -> None:
    async with websockets.serve(ws_handler, "127.0.0.1", ws_port):
        await broadcast_loop()


def run_ws_server() -> None:
    asyncio.run(ws_main())
