"""GitHub Issues-based queue implementation for workflow-orchestration-queue.

This module provides the GitHubQueue class that implements task discovery
and status management using GitHub Issues and Labels.
"""

from __future__ import annotations

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

import httpx

from src.models.work_item import WorkItem, WorkItemStatus

logger = logging.getLogger(__name__)


class ITaskQueue(ABC):
    """Abstract base class for task queue implementations.

    This interface enables provider-agnostic orchestration logic,
    allowing future support for Linear, Notion, or other providers.
    """

    @abstractmethod
    async def fetch_queued_items(self) -> list[WorkItem]:
        """Fetch all items currently in the queue.

        Returns:
            List of WorkItem objects awaiting processing.
        """
        ...

    @abstractmethod
    async def claim_task(self, item_id: str, sentinel_id: str) -> bool:
        """Attempt to claim a task for processing.

        Args:
            item_id: The unique identifier of the work item.
            sentinel_id: The identifier of the sentinel claiming the task.

        Returns:
            True if the task was successfully claimed, False otherwise.
        """
        ...

    @abstractmethod
    async def update_item_status(
        self, item_id: str, status: WorkItemStatus, comment: str | None = None
    ) -> bool:
        """Update the status of a work item.

        Args:
            item_id: The unique identifier of the work item.
            status: The new status to set.
            comment: Optional comment to post with the status update.

        Returns:
            True if the update was successful, False otherwise.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the queue connection and release resources."""
        ...


class GitHubQueue(ITaskQueue):
    """GitHub Issues-based task queue implementation.

    Uses GitHub Issues with labels as a distributed task queue.
    Implements the "Markdown-as-a-Database" pattern for state management.
    """

    def __init__(self, token: str | None = None, repo: str | None = None):
        """Initialize the GitHub queue.

        Args:
            token: GitHub API token. If not provided, reads from GITHUB_TOKEN env var.
            repo: Target repository in owner/repo format. If not provided,
                  reads from GITHUB_REPO env var.
        """
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.repo = repo or os.environ.get("GITHUB_REPO", "")

        if not self.token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN environment variable.")
        if not self.repo:
            raise ValueError("GitHub repository required. Set GITHUB_REPO environment variable.")

        # Create a single httpx client for connection pooling
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    async def close(self) -> None:
        """Close the HTTP client and release connection pool."""
        await self._client.aclose()

    async def fetch_queued_items(self) -> list[WorkItem]:
        """Fetch all issues with the agent:queued label.

        Returns:
            List of WorkItem objects created from queued GitHub issues.
        """
        url = f"/repos/{self.repo}/issues"
        params = {
            "labels": "agent:queued",
            "state": "open",
            "per_page": 100,
        }

        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            issues = response.json()

            work_items = []
            for issue in issues:
                work_items.append(self._issue_to_work_item(issue))

            logger.info(f"Fetched {len(work_items)} queued items from {self.repo}")
            return work_items

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch queued items: {e}")
            return []

    async def claim_task(self, item_id: str, sentinel_id: str) -> bool:
        """Claim a task using the assign-then-verify pattern.

        This implements a distributed lock using GitHub Assignees
        to prevent race conditions between multiple Sentinel instances.

        Args:
            item_id: The issue number to claim.
            sentinel_id: The GitHub login of the bot account.

        Returns:
            True if successfully claimed, False if another sentinel won.
        """
        issue_number = int(item_id)

        # Step 1: Attempt to assign the sentinel to the issue
        assign_url = f"/repos/{self.repo}/issues/{issue_number}/assignees"
        try:
            response = await self._client.post(assign_url, json={"assignees": [sentinel_id]})
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning(f"Failed to assign issue {issue_number}: {e}")
            return False

        # Step 2: Re-fetch the issue to verify assignment
        issue_url = f"/repos/{self.repo}/issues/{issue_number}"
        try:
            response = await self._client.get(issue_url)
            response.raise_for_status()
            issue = response.json()

            # Step 3: Verify the sentinel is in the assignees list
            assignees = [a["login"] for a in issue.get("assignees", [])]
            if sentinel_id not in assignees:
                logger.info(
                    f"Race condition detected: issue {issue_number} assigned to another sentinel"
                )
                return False

            logger.info(f"Successfully claimed issue {issue_number}")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to verify assignment for issue {issue_number}: {e}")
            return False

    async def update_item_status(
        self, item_id: str, status: WorkItemStatus, comment: str | None = None
    ) -> bool:
        """Update issue labels to reflect new status.

        Args:
            item_id: The issue number to update.
            status: The new status (maps to a label).
            comment: Optional comment to post.

        Returns:
            True if successful, False otherwise.
        """
        issue_number = int(item_id)

        # Remove old status labels and add new one
        status_labels = [
            "agent:queued",
            "agent:in-progress",
            "agent:success",
            "agent:error",
            "agent:infra-failure",
            "agent:stalled-budget",
            "agent:reconciling",
        ]

        try:
            # Get current issue to find existing labels
            issue_url = f"/repos/{self.repo}/issues/{issue_number}"
            response = await self._client.get(issue_url)
            response.raise_for_status()
            issue = response.json()

            current_labels = [l["name"] for l in issue.get("labels", [])]
            new_labels = [l for l in current_labels if l not in status_labels] + [status.value]

            # Update labels
            update_response = await self._client.patch(issue_url, json={"labels": new_labels})
            update_response.raise_for_status()

            # Post comment if provided
            if comment:
                comment_url = f"/repos/{self.repo}/issues/{issue_number}/comments"
                await self._client.post(comment_url, json={"body": comment})

            logger.info(f"Updated issue {issue_number} status to {status.value}")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to update issue {issue_number} status: {e}")
            return False

    def _issue_to_work_item(self, issue: dict[str, Any]) -> WorkItem:
        """Convert a GitHub issue to a WorkItem.

        Args:
            issue: The GitHub issue JSON object.

        Returns:
            A WorkItem instance.
        """
        labels = [l["name"] for l in issue.get("labels", [])]

        # Determine task type from labels
        task_type = "implement"  # default
        if "epic" in labels:
            task_type = "plan"
        elif "bug" in labels:
            task_type = "fix"

        # Determine current status from labels
        status = WorkItemStatus.QUEUED
        for label in labels:
            try:
                status = WorkItemStatus(label)
                break
            except ValueError:
                continue

        return WorkItem(
            id=str(issue["number"]),
            source_url=issue["html_url"],
            context_body=issue.get("body", ""),
            target_repo_slug=self.repo,
            task_type=task_type,
            status=status,
            metadata={
                "issue_node_id": issue.get("node_id"),
                "title": issue.get("title"),
                "created_at": issue.get("created_at"),
                "updated_at": issue.get("updated_at"),
                "assignees": [a["login"] for a in issue.get("assignees", [])],
            },
        )
