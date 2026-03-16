"""Tests for v4 sub-client endpoints (sandbox, revision, attacks, reconsolidation, goals)."""

from __future__ import annotations

import pytest
import respx

from mnemebrain.client import MnemeBrainClient

BASE = "http://localhost:8000"
V4 = f"{BASE}/api/mneme"


@pytest.fixture
def client():
    return MnemeBrainClient(base_url=BASE)


class TestSandboxClient:
    @respx.mock
    def test_fork(self, client):
        respx.post(f"{V4}/sandbox/fork").respond(
            201,
            json={
                "id": "sb-1",
                "frame_id": None,
                "scenario_label": "test",
                "status": "active",
                "created_at": "2026-01-01T00:00:00Z",
                "expires_at": "2026-01-01T00:10:00Z",
            },
        )
        result = client.sandbox.fork(scenario_label="test")
        assert result.id == "sb-1"
        assert result.status == "active"

    @respx.mock
    def test_quick(self, client):
        respx.post(f"{V4}/sandbox/quick").respond(
            201,
            json={
                "id": "sb-2",
                "frame_id": None,
                "scenario_label": "quick",
                "status": "active",
                "created_at": "2026-01-01T00:00:00Z",
                "expires_at": "2026-01-01T00:01:00Z",
            },
        )
        result = client.sandbox.quick()
        assert result.id == "sb-2"

    @respx.mock
    def test_get_context(self, client):
        respx.get(f"{V4}/sandbox/sb-1/context").respond(
            200,
            json={
                "id": "sb-1",
                "frame_id": None,
                "scenario_label": "test",
                "status": "active",
                "belief_overrides": {},
                "added_belief_ids": [],
                "invalidated_evidence": [],
                "created_at": "2026-01-01T00:00:00Z",
                "expires_at": None,
            },
        )
        result = client.sandbox.get_context("sb-1")
        assert result.id == "sb-1"
        assert result.belief_overrides == {}

    @respx.mock
    def test_diff(self, client):
        respx.get(f"{V4}/sandbox/sb-1/diff").respond(
            200,
            json={
                "belief_changes": [
                    {
                        "belief_id": "b1",
                        "field": "truth_state",
                        "old_value": "true",
                        "new_value": "false",
                    }
                ],
                "evidence_invalidations": ["ev1"],
                "new_beliefs": [],
                "temporary_attacks": [],
                "goal_changes": [],
                "summary": "1 override",
            },
        )
        result = client.sandbox.diff("sb-1")
        assert len(result.belief_changes) == 1
        assert result.belief_changes[0].field == "truth_state"

    @respx.mock
    def test_commit(self, client):
        respx.post(f"{V4}/sandbox/sb-1/commit").respond(
            200,
            json={"sandbox_id": "sb-1", "committed_belief_ids": ["b1"], "conflicts": []},
        )
        result = client.sandbox.commit("sb-1", commit_mode="all")
        assert result.committed_belief_ids == ["b1"]

    @respx.mock
    def test_discard(self, client):
        respx.delete(f"{V4}/sandbox/sb-1").respond(204)
        client.sandbox.discard("sb-1")  # no error = success

    @respx.mock
    def test_assume(self, client):
        respx.post(f"{V4}/sandbox/sb-1/assume").respond(204)
        client.sandbox.assume("sb-1", "b1", "false")

    @respx.mock
    def test_retract(self, client):
        respx.post(f"{V4}/sandbox/sb-1/retract").respond(204)
        client.sandbox.retract("sb-1", "ev-1")

    @respx.mock
    def test_believe(self, client):
        respx.post(f"{V4}/sandbox/sb-1/believe").respond(201, json={"belief_id": "b-new"})
        result = client.sandbox.believe("sb-1", "sky is blue")
        assert result == {"belief_id": "b-new"}

    @respx.mock
    def test_revise(self, client):
        respx.post(f"{V4}/sandbox/sb-1/revise").respond(204)
        client.sandbox.revise("sb-1", "b1", source_ref="s1", content="updated")

    @respx.mock
    def test_attack(self, client):
        respx.post(f"{V4}/sandbox/sb-1/attack").respond(201, json={"attack_id": "a-tmp"})
        result = client.sandbox.attack("sb-1", "b1", "b2", "contradicts")
        assert result == {"attack_id": "a-tmp"}

    @respx.mock
    def test_explain(self, client):
        respx.get(f"{V4}/sandbox/sb-1/explain/b1").respond(
            200,
            json={
                "belief_id": "b1",
                "sandbox_id": "sb-1",
                "resolved_truth_state": "false",
                "has_override": True,
                "override_fields": ["truth_state"],
                "invalidated_evidence_ids": [],
                "source": "sandbox",
            },
        )
        result = client.sandbox.explain("sb-1", "b1")
        assert result.has_override is True

    @respx.mock
    def test_evaluate_goal(self, client):
        respx.post(f"{V4}/sandbox/sb-1/goal/g1/evaluate").respond(
            200,
            json={
                "goal_id": "g1",
                "status": "active",
                "completion_fraction": 0.3,
                "blocking_belief_ids": ["b2"],
                "supporting_belief_ids": [],
            },
        )
        result = client.sandbox.evaluate_goal("sb-1", "g1")
        assert result.goal_id == "g1"
        assert result.completion_fraction == 0.3


