"""HTTP client for the MnemeBrain REST API."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx

from mnemebrain.models import (
    AskResult,
    AttackEdgeResult,
    BeliefChangeDetail,
    BeliefListItem,
    BeliefListResponse,
    BeliefResult,
    BeliefSnapshot,
    # Phase 5
    BenchmarkAttackResult,
    BenchmarkSandboxResult,
    ConsolidateResult,
    EvidenceDetail,
    EvidenceInput,
    ExplanationResult,
    FrameCommitResult,
    FrameContextResult,
    FrameOpenResult,
    GoalEvaluationResult,
    GoalResult,
    MemoryTierResult,
    MultihopResponse,
    MultihopResultItem,
    PolicyResult,
    PolicyStepResult,
    ReconsolidationQueueResult,
    ReconsolidationRunResult,
    RetrievedBelief,
    RevisionAuditEntry,
    RevisionEvidenceItem,
    RevisionPolicyResult,
    RevisionResult,
    SandboxCommitResult,
    SandboxContextResult,
    SandboxDiffResult,
    SandboxExplainResult,
    SandboxResult,
    SearchResponse,
    SearchResult,
)

DEFAULT_BASE_URL = "http://localhost:8000"

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
        frame_id: str | None = None,
        scenario_label: str = "",
        ttl_seconds: int = 600,
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
            belief_overrides=d["belief_overrides"],
            added_belief_ids=d["added_belief_ids"],
            invalidated_evidence=d["invalidated_evidence"],
            created_at=d["created_at"],
            expires_at=d.get("expires_at"),
        )

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

    def believe(self, sandbox_id: str, claim: str, belief_type: str = "fact") -> dict[str, str]:
        resp = self._http.post(
            f"{_V4_PREFIX}/sandbox/{sandbox_id}/believe",
            json={"claim": claim, "belief_type": belief_type},
        )
        resp.raise_for_status()
        return resp.json()

    def revise(
        self,
        sandbox_id: str,
        belief_id: str,
        source_ref: str = "",
        content: str = "",
        polarity: str = "supports",
        weight: float = 0.8,
        reliability: float = 0.7,
    ) -> None:
        resp = self._http.post(
            f"{_V4_PREFIX}/sandbox/{sandbox_id}/revise",
            json={
                "belief_id": belief_id,
                "source_ref": source_ref,
                "content": content,
                "polarity": polarity,
                "weight": weight,
                "reliability": reliability,
            },
        )
        resp.raise_for_status()

    def attack(
        self,
        sandbox_id: str,
        attacker_belief_id: str,
        target_belief_id: str,
        attack_type: str,
        weight: float = 0.5,
    ) -> dict[str, str]:
        resp = self._http.post(
            f"{_V4_PREFIX}/sandbox/{sandbox_id}/attack",
            json={
                "attacker_belief_id": attacker_belief_id,
                "target_belief_id": target_belief_id,
                "attack_type": attack_type,
                "weight": weight,
            },
        )
        resp.raise_for_status()
        return resp.json()

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
                for c in d["belief_changes"]
            ],
            evidence_invalidations=d["evidence_invalidations"],
            new_beliefs=d["new_beliefs"],
            temporary_attacks=d["temporary_attacks"],
            goal_changes=d["goal_changes"],
            summary=d["summary"],
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

    def explain(self, sandbox_id: str, belief_id: str) -> SandboxExplainResult:
        resp = self._http.get(f"{_V4_PREFIX}/sandbox/{sandbox_id}/explain/{belief_id}")
        resp.raise_for_status()
        d = resp.json()
        return SandboxExplainResult(
            belief_id=d["belief_id"],
            sandbox_id=d["sandbox_id"],
            resolved_truth_state=d["resolved_truth_state"],
            has_override=d["has_override"],
            override_fields=d["override_fields"],
            invalidated_evidence_ids=d["invalidated_evidence_ids"],
            source=d["source"],
        )

    def evaluate_goal(self, sandbox_id: str, goal_id: str) -> GoalEvaluationResult:
        resp = self._http.post(f"{_V4_PREFIX}/sandbox/{sandbox_id}/goal/{goal_id}/evaluate")
        resp.raise_for_status()
        d = resp.json()
        return GoalEvaluationResult(
            goal_id=d["goal_id"],
            status=d["status"],
            completion_fraction=d["completion_fraction"],
            blocking_belief_ids=d["blocking_belief_ids"],
            supporting_belief_ids=d["supporting_belief_ids"],
        )


class RevisionClient:
    """Sub-client for revision (phase 3) endpoints."""

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

    def revise(
        self,
        incoming_belief_id: str,
        conflicting_evidence: list[RevisionEvidenceItem] | None = None,
        incoming_evidence: list[RevisionEvidenceItem] | None = None,
        agent_id: str = "",
    ) -> RevisionResult:
        payload: dict[str, Any] = {
            "incoming_belief_id": incoming_belief_id,
            "conflicting_evidence": [e.to_dict() for e in (conflicting_evidence or [])],
            "incoming_evidence": [e.to_dict() for e in (incoming_evidence or [])],
            "agent_id": agent_id,
        }
        resp = self._http.post(f"{_V4_PREFIX}/revise", json=payload)
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
    """Sub-client for attack (phase 3.5) endpoints."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def create(
        self,
        belief_id: str,
        target_belief_id: str,
        attack_type: str,
        weight: float,
    ) -> AttackEdgeResult:
        resp = self._http.post(
            f"{_V4_PREFIX}/beliefs/{belief_id}/attacks",
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

    def get_chain(self, belief_id: str, max_depth: int = 2) -> list[list[AttackEdgeResult]]:
        resp = self._http.get(
            f"{_V4_PREFIX}/beliefs/{belief_id}/attack-chain",
            params={"max_depth": max_depth},
        )
        resp.raise_for_status()
        return [[_parse_attack_edge(e) for e in chain] for chain in resp.json()["chains"]]

    def deactivate(self, edge_id: str) -> None:
        resp = self._http.delete(f"{_V4_PREFIX}/attacks/{edge_id}")
        resp.raise_for_status()


class ReconsolidationClient:
    """Sub-client for reconsolidation (phase 4) endpoints."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def queue(self) -> ReconsolidationQueueResult:
        resp = self._http.get(f"{_V4_PREFIX}/reconsolidation/queue")
        resp.raise_for_status()
        return ReconsolidationQueueResult(queue_size=resp.json()["queue_size"])

    def run(self) -> ReconsolidationRunResult:
        resp = self._http.post(f"{_V4_PREFIX}/reconsolidation/run")
        resp.raise_for_status()
        d = resp.json()
        return ReconsolidationRunResult(processed=d["processed"], timestamp=d["timestamp"])


class GoalClient:
    """Sub-client for goal (phase 4) endpoints."""

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
            blocking_belief_ids=d["blocking_belief_ids"],
            supporting_belief_ids=d["supporting_belief_ids"],
        )

    def update_status(self, goal_id: str, status: str) -> GoalResult:
        resp = self._http.put(f"{_V4_PREFIX}/goals/{goal_id}/status", json={"status": status})
        resp.raise_for_status()
        return _parse_goal(resp.json())

    def abandon(self, goal_id: str) -> None:
        resp = self._http.delete(f"{_V4_PREFIX}/goals/{goal_id}")
        resp.raise_for_status()


class PolicyClient:
    """Sub-client for policy/procedural memory (phase 4.5) endpoints."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def create(
        self,
        name: str,
        steps: list[dict],
        description: str = "",
        applicability: dict | None = None,
    ) -> PolicyResult:
        payload: dict[str, Any] = {
            "name": name,
            "description": description,
            "steps": steps,
            "applicability": applicability or {},
        }
        resp = self._http.post(f"{_V4_PREFIX}/policies", json=payload)
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


