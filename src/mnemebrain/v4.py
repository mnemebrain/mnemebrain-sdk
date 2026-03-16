"""V4 sub-clients for MnemeBrain sandbox, revision, attacks, reconsolidation, goals, policies."""

from __future__ import annotations

from typing import Any

import httpx

from mnemebrain.models import (
    AttackEdgeResult,
    BeliefChangeDetail,
    BeliefSnapshot,
    FrameCommitResult,
    FrameContextResult,
    FrameOpenResult,
    GoalEvaluationResult,
    GoalResult,
    PolicyResult,
    PolicyStepResult,
    ReconsolidationQueueResult,
    ReconsolidationRunResult,
    RevisionAuditEntry,
    RevisionPolicyResult,
    RevisionResult,
    SandboxCommitResult,
    SandboxContextResult,
    SandboxDiffResult,
    SandboxExplainResult,
    SandboxResult,
)

_V4_PREFIX = "/api/mneme"


def _parse_sandbox(d: dict) -> SandboxResult:
    return SandboxResult(
        id=d["id"],
        frame_id=d.get("frame_id"),
        scenario_label=d["scenario_label"],
        status=d["status"],
        created_at=d["created_at"],
        expires_at=d.get("expires_at"),
    )


def _parse_attack_edge(d: dict) -> AttackEdgeResult:
    return AttackEdgeResult(
        id=d["id"],
        source_belief_id=d["source_belief_id"],
        target_belief_id=d["target_belief_id"],
        attack_type=d["attack_type"],
        weight=d["weight"],
        active=d["active"],
        created_at=d["created_at"],
    )


def _parse_goal(d: dict) -> GoalResult:
    return GoalResult(
        id=d["id"],
        goal=d["goal"],
        owner=d["owner"],
        priority=d["priority"],
        status=d["status"],
        created_at=d["created_at"],
        deadline=d.get("deadline"),
        success_criteria=d.get("success_criteria", {}),
    )


def _parse_policy(d: dict) -> PolicyResult:
    return PolicyResult(
        id=d["id"],
        name=d["name"],
        description=d["description"],
        version=d["version"],
        reliability=d["reliability"],
        status=d["status"],
        created_at=d["created_at"],
        last_updated=d["last_updated"],
        superseded_by=d.get("superseded_by"),
        steps=[
            PolicyStepResult(
                step_id=s["step_id"],
                action=s["action"],
                tool=s.get("tool"),
                conditions=s.get("conditions", []),
                fallback=s.get("fallback"),
            )
            for s in d.get("steps", [])
        ],
        applicability=d.get("applicability", {}),
    )