class TestRevisionClient:
    @respx.mock
    def test_set_policy(self, client):
        respx.post(f"{V4}/revision/policy").respond(
            200,
            json={"policy_name": "recency", "max_retraction_depth": 3, "max_retractions": 10},
        )
        result = client.revision.set_policy("recency")
        assert result.policy_name == "recency"

    @respx.mock
    def test_get_policy(self, client):
        respx.get(f"{V4}/revision/policy").respond(
            200,
            json={"policy_name": "confidence", "max_retraction_depth": 5, "max_retractions": 20},
        )
        result = client.revision.get_policy()
        assert result.policy_name == "confidence"

    @respx.mock
    def test_list_audit(self, client):
        respx.get(f"{V4}/revision/audit").respond(200, json=[])
        result = client.revision.list_audit()
        assert result == []

    @respx.mock
    def test_revise(self, client):
        respx.post(f"{V4}/revise").respond(
            200,
            json={
                "superseded_evidence_ids": ["ev1"],
                "retracted_belief_ids": [],
                "revision_depth": 1,
                "policy_name": "recency",
                "bounded": False,
            },
        )
        result = client.revision.revise("b1")
        assert result.superseded_evidence_ids == ["ev1"]


class TestAttackClient:
    @respx.mock
    def test_create(self, client):
        respx.post(f"{V4}/beliefs/b1/attacks").respond(
            201,
            json={
                "id": "a1",
                "source_belief_id": "b1",
                "target_belief_id": "b2",
                "attack_type": "contradicts",
                "weight": 0.8,
                "active": True,
                "created_at": "2026-01-01T00:00:00Z",
            },
        )
        result = client.attacks.create("b1", "b2", "contradicts", 0.8)
        assert result.id == "a1"
        assert result.attack_type == "contradicts"

    @respx.mock
    def test_list(self, client):
        respx.get(f"{V4}/beliefs/b1/attacks").respond(200, json=[])
        result = client.attacks.list("b1")
        assert result == []

    @respx.mock
    def test_get_chain(self, client):
        respx.get(f"{V4}/beliefs/b1/attack-chain").respond(200, json={"chains": []})
        result = client.attacks.get_chain("b1")
        assert result == []

    @respx.mock
    def test_deactivate(self, client):
        respx.delete(f"{V4}/attacks/a1").respond(204)
        client.attacks.deactivate("a1")


class TestReconsolidationClient:
    @respx.mock
    def test_queue(self, client):
        respx.get(f"{V4}/reconsolidation/queue").respond(200, json={"queue_size": 5})
        result = client.reconsolidation.queue()
        assert result.queue_size == 5

    @respx.mock
    def test_run(self, client):
        respx.post(f"{V4}/reconsolidation/run").respond(
            200, json={"processed": 3, "timestamp": "2026-01-01T00:00:00Z"}
        )
        result = client.reconsolidation.run()
        assert result.processed == 3


