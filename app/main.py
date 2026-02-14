"""
ASK AI Skills Builder - Web Application

FastAPI server with WebSocket support for real-time agent communication.
Serves the web interface on port 8074.

Usage:
    python -m app.main
    # or
    uvicorn app.main:app --host 0.0.0.0 --port 8074
"""

import asyncio
import json
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.agent import ConversationAgent

app = FastAPI(
    title="ASK AI Skills Builder",
    version="0.2.0",
    description="Interactive agent for discovering and using ASK AI features on documentation sites",
)

# Static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    """Serve the main web interface."""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "version": "0.2.0"})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent communication."""
    await websocket.accept()

    agent = ConversationAgent()

    async def status_callback(status: str, detail: str = ""):
        try:
            await websocket.send_json({
                "type": "status",
                "status": status,
                "detail": detail,
            })
        except Exception:
            pass

    async def message_callback(message: str, sender: str = "agent"):
        try:
            await websocket.send_json({
                "type": "message",
                "sender": sender,
                "content": message,
            })
        except Exception:
            pass

    agent.on_status = status_callback
    agent.on_message = message_callback

    # Send introduction
    await agent.introduce()

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                user_input = msg.get("content", "")
            except json.JSONDecodeError:
                user_input = data

            if user_input:
                # Echo user message back for display
                await websocket.send_json({
                    "type": "message",
                    "sender": "user",
                    "content": user_input,
                })
                await agent.handle_input(user_input)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WebSocket] Error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8074)