class SandboxClient:
    """Sub-client for sandbox (phase 2.5/3) endpoints."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def fork(
        self,
        scenario_label: str = "default",
        ttl_seconds: int = 600,
        frame_id: str | None = None,
    ) -> SandboxResult:
        payload: dict[str, Any] = {
            "scenario_label": scenario_label,
            "ttl_seconds": ttl_seconds,
        }
        if frame_id is not None:
            payload["frame_id"] = frame_id
        resp = self._http.post(f"{_V4_PREFIX}/sandbox/fork", json=payload)
        resp.raise_for_status()
        return _parse_sandbox(resp.json())

    def quick(self, frame_id: str | None = None) -> SandboxResult:
        payload: dict[str, Any] = {}
        if frame_id is not None:
            payload["frame_id"] = frame_id
        resp = self._http.post(f"{_V4_PREFIX}/sandbox/quick", json=payload)
        resp.raise_for_status()
        return _parse_sandbox(resp.json())

    def get_context(self, sandbox_id: str) -> SandboxContextResult:
        resp = self._http.get(f"{_V4_PREFIX}/sandbox/{sandbox_id}/context")
        resp.raise_for_status()
        d = resp.json()
        return SandboxContextResult(
            id=d["id"],
            frame_id=d.get("frame_id"),
            scenario_label=d["scenario_label"],
            status=d["status"],
            belief_overrides=d.get("belief_overrides", {}),
            added_belief_ids=d.get("added_belief_ids", []),
            invalidated_evidence=d.get("invalidated_evidence", []),
            created_at=d["created_at"],
            expires_at=d.get("expires_at"),
        )

    def diff(self, sandbox_id: str) -> SandboxDiffResult:
        resp = self._http.get(f"{_V4_PREFIX}/sandbox/{sandbox_id}/diff")
        resp.raise_for_status()
        d = resp.json()
        return SandboxDiffResult(
            belief_changes=[
                BeliefChangeDetail(
                    belief_id=c["belief_id"],
                    field=c["field"],
                    old_value=c["old_value"],
                    new_value=c["new_value"],
                )
                for c in d.get("belief_changes", [])
            ],
            evidence_invalidations=d.get("evidence_invalidations", []),
            new_beliefs=d.get("new_beliefs", []),
            temporary_attacks=d.get("temporary_attacks", []),
            goal_changes=d.get("goal_changes", []),
            summary=d.get("summary", ""),
        )

    def commit(
        self,
        sandbox_id: str,
        commit_mode: str = "selective",
        selected_ids: list[str] | None = None,
    ) -> SandboxCommitResult:
        payload: dict[str, Any] = {"commit_mode": commit_mode}
        if selected_ids is not None:
            payload["selected_ids"] = selected_ids
        resp = self._http.post(f"{_V4_PREFIX}/sandbox/{sandbox_id}/commit", json=payload)
        resp.raise_for_status()
        d = resp.json()
        return SandboxCommitResult(
            sandbox_id=d["sandbox_id"],
            committed_belief_ids=d["committed_belief_ids"],
            conflicts=d["conflicts"],
        )

    def discard(self, sandbox_id: str) -> None:
        resp = self._http.delete(f"{_V4_PREFIX}/sandbox/{sandbox_id}")
        resp.raise_for_status()

    def assume(self, sandbox_id: str, belief_id: str, truth_state: str) -> None:
        resp = self._http.post(
            f"{_V4_PREFIX}/sandbox/{sandbox_id}/assume",
            json={"belief_id": belief_id, "truth_state": truth_state},
        )
        resp.raise_for_status()

    def retract(self, sandbox_id: str, evidence_id: str) -> None:
        resp = self._http.post(
            f"{_V4_PREFIX}/sandbox/{sandbox_id}/retract",
            json={"evidence_id": evidence_id},
        )
        resp.raise_for_status()

    def believe(self, sandbox_id: str, claim: str) -> dict:
        resp = self._http.post(
            f"{_V4_PREFIX}/sandbox/{sandbox_id}/believe",
            json={"claim": claim},
        )
        resp.raise_for_status()
        return resp.json()

    def revise(
        self,
        sandbox_id: str,
        belief_id: str,
        source_ref: str = "",
        content: str = "",
    ) -> None:
        resp = self._http.post(
            f"{_V4_PREFIX}/sandbox/{sandbox_id}/revise",
            json={"belief_id": belief_id, "source_ref": source_ref, "content": content},
        )
        resp.raise_for_status()

    def attack(
        self,
        sandbox_id: str,
        source_id: str,
        target_id: str,
        attack_type: str,
    ) -> dict:
        resp = self._http.post(
            f"{_V4_PREFIX}/sandbox/{sandbox_id}/attack",
            json={
                "source_belief_id": source_id,
                "target_belief_id": target_id,
                "attack_type": attack_type,
            },
        )
        resp.raise_for_status()
        return resp.json()

    def explain(self, sandbox_id: str, belief_id: str) -> SandboxExplainResult:
        resp = self._http.get(f"{_V4_PREFIX}/sandbox/{sandbox_id}/explain/{belief_id}")
        resp.raise_for_status()
        d = resp.json()
        return SandboxExplainResult(
            belief_id=d["belief_id"],
            sandbox_id=d["sandbox_id"],
            resolved_truth_state=d["resolved_truth_state"],
            has_override=d["has_override"],
            override_fields=d.get("override_fields", []),
            invalidated_evidence_ids=d.get("invalidated_evidence_ids", []),
            source=d.get("source", ""),
        )

    def evaluate_goal(self, sandbox_id: str, goal_id: str) -> GoalEvaluationResult:
        resp = self._http.post(f"{_V4_PREFIX}/sandbox/{sandbox_id}/goal/{goal_id}/evaluate")
        resp.raise_for_status()
        d = resp.json()
        return GoalEvaluationResult(
            goal_id=d["goal_id"],
            status=d["status"],
            completion_fraction=d["completion_fraction"],
            blocking_belief_ids=d.get("blocking_belief_ids", []),
            supporting_belief_ids=d.get("supporting_belief_ids", []),
        )


class RevisionClient:
    """Sub-client for belief revision endpoints."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def set_policy(
        self,
        policy_name: str,
        max_retraction_depth: int | None = None,
        max_retractions: int | None = None,
    ) -> RevisionPolicyResult:
        payload: dict[str, Any] = {"policy_name": policy_name}
        if max_retraction_depth is not None:
            payload["max_retraction_depth"] = max_retraction_depth
        if max_retractions is not None:
            payload["max_retractions"] = max_retractions
        resp = self._http.post(f"{_V4_PREFIX}/revision/policy", json=payload)
        resp.raise_for_status()
        d = resp.json()
        return RevisionPolicyResult(
            policy_name=d["policy_name"],
            max_retraction_depth=d["max_retraction_depth"],
            max_retractions=d["max_retractions"],
        )

    def get_policy(self) -> RevisionPolicyResult:
        resp = self._http.get(f"{_V4_PREFIX}/revision/policy")
        resp.raise_for_status()
        d = resp.json()
        return RevisionPolicyResult(
            policy_name=d["policy_name"],
            max_retraction_depth=d["max_retraction_depth"],
            max_retractions=d["max_retractions"],
        )

    def list_audit(self) -> list[RevisionAuditEntry]:
        resp = self._http.get(f"{_V4_PREFIX}/revision/audit")
        resp.raise_for_status()
        return [
            RevisionAuditEntry(
                id=e["id"],
                timestamp=e["timestamp"],
                incoming_belief_id=e["incoming_belief_id"],
                policy_name=e["policy_name"],
                revision_depth=e["revision_depth"],
                bounded=e["bounded"],
                agent_id=e["agent_id"],
            )
            for e in resp.json()
        ]

    def revise(self, belief_id: str) -> RevisionResult:
        resp = self._http.post(f"{_V4_PREFIX}/revise", json={"belief_id": belief_id})
        resp.raise_for_status()
        d = resp.json()
        return RevisionResult(
            superseded_evidence_ids=d["superseded_evidence_ids"],
            retracted_belief_ids=d["retracted_belief_ids"],
            revision_depth=d["revision_depth"],
            policy_name=d["policy_name"],
            bounded=d["bounded"],
        )


