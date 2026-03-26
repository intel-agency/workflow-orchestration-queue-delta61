"""Tests for GitHubQueue implementation."""

import pytest

from src.models.work_item import WorkItemStatus
from src.queue.github_queue import GitHubQueue


class TestGitHubQueue:
    """Tests for the GitHubQueue class."""

    def test_queue_initialization_missing_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test queue initialization fails without token."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(ValueError, match="GitHub token required"):
            GitHubQueue(token=None, repo="owner/repo")

    def test_queue_initialization_missing_repo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test queue initialization fails without repo."""
        monkeypatch.delenv("GITHUB_REPO", raising=False)
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        with pytest.raises(ValueError, match="GitHub repository required"):
            GitHubQueue(token="test-token", repo=None)

    def test_queue_initialization_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful queue initialization."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_REPO", raising=False)
        queue = GitHubQueue(token="test-token", repo="owner/repo")
        assert queue.repo == "owner/repo"
        assert queue.token == "test-token"
