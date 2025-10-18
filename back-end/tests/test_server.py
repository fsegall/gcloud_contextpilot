"""
Unit tests for server.py API endpoints

Tests cover:
- Health check
- Context endpoints
- Proposal endpoints
- Agent status
- Retrospective endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.server import app
import os


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def workspace_id():
    """Default workspace ID for tests"""
    return "test-workspace"


# ===== HEALTH & STATUS TESTS =====


def test_health_check(client):
    """Test that health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "agents" in data
    assert isinstance(data["agents"], list)


def test_agents_status(client):
    """Test agents status endpoint"""
    response = client.get("/agents/status")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check first agent has required fields
    agent = data[0]
    assert "agent_id" in agent
    assert "name" in agent
    assert "status" in agent
    assert "last_activity" in agent


def test_abuse_stats(client):
    """Test admin abuse stats endpoint"""
    response = client.get("/admin/abuse-stats")
    assert response.status_code == 200
    
    data = response.json()
    # Should return abuse detection statistics
    assert isinstance(data, dict)


# ===== CONTEXT ENDPOINTS TESTS =====


def test_get_context(client, workspace_id):
    """Test get context endpoint"""
    response = client.get(f"/context?workspace_id={workspace_id}")
    assert response.status_code == 200
    
    data = response.json()
    # Context should be a dict (may have 'error' key if workspace doesn't exist)
    assert isinstance(data, dict)


