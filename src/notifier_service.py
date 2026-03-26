"""Notifier Service - FastAPI webhook receiver for GitHub events.

This service receives GitHub webhooks, validates signatures, triages events,
and queues tasks for the Sentinel to process.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import sys
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Environment variables
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

app = FastAPI(
    title="workflow-orchestration-queue Notifier",
    description="Webhook receiver for GitHub events",
    version="0.1.0",
)


def verify_signature(payload: bytes, signature: str | None) -> bool:
    """Verify the X-Hub-Signature-256 header.

    Args:
        payload: The raw request body bytes.
        signature: The signature header value.

    Returns:
        True if signature is valid, False otherwise.
    """
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET not set - signature verification disabled")
        return True

    if not signature:
        return False

    if not signature.startswith("sha256="):
        return False

    expected_sig = signature[7:]  # Remove 'sha256=' prefix
    computed_sig = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected_sig, computed_sig)


@app.post("/webhooks/github")
async def handle_github_webhook(
    request: Request,
    x_github_event: str | None = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256"),
) -> JSONResponse:
    """Handle incoming GitHub webhook events.

    Args:
        request: The FastAPI request object.
        x_github_event: The GitHub event type header.
        x_hub_signature_256: The HMAC signature header.

    Returns:
        JSON response acknowledging the event.

    Raises:
        HTTPException: If signature verification fails.
    """
    # Read raw body for signature verification
    payload = await request.body()

    # Verify signature
    if not verify_signature(payload, x_hub_signature_256):
        logger.warning("Invalid webhook signature - rejecting request")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse JSON body
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON body: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = x_github_event or "unknown"
    logger.info(f"Received GitHub event: {event_type}")

    # Handle different event types
    if event_type == "issues":
        await handle_issue_event(data)
    elif event_type == "issue_comment":
        await handle_issue_comment_event(data)
    elif event_type == "pull_request":
        await handle_pull_request_event(data)
    else:
        logger.debug(f"Ignoring event type: {event_type}")

    # Return 202 Accepted immediately (GitHub expects response within 10s)
    return JSONResponse(status_code=202, content={"status": "accepted"})


async def handle_issue_event(data: dict[str, Any]) -> None:
    """Handle GitHub issues events.

    Args:
        data: The webhook payload.
    """
    action = data.get("action", "")
    issue = data.get("issue", {})
    labels = [l["name"] for l in issue.get("labels", [])]

    # Check for orchestration dispatch label
    if action == "opened" and "orchestration:dispatch" in labels:
        logger.info(f"New orchestration dispatch issue: {issue.get('number')}")
        # Queue the task by ensuring agent:queued label
        # TODO: Implement actual queueing via GitHubQueue


async def handle_issue_comment_event(data: dict[str, Any]) -> None:
    """Handle GitHub issue_comment events.

    Args:
        data: The webhook payload.
    """
    action = data.get("action", "")
    comment = data.get("comment", {})
    issue = data.get("issue", {})

    logger.debug(f"Issue comment {action} on issue {issue.get('number')}")
    # TODO: Implement comment-based triggers


async def handle_pull_request_event(data: dict[str, Any]) -> None:
    """Handle GitHub pull_request events.

    Args:
        data: The webhook payload.
    """
    action = data.get("action", "")
    pr = data.get("pull_request", {})

    logger.debug(f"Pull request {action}: {pr.get('number')}")
    # TODO: Implement PR-based triggers


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Simple health status.
    """
    return {"status": "healthy"}


def main() -> None:
    """Main entry point for the Notifier service."""
    # Validate environment
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET not set - signature verification disabled")
    if not GITHUB_REPO:
        logger.error("GITHUB_REPO environment variable is required")
        sys.exit(1)
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN environment variable is required")
        sys.exit(1)

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
