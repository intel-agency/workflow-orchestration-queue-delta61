"""Tests for WorkItem model and related utilities."""

import pytest

from src.models.work_item import TaskType, WorkItem, WorkItemStatus, scrub_secrets


class TestScrubSecrets:
    """Tests for the scrub_secrets utility."""

    def test_scrub_github_pat(self) -> None:
        """Test GitHub PAT scrubbing."""
        text = "Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        result = scrub_secrets(text)
        assert "ghp_" not in result
        assert "***REDACTED***" in result

    def test_scrub_bearer_token(self) -> None:
        """Test Bearer token scrubbing."""
        text = "Authorization: Bearer abc123xyz789"
        result = scrub_secrets(text)
        assert "Bearer abc123xyz789" not in result

    def test_scrub_openai_key(self) -> None:
        """Test OpenAI API key scrubbing."""
        text = "API key: sk-1234567890abcdefghijklmnopqrstuv"
        result = scrub_secrets(text)
        assert "sk-" not in result

    def test_no_secrets(self) -> None:
        """Test text without secrets passes through."""
        text = "This is a normal log message"
        result = scrub_secrets(text)
        assert result == text


class TestWorkItem:
    """Tests for the WorkItem model."""

    def test_work_item_creation(self) -> None:
        """Test basic WorkItem creation."""
        item = WorkItem(
            id="42",
            source_url="https://github.com/owner/repo/issues/42",
            context_body="Test body",
            target_repo_slug="owner/repo",
        )
        assert item.id == "42"
        assert item.task_type == TaskType.IMPLEMENT
        assert item.status == WorkItemStatus.QUEUED

    def test_work_item_get_safe_context(self) -> None:
        """Test safe context retrieval."""
        item = WorkItem(
            id="42",
            source_url="https://github.com/owner/repo/issues/42",
            context_body="Secret: ghp_1234567890abcdefghijklmnopqrstuvwxyz",
            target_repo_slug="owner/repo",
        )
        safe = item.get_safe_context()
        assert "ghp_" not in safe
        assert "***REDACTED***" in safe

    def test_work_item_to_log_dict(self) -> None:
        """Test log dictionary conversion."""
        item = WorkItem(
            id="42",
            source_url="https://github.com/owner/repo/issues/42",
            context_body="Secret: ghp_1234567890abcdefghijklmnopqrstuvwxyz",
            target_repo_slug="owner/repo",
        )
        log_dict = item.to_log_dict()
        assert "ghp_" not in log_dict["context_body"]