class AttackClient:
    """Sub-client for attack-edge endpoints."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def create(
        self,
        source_belief_id: str,
        target_belief_id: str,
        attack_type: str,
        weight: float,
    ) -> AttackEdgeResult:
        resp = self._http.post(
            f"{_V4_PREFIX}/beliefs/{source_belief_id}/attacks",
            json={
                "target_belief_id": target_belief_id,
                "attack_type": attack_type,
                "weight": weight,
            },
        )
        resp.raise_for_status()
        return _parse_attack_edge(resp.json())

    def list(self, belief_id: str) -> list[AttackEdgeResult]:
        resp = self._http.get(f"{_V4_PREFIX}/beliefs/{belief_id}/attacks")
        resp.raise_for_status()
        return [_parse_attack_edge(e) for e in resp.json()]

    def get_chain(self, belief_id: str) -> list:
        resp = self._http.get(f"{_V4_PREFIX}/beliefs/{belief_id}/attack-chain")
        resp.raise_for_status()
        return resp.json().get("chains", [])

    def deactivate(self, attack_id: str) -> None:
        resp = self._http.delete(f"{_V4_PREFIX}/attacks/{attack_id}")
        resp.raise_for_status()


class ReconsolidationClient:
    """Sub-client for reconsolidation endpoints."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def queue(self) -> ReconsolidationQueueResult:
        resp = self._http.get(f"{_V4_PREFIX}/reconsolidation/queue")
        resp.raise_for_status()
        d = resp.json()
        return ReconsolidationQueueResult(queue_size=d["queue_size"])

    def run(self) -> ReconsolidationRunResult:
        resp = self._http.post(f"{_V4_PREFIX}/reconsolidation/run")
        resp.raise_for_status()
        d = resp.json()
        return ReconsolidationRunResult(
            processed=d["processed"],
            timestamp=d["timestamp"],
        )


class GoalClient:
    """Sub-client for goal endpoints."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def create(
        self,
        goal: str,
        owner: str,
        priority: float = 0.5,
        success_criteria: dict | None = None,
        deadline: str | None = None,
    ) -> GoalResult:
        payload: dict[str, Any] = {
            "goal": goal,
            "owner": owner,
            "priority": priority,
        }
        if success_criteria is not None:
            payload["success_criteria"] = success_criteria
        if deadline is not None:
            payload["deadline"] = deadline
        resp = self._http.post(f"{_V4_PREFIX}/goals", json=payload)
        resp.raise_for_status()
        return _parse_goal(resp.json())

    def list(self) -> list[GoalResult]:
        resp = self._http.get(f"{_V4_PREFIX}/goals")
        resp.raise_for_status()
        return [_parse_goal(g) for g in resp.json()]

    def get(self, goal_id: str) -> GoalResult:
        resp = self._http.get(f"{_V4_PREFIX}/goals/{goal_id}")
        resp.raise_for_status()
        return _parse_goal(resp.json())

    def evaluate(self, goal_id: str) -> GoalEvaluationResult:
        resp = self._http.post(f"{_V4_PREFIX}/goals/{goal_id}/evaluate")
        resp.raise_for_status()
        d = resp.json()
        return GoalEvaluationResult(
            goal_id=d["goal_id"],
            status=d["status"],
            completion_fraction=d["completion_fraction"],
            blocking_belief_ids=d.get("blocking_belief_ids", []),
            supporting_belief_ids=d.get("supporting_belief_ids", []),
        )

    def update_status(self, goal_id: str, status: str) -> GoalResult:
        resp = self._http.put(f"{_V4_PREFIX}/goals/{goal_id}/status", json={"status": status})
        resp.raise_for_status()
        return _parse_goal(resp.json())

    def abandon(self, goal_id: str) -> None:
        resp = self._http.delete(f"{_V4_PREFIX}/goals/{goal_id}")
        resp.raise_for_status()


class PolicyClient:
    """Sub-client for policy endpoints."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def create(
        self,
        name: str,
        steps: list[dict],
        description: str = "",
    ) -> PolicyResult:
        resp = self._http.post(
            f"{_V4_PREFIX}/policies",
            json={"name": name, "steps": steps, "description": description},
        )
        resp.raise_for_status()
        return _parse_policy(resp.json())

    def list(self) -> list[PolicyResult]:
        resp = self._http.get(f"{_V4_PREFIX}/policies")
        resp.raise_for_status()
        return [_parse_policy(p) for p in resp.json()]

    def get(self, policy_id: str) -> PolicyResult:
        resp = self._http.get(f"{_V4_PREFIX}/policies/{policy_id}")
        resp.raise_for_status()
        return _parse_policy(resp.json())

    def get_history(self, policy_id: str) -> list[PolicyResult]:
        resp = self._http.get(f"{_V4_PREFIX}/policies/{policy_id}/history")
        resp.raise_for_status()
        return [_parse_policy(p) for p in resp.json()]

    def update_status(self, policy_id: str, status: str) -> PolicyResult:
        resp = self._http.put(
            f"{_V4_PREFIX}/policies/{policy_id}/status",
            json={"status": status},
        )
        resp.raise_for_status()
        return _parse_policy(resp.json())


class BenchmarkClient:
    """Sub-client for benchmark sandbox/attack endpoints."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def sandbox_fork(self, scenario_label: str = "") -> dict:
        """Fork a benchmark sandbox."""
        from mnemebrain.models import BenchmarkSandboxResult

        resp = self._http.post("/benchmark/sandbox/fork", json={"scenario_label": scenario_label})
        resp.raise_for_status()
        d = resp.json()
        return BenchmarkSandboxResult(
            sandbox_id=d["sandbox_id"],
            resolved_truth_state=d["resolved_truth_state"],
            canonical_unchanged=d["canonical_unchanged"],
        )

    def sandbox_assume(self, sandbox_id: str, belief_id: str, truth_state: str) -> dict:
        """Override a belief's truth state in a benchmark sandbox."""
        from mnemebrain.models import BenchmarkSandboxResult

        resp = self._http.post(
            f"/benchmark/sandbox/{sandbox_id}/assume",
            json={"belief_id": belief_id, "truth_state": truth_state},
        )
        resp.raise_for_status()
        d = resp.json()
        return BenchmarkSandboxResult(
            sandbox_id=d["sandbox_id"],
            resolved_truth_state=d["resolved_truth_state"],
            canonical_unchanged=d["canonical_unchanged"],
        )

    def sandbox_resolve(self, sandbox_id: str, belief_id: str) -> dict:
        """Resolve a belief in a benchmark sandbox."""
        from mnemebrain.models import BenchmarkSandboxResult

        encoded_id = belief_id.replace("#", "%23")
        resp = self._http.get(f"/benchmark/sandbox/{sandbox_id}/resolve/{encoded_id}")
        resp.raise_for_status()
        d = resp.json()
        return BenchmarkSandboxResult(
            sandbox_id=d["sandbox_id"],
            resolved_truth_state=d["resolved_truth_state"],
            canonical_unchanged=d["canonical_unchanged"],
        )

    def sandbox_discard(self, sandbox_id: str) -> None:
        """Discard a benchmark sandbox."""
        resp = self._http.delete(f"/benchmark/sandbox/{sandbox_id}")
        resp.raise_for_status()

    def attack(
        self,
        attacker_id: str,
        target_id: str,
        attack_type: str = "undermining",
        weight: float = 0.5,
    ) -> dict:
        """Create a benchmark attack edge."""
        from mnemebrain.models import BenchmarkAttackResult

        resp = self._http.post(
            "/benchmark/attack",
            json={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "attack_type": attack_type,
                "weight": weight,
            },
        )
        resp.raise_for_status()
        d = resp.json()
        return BenchmarkAttackResult(
            edge_id=d["edge_id"],
            attacker_id=d["attacker_id"],
            target_id=d["target_id"],
        )


class FrameClient:
    """Sub-client for working memory frame endpoints."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def _parse_snapshot(self, s: dict) -> BeliefSnapshot:
        return BeliefSnapshot(
            belief_id=s["belief_id"],
            claim=s["claim"],
            truth_state=s["truth_state"],
            confidence=s["confidence"],
            belief_type=s["belief_type"],
            evidence_count=s["evidence_count"],
            conflict=s["conflict"],
        )

    def open(
        self,
        query_id: str,
        goal_id: str | None = None,
        top_k: int = 20,
        ttl_seconds: int = 300,
    ) -> FrameOpenResult:
        """Open a working memory frame for multi-step reasoning."""
        payload: dict[str, Any] = {
            "query_id": query_id,
            "top_k": top_k,
            "ttl_seconds": ttl_seconds,
        }
        if goal_id is not None:
            payload["goal_id"] = goal_id
        resp = self._http.post("/frame/open", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return FrameOpenResult(
            frame_id=data["frame_id"],
            beliefs_loaded=data["beliefs_loaded"],
            conflicts=data["conflicts"],
            snapshots=[self._parse_snapshot(s) for s in data["snapshots"]],
        )

    def add(self, frame_id: str, claim: str) -> BeliefSnapshot:
        """Add a belief to an active frame."""
        resp = self._http.post(f"/frame/{frame_id}/add", json={"claim": claim})
        resp.raise_for_status()
        return self._parse_snapshot(resp.json())

    def scratchpad(self, frame_id: str, key: str, value: Any) -> None:
        """Write to the frame's scratchpad."""
        resp = self._http.post(
            f"/frame/{frame_id}/scratchpad",
            json={"key": key, "value": value},
        )
        resp.raise_for_status()

    def context(self, frame_id: str) -> FrameContextResult:
        """Get the full active context of a frame."""
        resp = self._http.get(f"/frame/{frame_id}/context")
        resp.raise_for_status()
        data = resp.json()
        return FrameContextResult(
            active_query=data["active_query"],
            active_goal=data.get("active_goal"),
            beliefs=[self._parse_snapshot(s) for s in data["beliefs"]],
            scratchpad=data["scratchpad"],
            conflicts=[self._parse_snapshot(s) for s in data["conflicts"]],
            step_count=data["step_count"],
        )

    def commit(
        self,
        frame_id: str,
        new_beliefs: list[dict] | None = None,
        revisions: list[dict] | None = None,
    ) -> FrameCommitResult:
        """Commit frame results back to the belief graph."""
        payload: dict[str, Any] = {
            "new_beliefs": new_beliefs or [],
            "revisions": revisions or [],
        }
        resp = self._http.post(f"/frame/{frame_id}/commit", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return FrameCommitResult(
            frame_id=data["frame_id"],
            beliefs_created=data["beliefs_created"],
            beliefs_revised=data["beliefs_revised"],
        )

    def close(self, frame_id: str) -> None:
        """Close a frame without committing."""
        resp = self._http.delete(f"/frame/{frame_id}")
        resp.raise_for_status()


class DebugClient:
    """Sub-client for debug/admin endpoints."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def reset(self) -> None:
        """Clear all server state and reinitialise."""
        resp = self._http.post("/reset")
        resp.raise_for_status()

    def set_time_offset(self, days: int) -> None:
        """Backdate evidence timestamps by *days* for decay tests."""
        resp = self._http.post("/debug/set_time_offset", json={"days": days})
        resp.raise_for_status()