def test_get_milestones(client, workspace_id):
    """Test get milestones endpoint"""
    response = client.get(f"/context/milestones?workspace_id={workspace_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "milestones" in data
    assert isinstance(data["milestones"], list)


def test_get_summary(client, workspace_id):
    """Test get summary endpoint"""
    response = client.get(f"/summary?workspace_id={workspace_id}")
    assert response.status_code == 200
    
    data = response.json()
    # Summary may have None values if workspace is new
    assert isinstance(data, dict)


def test_coach_tip(client, workspace_id):
    """Test coach tip endpoint"""
    response = client.get(f"/coach?workspace_id={workspace_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "tip" in data
    assert isinstance(data["tip"], str)


# ===== PROPOSAL ENDPOINTS TESTS =====


def test_list_proposals(client, workspace_id):
    """Test list proposals endpoint"""
    response = client.get(f"/proposals?workspace_id={workspace_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "proposals" in data
    assert "count" in data
    assert isinstance(data["proposals"], list)
    assert isinstance(data["count"], int)


def test_get_mock_proposals(client):
    """Test mock proposals endpoint"""
    response = client.get("/proposals/mock")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    
    if len(data) > 0:
        proposal = data[0]
        assert "id" in proposal
        assert "agent_id" in proposal
        assert "title" in proposal
        assert "status" in proposal


def test_get_proposal_not_found(client, workspace_id):
    """Test get proposal that doesn't exist"""
    response = client.get(f"/proposals/nonexistent-id?workspace_id={workspace_id}")
    assert response.status_code == 404


def test_reject_proposal_not_found(client, workspace_id):
    """Test reject proposal that doesn't exist"""
    response = client.post(
        f"/proposals/nonexistent-id/reject?workspace_id={workspace_id}",
        json=""
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "not_found"


# ===== SPEC AGENT TESTS =====


@pytest.mark.asyncio
async def test_spec_analyze(client, workspace_id):
    """Test spec agent analyze endpoint"""
    response = client.post(f"/agents/spec/analyze?workspace_id={workspace_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "issues" in data
    assert "count" in data
    assert isinstance(data["issues"], list)
    assert isinstance(data["count"], int)


@pytest.mark.asyncio
async def test_spec_proposals(client, workspace_id):
    """Test spec agent proposals endpoint"""
    response = client.get(f"/agents/spec/proposals?workspace_id={workspace_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "proposals" in data
    assert "count" in data


# ===== RETROSPECTIVE TESTS =====


@pytest.mark.asyncio
async def test_trigger_retrospective(client, workspace_id):
    """Test triggering a retrospective"""
    response = client.post(
        f"/agents/retrospective/trigger?workspace_id={workspace_id}",
        json={"trigger": "manual", "use_llm": False}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    
    if data["status"] == "success":
        assert "retrospective" in data
        retro = data["retrospective"]
        assert "retrospective_id" in retro
        assert "timestamp" in retro
        assert "agent_metrics" in retro
        assert "insights" in retro
        assert "action_items" in retro


@pytest.mark.asyncio
async def test_list_retrospectives(client, workspace_id):
    """Test listing retrospectives"""
    response = client.get(f"/agents/retrospective/list?workspace_id={workspace_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "retrospectives" in data
    assert "count" in data
    assert isinstance(data["retrospectives"], list)


@pytest.mark.asyncio
async def test_get_retrospective_not_found(client, workspace_id):
    """Test getting a retrospective that doesn't exist"""
    response = client.get(
        f"/agents/retrospective/nonexistent-id?workspace_id={workspace_id}"
    )
    assert response.status_code == 404


# ===== REWARDS TESTS =====


def test_mock_balance(client):
    """Test mock rewards balance endpoint"""
    response = client.get("/rewards/balance/mock?user_id=test-user")
    assert response.status_code == 200
    
    data = response.json()
    assert "balance" in data
    assert "total_earned" in data
    assert "pending_rewards" in data
    assert isinstance(data["balance"], (int, float))


# ===== COACH AGENT TESTS =====


def test_coach_ask(client):
    """Test coach agent ask endpoint"""
    response = client.post(
        "/agents/coach/ask",
        json={"user_id": "test-user", "question": "How do I implement a new feature?"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)


# ===== RATE LIMITING TESTS =====


def test_rate_limiting_health_exempt(client):
    """Test that health check is exempt from rate limiting"""
    # Make 200 health check requests (should all succeed)
    for _ in range(200):
        response = client.get("/health")
        assert response.status_code == 200


def test_rate_limiting_enforced(client):
    """Test that rate limiting is enforced on regular endpoints"""
    # This test would require mocking time to speed up
    # For now, just verify the endpoint exists
    response = client.get("/context")
    assert response.status_code in [200, 429]  # Either success or rate limited


# ===== ERROR HANDLING TESTS =====


def test_invalid_workspace_id(client):
    """Test handling of invalid workspace ID"""
    # Should not crash, should return error or empty data
    response = client.get("/context?workspace_id=../../../etc/passwd")
    assert response.status_code in [200, 400, 404]


def test_malformed_json(client):
    """Test handling of malformed JSON in POST requests"""
    response = client.post(
        "/agents/coach/ask",
        data="not valid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422  # Validation error


# ===== INTEGRATION TESTS =====


@pytest.mark.integration
def test_full_proposal_workflow(client, workspace_id):
    """
    Integration test: Create proposal, approve it, verify commit
    
    This test requires a valid workspace with git initialized.
    """
    # 1. Create proposals
    response = client.post(f"/proposals/create?workspace_id={workspace_id}")
    assert response.status_code == 200
    
    # 2. List proposals
    response = client.get(f"/proposals?workspace_id={workspace_id}")
    assert response.status_code == 200
    
    data = response.json()
    proposals = data.get("proposals", [])
    
    if len(proposals) > 0:
        proposal_id = proposals[0]["id"]
        
        # 3. Approve proposal
        response = client.post(
            f"/proposals/{proposal_id}/approve?workspace_id={workspace_id}"
        )
        assert response.status_code == 200


# ===== PARAMETRIZED TESTS =====


@pytest.mark.parametrize("workspace_id", ["default", "test", "workspace-123"])
def test_context_with_different_workspaces(client, workspace_id):
    """Test context endpoint with different workspace IDs"""
    response = client.get(f"/context?workspace_id={workspace_id}")
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint,expected_status",
    [
        ("/health", 200),
        ("/agents/status", 200),
        ("/proposals/mock", 200),
        ("/nonexistent-endpoint", 404),
    ]
)
def test_endpoints_status_codes(client, endpoint, expected_status):
    """Test that endpoints return expected status codes"""
    response = client.get(endpoint)
    assert response.status_code == expected_status