class MnemeBrainClient:
    """Low-level HTTP client wrapping the MnemeBrain REST API."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self._base_url, timeout=timeout)
        self._sandbox: SandboxClient | None = None
        self._revision: RevisionClient | None = None
        self._attacks: AttackClient | None = None
        self._reconsolidation: ReconsolidationClient | None = None
        self._goals: GoalClient | None = None
        self._policies: PolicyClient | None = None

    @property
    def sandbox(self) -> SandboxClient:
        if self._sandbox is None:
            self._sandbox = SandboxClient(self._client)
        return self._sandbox

    @property
    def revision(self) -> RevisionClient:
        if self._revision is None:
            self._revision = RevisionClient(self._client)
        return self._revision

    @property
    def attacks(self) -> AttackClient:
        if self._attacks is None:
            self._attacks = AttackClient(self._client)
        return self._attacks

    @property
    def reconsolidation(self) -> ReconsolidationClient:
        if self._reconsolidation is None:
            self._reconsolidation = ReconsolidationClient(self._client)
        return self._reconsolidation

    @property
    def goals(self) -> GoalClient:
        if self._goals is None:
            self._goals = GoalClient(self._client)
        return self._goals

    @property
    def policies(self) -> PolicyClient:
        if self._policies is None:
            self._policies = PolicyClient(self._client)
        return self._policies

    def health(self) -> dict:
        resp = self._client.get("/health")
        resp.raise_for_status()
        return resp.json()

    def believe(
        self,
        claim: str,
        evidence: list[EvidenceInput],
        belief_type: str = "inference",
        tags: list[str] | None = None,
        source_agent: str = "",
    ) -> BeliefResult:
        payload = {
            "claim": claim,
            "evidence": [e.to_dict() for e in evidence],
            "belief_type": belief_type,
            "tags": tags or [],
            "source_agent": source_agent,
        }
        resp = self._client.post("/believe", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return BeliefResult(
            id=data["id"],
            truth_state=data["truth_state"],
            confidence=data["confidence"],
            conflict=data["conflict"],
            was_separated=data.get("was_separated", False),
            memory_tier=data.get("memory_tier", "episodic"),
            evidence_ids=data.get("evidence_ids"),
        )

    def explain(self, claim: str) -> ExplanationResult | None:
        resp = self._client.get("/explain", params={"claim": claim})
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

        def _parse_evidence(items: list[dict]) -> list[EvidenceDetail]:
            return [
                EvidenceDetail(
                    id=e["id"],
                    source_ref=e["source_ref"],
                    content=e["content"],
                    polarity=e["polarity"],
                    weight=e["weight"],
                    reliability=e["reliability"],
                    scope=e.get("scope"),
                )
                for e in items
            ]

        return ExplanationResult(
            claim=data["claim"],
            truth_state=data["truth_state"],
            confidence=data["confidence"],
            supporting=_parse_evidence(data["supporting"]),
            attacking=_parse_evidence(data["attacking"]),
            expired=_parse_evidence(data["expired"]),
        )

    def search(
        self,
        query: str,
        limit: int = 10,
        alpha: float = 0.7,
        conflict_policy: str = "surface",
    ) -> SearchResponse:
        resp = self._client.get(
            "/search",
            params={
                "query": query,
                "limit": limit,
                "alpha": alpha,
                "conflict_policy": conflict_policy,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return SearchResponse(
            results=[
                SearchResult(
                    belief_id=r["belief_id"],
                    claim=r["claim"],
                    truth_state=r["truth_state"],
                    confidence=r["confidence"],
                    similarity=r["similarity"],
                    rank_score=r["rank_score"],
                )
                for r in data["results"]
            ]
        )

    def retract(self, evidence_id: str) -> list[BeliefResult]:
        resp = self._client.post("/retract", json={"evidence_id": evidence_id})
        resp.raise_for_status()
        data = resp.json()
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        return [
            BeliefResult(
                id=r["id"],
                truth_state=r["truth_state"],
                confidence=r["confidence"],
                conflict=r["conflict"],
            )
            for r in items
        ]

    def revise(self, belief_id: str, evidence: EvidenceInput) -> BeliefResult:
        payload = {
            "belief_id": belief_id,
            "evidence": evidence.to_dict(),
        }
        resp = self._client.post("/revise", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return BeliefResult(
            id=data["id"],
            truth_state=data["truth_state"],
            confidence=data["confidence"],
            conflict=data["conflict"],
        )

    def list_beliefs(
        self,
        truth_state: str | None = None,
        belief_type: str | None = None,
        tag: str | None = None,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0,
        limit: int = 50,
        offset: int = 0,
    ) -> BeliefListResponse:
        """List beliefs with optional filters."""
        params: dict[str, Any] = {
            "min_confidence": min_confidence,
            "max_confidence": max_confidence,
            "limit": limit,
            "offset": offset,
        }
        if truth_state is not None:
            params["truth_state"] = truth_state
        if belief_type is not None:
            params["belief_type"] = belief_type
        if tag is not None:
            params["tag"] = tag
        resp = self._client.get("/beliefs", params=params)
        resp.raise_for_status()
        data = resp.json()
        return BeliefListResponse(
            beliefs=[
                BeliefListItem(
                    id=b["id"],
                    claim=b["claim"],
                    belief_type=b["belief_type"],
                    truth_state=b["truth_state"],
                    confidence=b["confidence"],
                    tag_count=b["tag_count"],
                    evidence_count=b["evidence_count"],
                    created_at=b["created_at"],
                    last_revised=b["last_revised"],
                )
                for b in data["beliefs"]
            ],
            total=data["total"],
            offset=data["offset"],
            limit=data["limit"],
        )

    # -- Phase 2: WorkingMemoryFrame endpoints --

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

    def frame_open(
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
        resp = self._client.post("/frame/open", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return FrameOpenResult(
            frame_id=data["frame_id"],
            beliefs_loaded=data["beliefs_loaded"],
            conflicts=data["conflicts"],
            snapshots=[self._parse_snapshot(s) for s in data["snapshots"]],
        )

    def frame_add(self, frame_id: str, claim: str) -> BeliefSnapshot:
        """Add a belief to an active frame."""
        resp = self._client.post(f"/frame/{frame_id}/add", json={"claim": claim})
        resp.raise_for_status()
        return self._parse_snapshot(resp.json())

    def frame_scratchpad(self, frame_id: str, key: str, value: Any) -> None:
        """Write to the frame's scratchpad."""
        resp = self._client.post(
            f"/frame/{frame_id}/scratchpad",
            json={"key": key, "value": value},
        )
        resp.raise_for_status()

    def frame_context(self, frame_id: str) -> FrameContextResult:
        """Get the full active context of a frame."""
        resp = self._client.get(f"/frame/{frame_id}/context")
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

    def frame_commit(
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
        resp = self._client.post(f"/frame/{frame_id}/commit", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return FrameCommitResult(
            frame_id=data["frame_id"],
            beliefs_created=data["beliefs_created"],
            beliefs_revised=data["beliefs_revised"],
        )

    def frame_close(self, frame_id: str) -> None:
        """Close a frame without committing."""
        resp = self._client.delete(f"/frame/{frame_id}")
        resp.raise_for_status()

    # -- Phase 5 endpoints --

    def reset(self) -> None:
        """Clear all server state and reinitialise."""
        resp = self._client.post("/reset")
        resp.raise_for_status()

    def set_time_offset(self, days: int) -> None:
        """Backdate evidence timestamps by *days* for decay tests."""
        resp = self._client.post("/debug/set_time_offset", json={"days": days})
        resp.raise_for_status()

    def consolidate(self) -> ConsolidateResult:
        """Run one consolidation cycle."""
        resp = self._client.post("/consolidate")
        resp.raise_for_status()
        d = resp.json()
        return ConsolidateResult(
            semantic_beliefs_created=d["semantic_beliefs_created"],
            episodics_pruned=d["episodics_pruned"],
            clusters_found=d["clusters_found"],
        )

    def get_memory_tier(self, belief_id: str) -> MemoryTierResult:
        """Return memory-tier metadata for a belief."""
        encoded_id = belief_id.replace("#", "%23")
        resp = self._client.get(f"/memory_tier/{encoded_id}")
        resp.raise_for_status()
        d = resp.json()
        return MemoryTierResult(
            belief_id=d["belief_id"],
            memory_tier=d["memory_tier"],
            consolidated_from_count=d["consolidated_from_count"],
        )

    def query_multihop(self, query: str) -> MultihopResponse:
        """HippoRAG multi-hop retrieval."""
        resp = self._client.post("/query_multihop", json={"query": query})
        resp.raise_for_status()
        d = resp.json()
        return MultihopResponse(
            results=[
                MultihopResultItem(
                    belief_id=r["belief_id"],
                    claim=r["claim"],
                    confidence=r["confidence"],
                    truth_state=r["truth_state"],
                )
                for r in d["results"]
            ]
        )

    # -- Benchmark sandbox/attack endpoints --

    def benchmark_sandbox_fork(self, scenario_label: str = "") -> BenchmarkSandboxResult:
        """Fork a benchmark sandbox."""
        resp = self._client.post("/benchmark/sandbox/fork", json={"scenario_label": scenario_label})
        resp.raise_for_status()
        d = resp.json()
        return BenchmarkSandboxResult(
            sandbox_id=d["sandbox_id"],
            resolved_truth_state=d["resolved_truth_state"],
            canonical_unchanged=d["canonical_unchanged"],
        )

    def benchmark_sandbox_assume(
        self, sandbox_id: str, belief_id: str, truth_state: str
    ) -> BenchmarkSandboxResult:
        """Override a belief's truth state in a benchmark sandbox."""
        resp = self._client.post(
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

    def benchmark_sandbox_resolve(self, sandbox_id: str, belief_id: str) -> BenchmarkSandboxResult:
        """Resolve a belief in a benchmark sandbox."""
        encoded_id = belief_id.replace("#", "%23")
        resp = self._client.get(f"/benchmark/sandbox/{sandbox_id}/resolve/{encoded_id}")
        resp.raise_for_status()
        d = resp.json()
        return BenchmarkSandboxResult(
            sandbox_id=d["sandbox_id"],
            resolved_truth_state=d["resolved_truth_state"],
            canonical_unchanged=d["canonical_unchanged"],
        )

    def benchmark_sandbox_discard(self, sandbox_id: str) -> None:
        """Discard a benchmark sandbox."""
        resp = self._client.delete(f"/benchmark/sandbox/{sandbox_id}")
        resp.raise_for_status()

    def benchmark_attack(
        self,
        attacker_id: str,
        target_id: str,
        attack_type: str = "undermining",
        weight: float = 0.5,
    ) -> BenchmarkAttackResult:
        """Create a benchmark attack edge."""
        resp = self._client.post(
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

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> MnemeBrainClient:
        return self

    def __exit__(self, *args) -> None:
        self.close()


class Brain:
    """High-level experiment-friendly API matching the proof-the-claim doc.

    Usage:
        brain = Brain(agent_id="experiment-7b")
        brain.believe(claim="Paris is the capital of France", evidence=["wiki_123"], confidence=0.9)
        result = brain.ask(question="What is the capital of France?")
        for belief in result.retrieved_beliefs:
            print(belief.claim)
    """

    def __init__(
        self,
        agent_id: str = "default",
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self.agent_id = agent_id
        self._client = MnemeBrainClient(base_url=base_url, timeout=timeout)

    def believe(
        self,
        claim: str,
        evidence: list[str] | None = None,
        confidence: float = 0.8,
        belief_type: str = "inference",
    ) -> BeliefResult:
        """Store a belief with evidence. Simplified API for experiments.

        Args:
            claim: The belief claim text.
            evidence: List of evidence source references (strings).
            confidence: Confidence weight for the evidence (0.0–1.0).
            belief_type: One of "fact", "preference", "inference", "prediction".
        """
        evidence_items = [
            EvidenceInput(
                source_ref=ref,
                content=claim,
                polarity="supports",
                weight=confidence,
                reliability=confidence,
            )
            for ref in (evidence or ["auto"])
        ]
        return self._client.believe(
            claim=claim,
            evidence=evidence_items,
            belief_type=belief_type,
            source_agent=self.agent_id,
        )

    def ask(
        self,
        question: str,
        limit: int = 5,
    ) -> AskResult:
        """Ask a question and retrieve relevant beliefs.

        Args:
            question: The question to search for.
            limit: Max beliefs to retrieve.
        """
        response = self._client.search(query=question, limit=limit)
        retrieved = [
            RetrievedBelief(
                claim=r.claim,
                confidence=r.confidence,
                similarity=r.similarity,
            )
            for r in response.results
        ]
        return AskResult(
            query_id=str(uuid4()),
            retrieved_beliefs=retrieved,
        )

    def explain(self, claim: str) -> ExplanationResult | None:
        """Explain a belief's truth state with full evidence provenance.

        Args:
            claim: The belief claim text to explain.

        Returns:
            ExplanationResult with supporting/attacking/expired evidence,
            or None if no matching belief is found.
        """
        return self._client.explain(claim)

    def feedback(self, query_id: str, outcome: str = "COMPLETED") -> None:
        """Record feedback for a query.

        Raises:
            NotImplementedError: This endpoint is not yet available.
        """
        raise NotImplementedError("feedback endpoint is not yet implemented")

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Brain:
        return self

    def __exit__(self, *args) -> None:
        self.close()