class TestGoalClient:
    @respx.mock
    def test_create(self, client):
        respx.post(f"{V4}/goals").respond(
            201,
            json={
                "id": "g1",
                "goal": "deploy feature",
                "owner": "agent-1",
                "priority": 0.8,
                "status": "active",
                "created_at": "2026-01-01T00:00:00Z",
                "deadline": None,
                "success_criteria": {},
            },
        )
        result = client.goals.create("deploy feature", "agent-1", priority=0.8)
        assert result.id == "g1"

    @respx.mock
    def test_list(self, client):
        respx.get(f"{V4}/goals").respond(200, json=[])
        assert client.goals.list() == []

    @respx.mock
    def test_get(self, client):
        respx.get(f"{V4}/goals/g1").respond(
            200,
            json={
                "id": "g1",
                "goal": "deploy",
                "owner": "a1",
                "priority": 0.5,
                "status": "active",
                "created_at": "2026-01-01T00:00:00Z",
                "deadline": None,
                "success_criteria": {},
            },
        )
        result = client.goals.get("g1")
        assert result.goal == "deploy"

    @respx.mock
    def test_evaluate(self, client):
        respx.post(f"{V4}/goals/g1/evaluate").respond(
            200,
            json={
                "goal_id": "g1",
                "status": "active",
                "completion_fraction": 0.5,
                "blocking_belief_ids": [],
                "supporting_belief_ids": ["b1"],
            },
        )
        result = client.goals.evaluate("g1")
        assert result.completion_fraction == 0.5

    @respx.mock
    def test_update_status(self, client):
        respx.put(f"{V4}/goals/g1/status").respond(
            200,
            json={
                "id": "g1",
                "goal": "deploy",
                "owner": "a1",
                "priority": 0.5,
                "status": "completed",
                "created_at": "2026-01-01T00:00:00Z",
                "deadline": None,
                "success_criteria": {},
            },
        )
        result = client.goals.update_status("g1", "completed")
        assert result.status == "completed"

    @respx.mock
    def test_abandon(self, client):
        respx.delete(f"{V4}/goals/g1").respond(204)
        client.goals.abandon("g1")


class TestPolicyClient:
    @respx.mock
    def test_create(self, client):
        respx.post(f"{V4}/policies").respond(
            201,
            json={
                "id": "p1",
                "name": "auth-flow",
                "description": "Auth policy",
                "version": 1,
                "reliability": 1.0,
                "status": "active",
                "created_at": "2026-01-01T00:00:00Z",
                "last_updated": "2026-01-01T00:00:00Z",
                "superseded_by": None,
                "steps": [
                    {
                        "step_id": 1,
                        "action": "check token",
                        "tool": None,
                        "conditions": [],
                        "fallback": None,
                    }
                ],
                "applicability": {},
            },
        )
        result = client.policies.create(
            "auth-flow",
            steps=[{"step_id": 1, "action": "check token"}],
            description="Auth policy",
        )
        assert result.name == "auth-flow"
        assert len(result.steps) == 1

    @respx.mock
    def test_list(self, client):
        respx.get(f"{V4}/policies").respond(200, json=[])
        assert client.policies.list() == []

    @respx.mock
    def test_get(self, client):
        respx.get(f"{V4}/policies/p1").respond(
            200,
            json={
                "id": "p1",
                "name": "auth",
                "description": "",
                "version": 1,
                "reliability": 1.0,
                "status": "active",
                "created_at": "2026-01-01T00:00:00Z",
                "last_updated": "2026-01-01T00:00:00Z",
                "superseded_by": None,
                "steps": [],
                "applicability": {},
            },
        )
        result = client.policies.get("p1")
        assert result.id == "p1"

    @respx.mock
    def test_get_history(self, client):
        respx.get(f"{V4}/policies/p1/history").respond(200, json=[])
        assert client.policies.get_history("p1") == []

    @respx.mock
    def test_update_status(self, client):
        respx.put(f"{V4}/policies/p1/status").respond(
            200,
            json={
                "id": "p1",
                "name": "auth",
                "description": "",
                "version": 1,
                "reliability": 1.0,
                "status": "retired",
                "created_at": "2026-01-01T00:00:00Z",
                "last_updated": "2026-01-01T00:00:00Z",
                "superseded_by": None,
                "steps": [],
                "applicability": {},
            },
        )
        result = client.policies.update_status("p1", "retired")
        assert result.status == "retired"


