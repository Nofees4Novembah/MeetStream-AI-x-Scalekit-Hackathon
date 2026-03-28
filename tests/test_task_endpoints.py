"""
Tests for task management endpoints:
  GET  /tasks/pending
  POST /tasks/clear
  POST /tasks/{task_id}/approve
  POST /tasks/{task_id}/reject
"""

import pytest
from fastapi.testclient import TestClient

import app.extractor as extractor
from app.server import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_pending_tasks():
    """Clear global state before every test."""
    extractor.PENDING_TASKS.clear()
    yield
    extractor.PENDING_TASKS.clear()


def _seed_task(task_id: str = "task_0", tool: str = "Slack", summary: str = "Send recap") -> dict:
    task = {"id": task_id, "tool": tool, "summary": summary, "status": "pending"}
    extractor.PENDING_TASKS.append(task)
    return task


# ---------------------------------------------------------------------------
# GET /tasks/pending
# ---------------------------------------------------------------------------

def test_get_pending_tasks_empty():
    response = client.get("/tasks/pending")
    assert response.status_code == 200
    assert response.json() == []


def test_get_pending_tasks_returns_seeded_task():
    _seed_task()
    response = client.get("/tasks/pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "task_0"


# ---------------------------------------------------------------------------
# POST /tasks/clear
# ---------------------------------------------------------------------------

def test_clear_pending_tasks():
    _seed_task("task_0")
    _seed_task("task_1")
    response = client.post("/tasks/clear")
    assert response.status_code == 200
    assert response.json() == {"status": "cleared"}
    assert extractor.PENDING_TASKS == []


# ---------------------------------------------------------------------------
# POST /tasks/{task_id}/approve
# ---------------------------------------------------------------------------

def test_approve_task_success():
    _seed_task("task_0")
    response = client.post("/tasks/task_0/approve")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["task"]["id"] == "task_0"
    assert body["task"]["status"] == "approved"


def test_approve_task_mutates_global_state():
    _seed_task("task_0")
    client.post("/tasks/task_0/approve")
    assert extractor.PENDING_TASKS[0]["status"] == "approved"


def test_approve_task_not_found():
    response = client.post("/tasks/nonexistent/approve")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_approve_preserves_other_tasks():
    _seed_task("task_0")
    _seed_task("task_1")
    client.post("/tasks/task_0/approve")
    assert extractor.PENDING_TASKS[1]["status"] == "pending"


# ---------------------------------------------------------------------------
# POST /tasks/{task_id}/reject
# ---------------------------------------------------------------------------

def test_reject_task_success():
    _seed_task("task_0")
    response = client.post("/tasks/task_0/reject")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "rejected"
    assert body["task"]["id"] == "task_0"
    assert body["task"]["status"] == "rejected"


def test_reject_task_mutates_global_state():
    _seed_task("task_0")
    client.post("/tasks/task_0/reject")
    assert extractor.PENDING_TASKS[0]["status"] == "rejected"


def test_reject_task_not_found():
    response = client.post("/tasks/nonexistent/reject")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_reject_preserves_other_tasks():
    _seed_task("task_0")
    _seed_task("task_1")
    client.post("/tasks/task_0/reject")
    assert extractor.PENDING_TASKS[1]["status"] == "pending"


# ---------------------------------------------------------------------------
# Status transition sanity checks
# ---------------------------------------------------------------------------

def test_approve_then_reject_same_task():
    """Last write wins — status should be 'rejected'."""
    _seed_task("task_0")
    client.post("/tasks/task_0/approve")
    client.post("/tasks/task_0/reject")
    assert extractor.PENDING_TASKS[0]["status"] == "rejected"
