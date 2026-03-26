"""Sentinel Orchestrator - Background polling and dispatch service.

This is the main entry point for the Sentinel service that continuously
polls for queued tasks, claims them, and dispatches workers.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from typing import Any

from src.models.work_item import WorkItemStatus
from src.queue.github_queue import GitHubQueue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Environment variables
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))
MAX_BACKOFF = int(os.environ.get("MAX_BACKOFF", "960"))
SENTINEL_ID = os.environ.get("SENTINEL_ID", "sentinel-001")
SENTINEL_BOT_LOGIN = os.environ.get("SENTINEL_BOT_LOGIN", "")
HEARTBEAT_INTERVAL = int(os.environ.get("HEARTBEAT_INTERVAL", "300"))

# Graceful shutdown flag
_shutdown_requested = False


def handle_shutdown(signum: int, frame: Any) -> None:
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    logger.info(f"Received signal {signum}, requesting graceful shutdown...")
    _shutdown_requested = True


async def heartbeat_loop(item_id: str, start_time: float) -> None:
    """Post heartbeat comments during long-running tasks.

    Args:
        item_id: The issue number being processed.
        start_time: The timestamp when processing started.
    """
    queue = GitHubQueue()
    try:
        while not _shutdown_requested:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            elapsed = asyncio.get_event_loop().time() - start_time
            comment = f"⏱️ **Heartbeat**: Sentinel {SENTINEL_ID} is still working. Elapsed: {int(elapsed // 60)} minutes."
            await queue.update_item_status(item_id, WorkItemStatus.IN_PROGRESS, comment)
    finally:
        await queue.close()


async def process_task(item_id: str) -> bool:
    """Process a single work item.

    Args:
        item_id: The issue number to process.

    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"Processing task {item_id}")
    # TODO: Implement actual task processing via devcontainer-opencode.sh
    # This is a placeholder for Phase 1 MVP
    await asyncio.sleep(5)  # Simulate work
    return True


async def polling_loop(queue: GitHubQueue) -> None:
    """Main polling loop for task discovery.

    Args:
        queue: The GitHub queue instance.
    """
    global _shutdown_requested
    current_backoff = POLL_INTERVAL

    while not _shutdown_requested:
        try:
            # Fetch queued items
            items = await queue.fetch_queued_items()

            if items:
                logger.info(f"Found {len(items)} queued items")
                current_backoff = POLL_INTERVAL  # Reset backoff on success

                for item in items:
                    if _shutdown_requested:
                        break

                    # Attempt to claim the task
                    if SENTINEL_BOT_LOGIN:
                        claimed = await queue.claim_task(item.id, SENTINEL_BOT_LOGIN)
                        if not claimed:
                            logger.info(f"Skipping item {item.id} - already claimed")
                            continue
                    else:
                        logger.warning("SENTINEL_BOT_LOGIN not set - locking disabled")

                    # Update status to in-progress
                    await queue.update_item_status(
                        item.id,
                        WorkItemStatus.IN_PROGRESS,
                        f"🤖 Sentinel {SENTINEL_ID} is starting work on this issue.",
                    )

                    # Start heartbeat task
                    start_time = asyncio.get_event_loop().time()
                    heartbeat_task = asyncio.create_task(heartbeat_loop(item.id, start_time))

                    try:
                        # Process the task
                        success = await process_task(item.id)

                        # Update final status
                        final_status = WorkItemStatus.SUCCESS if success else WorkItemStatus.ERROR
                        await queue.update_item_status(
                            item.id,
                            final_status,
                            f"{'✅' if success else '❌'} Task {'completed' if success else 'failed'}.",
                        )

                    finally:
                        # Cancel heartbeat
                        heartbeat_task.cancel()
                        try:
                            await heartbeat_task
                        except asyncio.CancelledError:
                            pass

            # Wait before next poll
            logger.debug(f"Sleeping for {current_backoff} seconds...")
            await asyncio.sleep(current_backoff)

        except Exception as e:
            logger.error(f"Error in polling loop: {e}")
            # Apply jittered exponential backoff
            import random

            jitter = random.uniform(0, 0.1 * current_backoff)
            current_backoff = min(current_backoff + int(jitter), MAX_BACKOFF)
            logger.info(f"Backing off for {current_backoff} seconds")
            await asyncio.sleep(current_backoff)


def main() -> None:
    """Main entry point for the Sentinel service."""
    global _shutdown_requested

    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    logger.info(f"Starting Sentinel {SENTINEL_ID}")
    logger.info(f"Poll interval: {POLL_INTERVAL}s")
    logger.info(f"Heartbeat interval: {HEARTBEAT_INTERVAL}s")

    # Validate environment
    if not os.environ.get("GITHUB_TOKEN"):
        logger.error("GITHUB_TOKEN environment variable is required")
        sys.exit(1)
    if not os.environ.get("GITHUB_REPO"):
        logger.error("GITHUB_REPO environment variable is required")
        sys.exit(1)

    # Create queue and run polling loop
    queue = GitHubQueue()

    try:
        asyncio.run(polling_loop(queue))
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        asyncio.run(queue.close())

    logger.info("Sentinel shutdown complete")


if __name__ == "__main__":
    main()
