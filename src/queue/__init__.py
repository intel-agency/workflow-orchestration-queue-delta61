"""Queue package for workflow-orchestration-queue.

This package contains queue implementations for different providers.
"""

from src.queue.github_queue import GitHubQueue

__all__ = [
    "GitHubQueue",
]