class TestLazyProperties:
    def test_sandbox_is_lazy(self, client):
        assert client._sandbox is None
        sb = client.sandbox
        assert sb is client.sandbox  # same instance returned

    def test_revision_is_lazy(self, client):
        assert client._revision is None
        rv = client.revision
        assert rv is client.revision

    def test_attacks_is_lazy(self, client):
        assert client._attacks is None
        at = client.attacks
        assert at is client.attacks

    def test_reconsolidation_is_lazy(self, client):
        assert client._reconsolidation is None
        rc = client.reconsolidation
        assert rc is client.reconsolidation

    def test_goals_is_lazy(self, client):
        assert client._goals is None
        gl = client.goals
        assert gl is client.goals

    def test_policies_is_lazy(self, client):
        assert client._policies is None
        pl = client.policies
        assert pl is client.policies


class TestOptionalParamBranches:
    """Cover optional-parameter branches that default tests skip."""

    SANDBOX_JSON = {
        "id": "sb-x",
        "frame_id": "f-1",
        "scenario_label": "test",
        "status": "active",
        "created_at": "2026-01-01T00:00:00Z",
        "expires_at": "2026-01-01T00:10:00Z",
    }

    @respx.mock
    def test_fork_with_frame_id(self, client):
        respx.post(f"{V4}/sandbox/fork").respond(201, json=self.SANDBOX_JSON)
        result = client.sandbox.fork(scenario_label="test", frame_id="f-1")
        assert result.frame_id == "f-1"

    @respx.mock
    def test_quick_with_frame_id(self, client):
        respx.post(f"{V4}/sandbox/quick").respond(201, json=self.SANDBOX_JSON)
        result = client.sandbox.quick(frame_id="f-1")
        assert result.frame_id == "f-1"

    @respx.mock
    def test_commit_with_selected_ids(self, client):
        respx.post(f"{V4}/sandbox/sb-1/commit").respond(
            200,
            json={
                "sandbox_id": "sb-1",
                "committed_belief_ids": ["b1"],
                "conflicts": [],
            },
        )
        result = client.sandbox.commit("sb-1", selected_ids=["b1"])
        assert result.committed_belief_ids == ["b1"]

    @respx.mock
    def test_set_policy_with_limits(self, client):
        respx.post(f"{V4}/revision/policy").respond(
            200,
            json={
                "policy_name": "recency",
                "max_retraction_depth": 5,
                "max_retractions": 20,
            },
        )
        result = client.revision.set_policy("recency", max_retraction_depth=5, max_retractions=20)
        assert result.max_retraction_depth == 5
        assert result.max_retractions == 20

    @respx.mock
    def test_goal_create_with_optional_fields(self, client):
        respx.post(f"{V4}/goals").respond(
            201,
            json={
                "id": "g2",
                "goal": "ship v2",
                "owner": "agent-1",
                "priority": 0.9,
                "status": "active",
                "created_at": "2026-01-01T00:00:00Z",
                "deadline": "2026-06-01",
                "success_criteria": {"tests": "pass"},
            },
        )
        result = client.goals.create(
            "ship v2",
            "agent-1",
            priority=0.9,
            success_criteria={"tests": "pass"},
            deadline="2026-06-01",
        )
        assert result.id == "g2"
        assert result.deadline == "2026-06-01"
