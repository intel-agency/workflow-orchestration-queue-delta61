"""Test configuration and fixtures for workflow-orchestration-queue."""

import pytest


@pytest.fixture
def sample_issue() -> dict:
    """Sample GitHub issue fixture for testing."""
    return {
        "number": 42,
        "html_url": "https://github.com/owner/repo/issues/42",
        "body": "Test issue body",
        "title": "Test Issue",
        "labels": [{"name": "agent:queued"}],
        "assignees": [],
        "node_id": "I_test123",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }
