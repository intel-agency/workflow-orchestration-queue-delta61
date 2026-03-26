"""Unified WorkItem model and related enums for workflow-orchestration-queue.

This module defines the core data structures used by both the Sentinel
Orchestrator and the Notifier Service for task management.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Type of task to be executed."""

    PLAN = "plan"
    IMPLEMENT = "implement"
    REVIEW = "review"
    FIX = "fix"
    DEPLOY = "deploy"


class WorkItemStatus(str, Enum):
    """Status of a work item in the queue.

    Maps to GitHub labels for state management.
    """

    QUEUED = "agent:queued"
    IN_PROGRESS = "agent:in-progress"
    SUCCESS = "agent:success"
    ERROR = "agent:error"
    INFRA_FAILURE = "agent:infra-failure"
    STALLED_BUDGET = "agent:stalled-budget"
    RECONCILING = "agent:reconciling"


# Regex patterns for secret scrubbing
SECRET_PATTERNS = [
    # GitHub PATs
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),
    re.compile(r"ghs_[a-zA-Z0-9]{36}"),
    re.compile(r"gho_[a-zA-Z0-9]{36}"),
    re.compile(r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}"),
    # Generic tokens
    re.compile(r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*", re.IGNORECASE),
    re.compile(r"token[=:]\s*[a-zA-Z0-9\-._~+/]+", re.IGNORECASE),
    # OpenAI/LLM keys
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    # ZhipuAI keys
    re.compile(r"[a-f0-9]{32}\.[a-f0-9]{32}"),
]

REDACTED = "***REDACTED***"


def scrub_secrets(text: str) -> str:
    """Scrub secrets and sensitive data from text.

    Args:
        text: The text to scrub.

    Returns:
        The text with all secrets replaced by REDACTED.
    """
    result = text
    for pattern in SECRET_PATTERNS:
        result = pattern.sub(REDACTED, result)
    return result


class WorkItem(BaseModel):
    """Unified work item representing a task in the orchestration queue.

    This model abstracts the task representation from the specific provider
    (GitHub, Linear, etc.) to enable provider-agnostic orchestration logic.
    """

    id: str = Field(..., description="Unique identifier for the work item")
    source_url: str = Field(..., description="URL to the original issue/task")
    context_body: str = Field(
        ..., description="The body/description of the task (e.g., issue body)"
    )
    target_repo_slug: str = Field(..., description="Target repository in owner/repo format")
    task_type: TaskType = Field(default=TaskType.IMPLEMENT, description="Type of task to execute")
    status: WorkItemStatus = Field(
        default=WorkItemStatus.QUEUED, description="Current status of the work item"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific metadata (e.g., issue_node_id for GitHub)",
    )

    model_config = {
        "use_enum_values": True,
        "extra": "forbid",
    }

    def get_safe_context(self) -> str:
        """Get the context body with secrets scrubbed.

        Returns:
            The context body with all secrets removed.
        """
        return scrub_secrets(self.context_body)

    def to_log_dict(self) -> dict[str, Any]:
        """Convert to a dictionary safe for logging.

        Returns:
            A dictionary with secrets scrubbed from context_body.
        """
        data = self.model_dump()
        data["context_body"] = self.get_safe_context()
        return data
