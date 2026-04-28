import logging
import os
from typing import Any

from fastmcp import FastMCP
from orchestrator import orchestrate_goal
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="ChatGPT Orchestrator MCP",
    instructions=(
        "This MCP server exposes one entry point into the user's main "
        "orchestrator agent. Use run_orchestrator when the user asks the "
        "agent system to complete a goal."
    ),
)


@mcp.custom_route("/", methods=["GET"], include_in_schema=False)
async def root(request: Request) -> Response:
    return JSONResponse(
        {
            "status": "ok",
            "service": "ChatGPT Orchestrator MCP",
            "mcp_endpoint": "/mcp",
            "health_endpoint": "/health",
        }
    )


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health(request: Request) -> Response:
    return JSONResponse({"status": "ok"})


def call_real_orchestrator(goal: str) -> dict[str, Any]:
    return orchestrate_goal(goal)


def handle_run_orchestrator(goal: str) -> dict[str, Any]:
    clean_goal = goal.strip()

    if not clean_goal:
        return {
            "status": "error",
            "message": "The 'goal' argument is required and cannot be empty.",
        }

    try:
        return call_real_orchestrator(clean_goal)
    except Exception as exc:
        logger.exception("Orchestrator failed")
        return {
            "status": "error",
            "message": "Orchestrator failed while processing the goal.",
            "goal": clean_goal,
            "error_type": type(exc).__name__,
        }


@mcp.tool()
def run_orchestrator(goal: str) -> dict[str, Any]:
    """
    Send a goal to the main orchestrator agent and return the result.

    Args:
        goal: The task or objective that the main orchestrator should handle.
    """
    return handle_run_orchestrator(goal)


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    path = os.environ.get("MCP_PATH", "/mcp")

    mcp.run(
        transport="http",
        host=host,
        port=port,
        path=path,
    )
