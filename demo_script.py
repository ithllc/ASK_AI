#!/usr/bin/env python3
"""
ASK AI Skills Builder - Demo Script

Demonstrates the full agent workflow by:
1. Starting the FastAPI server
2. Connecting via WebSocket
3. Walking through a complete conversation
4. Showing all agent status transitions

Usage:
    python demo_script.py
    # or for interactive mode:
    python demo_script.py --interactive
"""

import asyncio
import json
import subprocess
import sys
import time
import signal

# Demo conversation steps
DEMO_CONVERSATION = [
    {
        "delay": 2,
        "input": None,
        "description": "Agent sends introduction",
    },
    {
        "delay": 3,
        "input": "building dApps on Base blockchain",
        "description": "User asks about Base blockchain dApp development",
    },
    {
        "delay": 5,
        "input": "1",
        "description": "User selects the first result from search",
    },
]


def print_banner():
    print("\n" + "=" * 60)
    print("  ASK AI Skills Builder - Demo Script")
    print("  " + "-" * 40)
    print("  Port: 8074")
    print("  Mode: Automated Demo")
    print("=" * 60 + "\n")


def print_status(msg, icon="-->"):
    print(f"  {icon} {msg}")


def print_agent_msg(content):
    # Truncate long messages for demo output
    lines = content.split("\n")
    for line in lines[:10]:
        print(f"  AGENT: {line}")
    if len(lines) > 10:
        print(f"  AGENT: ... ({len(lines) - 10} more lines)")


def print_user_msg(content):
    print(f"  USER:  {content}")


async def run_demo():
    """Run the automated demo conversation via WebSocket."""
    try:
        import websockets
    except ImportError:
        print("Installing websockets...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
        import websockets

    print_banner()

    # Start the server
    print_status("Starting FastAPI server on port 8074...", "[1]")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", "8074", "--log-level", "warning"],
        cwd="/llm_models_python_code_src/ASK_AI",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    time.sleep(3)
    if server_proc.poll() is not None:
        print_status("Server failed to start!", "[!]")
        stderr = server_proc.stderr.read().decode()
        print(f"  Error: {stderr[:500]}")
        return

    print_status("Server started successfully", "[+]")
    print_status("Web interface available at: http://localhost:8074", "[+]")
    print()

    try:
        # Connect via WebSocket
        print_status("Connecting to WebSocket...", "[2]")
        async with websockets.connect("ws://localhost:8074/ws") as ws:
            print_status("Connected!", "[+]")
            print()

            for step_num, step in enumerate(DEMO_CONVERSATION):
                print(f"\n  --- Step {step_num + 1}: {step['description']} ---")

                if step["input"] is None:
                    # Just wait for agent messages
                    print_status(f"Waiting {step['delay']}s for agent response...")
                else:
                    # Wait a bit then send input
                    await asyncio.sleep(step["delay"])
                    print_user_msg(step["input"])
                    await ws.send(json.dumps({
                        "type": "message",
                        "content": step["input"],
                    }))

                # Collect responses for a window
                deadline = time.time() + step["delay"] + 5
                while time.time() < deadline:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        data = json.loads(msg)

                        if data["type"] == "status":
                            status = data["status"]
                            detail = data.get("detail", "")
                            icon = {
                                "ready": "[*]",
                                "searching": "[~]",
                                "deep_search": "[~]",
                                "results_found": "[+]",
                                "site_selected": "[+]",
                                "checking_docs": "[~]",
                                "docs_found": "[+]",
                                "no_docs": "[!]",
                                "checking_ask_ai": "[~]",
                                "ask_ai_found": "[+]",
                                "interacting": "[~]",
                                "extracting": "[~]",
                                "complete": "[+]",
                                "error": "[!]",
                                "ended": "[.]",
                            }.get(status, "[?]")
                            print_status(f"STATUS: {status} - {detail}", icon)

                        elif data["type"] == "message":
                            sender = data.get("sender", "agent")
                            if sender == "agent":
                                print_agent_msg(data["content"])

                    except asyncio.TimeoutError:
                        break
                    except Exception as e:
                        print_status(f"Error: {e}", "[!]")
                        break

            print("\n" + "=" * 60)
            print("  Demo Complete!")
            print("  " + "-" * 40)
            print("  The web interface is still running at:")
            print("  http://localhost:8074")
            print()
            print("  You can open it in a browser to interact manually.")
            print("  Press Ctrl+C to stop the server.")
            print("=" * 60 + "\n")

            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass

    except Exception as e:
        print_status(f"Demo error: {e}", "[!]")
    finally:
        print_status("Shutting down server...")
        server_proc.terminate()
        server_proc.wait(timeout=5)
        print_status("Server stopped.")


async def run_interactive():
    """Run in interactive mode - just start the server."""
    print_banner()
    print_status("Starting server in interactive mode...")
    print_status("Open http://localhost:8074 in your browser")
    print_status("Press Ctrl+C to stop")
    print()

    import uvicorn
    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=8074,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


def main():
    interactive = "--interactive" in sys.argv or "-i" in sys.argv

    try:
        if interactive:
            asyncio.run(run_interactive())
        else:
            asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n  Stopped by user.")


if __name__ == "__main__":
    main()
