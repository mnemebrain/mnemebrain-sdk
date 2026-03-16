"""Data models for the MnemeBrain Python SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TruthState(str, Enum):
    TRUE = "true"
    FALSE = "false"
    BOTH = "both"
    NEITHER = "neither"


class BeliefType(str, Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    INFERENCE = "inference"
    PREDICTION = "prediction"


class Polarity(str, Enum):
    SUPPORTS = "supports"
    ATTACKS = "attacks"


@dataclass
class EvidenceInput:
    """Evidence to attach to a belief."""

    source_ref: str
    content: str
    polarity: str = "supports"
    weight: float = 0.7
    reliability: float = 0.8
    scope: str | None = None

    def to_dict(self) -> dict:
        d = {
            "source_ref": self.source_ref,
            "content": self.content,
            "polarity": self.polarity,
            "weight": self.weight,
            "reliability": self.reliability,
        }
        if self.scope is not None:
            d["scope"] = self.scope
        return d


@dataclass
class BeliefResult:
    """Result from believe/revise operations."""

    id: str
    truth_state: str
    confidence: float
    conflict: bool
    was_separated: bool = False
    memory_tier: str = "episodic"
    evidence_ids: list[str] | None = None


@dataclass
class EvidenceDetail:
    """Evidence detail from explain responses."""

    id: str
    source_ref: str
    content: str
    polarity: str
    weight: float
    reliability: float
    scope: str | None = None


@dataclass
class ExplanationResult:
    """Result from explain operation."""

    claim: str
    truth_state: str
    confidence: float
    supporting: list[EvidenceDetail] = field(default_factory=list)
    attacking: list[EvidenceDetail] = field(default_factory=list)
    expired: list[EvidenceDetail] = field(default_factory=list)


@dataclass
class SearchResult:
    """A single search hit."""

    belief_id: str
    claim: str
    truth_state: str
    confidence: float
    similarity: float
    rank_score: float


@dataclass
class SearchResponse:
    """Result from search operation."""

    results: list[SearchResult] = field(default_factory=list)


@dataclass
class BeliefListItem:
    """A belief in a list response."""

    id: str
    claim: str
    belief_type: str
    truth_state: str
    confidence: float
    tag_count: int
    evidence_count: int
    created_at: str
    last_revised: str


@dataclass
class BeliefListResponse:
    """Result from list_beliefs operation."""

    beliefs: list[BeliefListItem] = field(default_factory=list)
    total: int = 0
    offset: int = 0
    limit: int = 50


@dataclass
class BeliefSnapshot:
    """A belief snapshot in a working memory frame."""

    belief_id: str
    claim: str
    truth_state: str
    confidence: float
    belief_type: str
    evidence_count: int
    conflict: bool


@dataclass
class FrameOpenResult:
    """Result from opening a working memory frame."""

    frame_id: str
    beliefs_loaded: int
    conflicts: int
    snapshots: list[BeliefSnapshot] = field(default_factory=list)


@dataclass
class FrameContextResult:
    """Result from getting frame context."""

    active_query: str
    active_goal: str | None = None
    beliefs: list[BeliefSnapshot] = field(default_factory=list)
    scratchpad: dict = field(default_factory=dict)
    conflicts: list[BeliefSnapshot] = field(default_factory=list)
    step_count: int = 0


@dataclass
class FrameCommitResult:
    """Result from committing a frame."""

    frame_id: str
    beliefs_created: int
    beliefs_revised: int


@dataclass
class RetrievedBelief:
    """A belief retrieved by Brain.ask() — simplified view for experiments."""

    claim: str
    confidence: float
    similarity: float


@dataclass
class AskResult:
    """Result from Brain.ask() — experiment-friendly query result."""

    query_id: str
    retrieved_beliefs: list[RetrievedBelief] = field(default_factory=list)


# ---------------------------------------------------------------------------
# V4 Enums (Phase 1–4.5)
# ---------------------------------------------------------------------------


class SandboxStatus(str, Enum):
    ACTIVE = "active"
    COMMITTED = "committed"
    DISCARDED = "discarded"
    EXPIRED = "expired"


class CommitMode(str, Enum):
    SELECTIVE = "selective"
    ALL = "all"
    DISCARD_CONFLICTS = "discard_conflicts"


class AttackType(str, Enum):
    CONTRADICTS = "contradicts"
    UNDERMINES = "undermines"
    REBUTS = "rebuts"
    UNDERCUTS = "undercuts"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class PolicyStatus(str, Enum):
    ACTIVE = "active"
    FLAGGED_FOR_REVISION = "flagged_for_revision"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


# ---------------------------------------------------------------------------
# V4 Dataclasses — Sandbox
# ---------------------------------------------------------------------------


@dataclass
class SandboxResult:
    """Result from sandbox fork/quick operations."""

    id: str
    frame_id: str | None
    scenario_label: str
    status: str
    created_at: str
    expires_at: str | None


@dataclass
class SandboxContextResult:
    """Full state of a sandbox."""

    id: str
    frame_id: str | None
    scenario_label: str
    status: str
    belief_overrides: dict
    added_belief_ids: list[str]
    invalidated_evidence: list[str]
    created_at: str
    expires_at: str | None


@dataclass
class BeliefChangeDetail:
    """A single field change within a sandbox diff."""

    belief_id: str
    field: str
    old_value: object
    new_value: object


@dataclass
class SandboxDiffResult:
    """Diff between sandbox and parent graph."""

    belief_changes: list[BeliefChangeDetail] = field(default_factory=list)
    evidence_invalidations: list[str] = field(default_factory=list)
    new_beliefs: list[str] = field(default_factory=list)
    temporary_attacks: list[object] = field(default_factory=list)
    goal_changes: list[object] = field(default_factory=list)
    summary: str = ""


@dataclass
class SandboxCommitResult:
    """Result from committing a sandbox."""

    sandbox_id: str
    committed_belief_ids: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)


@dataclass
class SandboxExplainResult:
    """Explanation of a belief's state within a sandbox."""

    belief_id: str
    sandbox_id: str
    resolved_truth_state: str
    has_override: bool
    override_fields: list[str] = field(default_factory=list)
    invalidated_evidence_ids: list[str] = field(default_factory=list)
    source: str = ""


# ---------------------------------------------------------------------------
# V4 Dataclasses — Revision
# ---------------------------------------------------------------------------


@dataclass
class RevisionPolicyResult:
    """Current revision policy configuration."""

    policy_name: str
    max_retraction_depth: int
    max_retractions: int


@dataclass
class RevisionAuditEntry:
    """A single revision audit log entry."""

    id: str
    timestamp: str
    incoming_belief_id: str
    policy_name: str
    revision_depth: int
    bounded: bool
    agent_id: str


@dataclass
class RevisionEvidenceItem:
    """Evidence item for v4 revise operations."""

    source_ref: str = ""
    content: str = ""
    polarity: str = "supports"
    weight: float = 0.8
    reliability: float = 0.7
    id: str | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "source_ref": self.source_ref,
            "content": self.content,
            "polarity": self.polarity,
            "weight": self.weight,
            "reliability": self.reliability,
        }
        if self.id is not None:
            d["id"] = self.id
        return d


@dataclass
class RevisionResult:
    """Result from v4 revise operation."""

    superseded_evidence_ids: list[str] = field(default_factory=list)
    retracted_belief_ids: list[str] = field(default_factory=list)
    revision_depth: int = 0
    policy_name: str = ""
    bounded: bool = False


# ---------------------------------------------------------------------------
# V4 Dataclasses — Attacks
# ---------------------------------------------------------------------------


@dataclass
class AttackEdgeResult:
    """An attack edge between two beliefs."""

    id: str
    source_belief_id: str
    target_belief_id: str
    attack_type: str
    weight: float
    active: bool
    created_at: str


# ---------------------------------------------------------------------------
# V4 Dataclasses — Reconsolidation
# ---------------------------------------------------------------------------


@dataclass
class ReconsolidationQueueResult:
    """Reconsolidation scheduler queue status."""

    queue_size: int


@dataclass
class ReconsolidationRunResult:
    """Result from triggering a reconsolidation cycle."""

    processed: int
    timestamp: str


# ---------------------------------------------------------------------------
# V4 Dataclasses — Goals
# ---------------------------------------------------------------------------


@dataclass
class GoalResult:
    """A goal node."""

    id: str
    goal: str
    owner: str
    priority: float
    status: str
    created_at: str
    deadline: str | None = None
    success_criteria: dict = field(default_factory=dict)


@dataclass
class GoalEvaluationResult:
    """Result from evaluating a goal."""

    goal_id: str
    status: str
    completion_fraction: float
    blocking_belief_ids: list[str] = field(default_factory=list)
    supporting_belief_ids: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# V4 Dataclasses — Policy
# ---------------------------------------------------------------------------


@dataclass
class PolicyStepResult:
    """A single step in a policy."""

    step_id: int
    action: str
    tool: str | None = None
    conditions: list[str] = field(default_factory=list)
    fallback: str | None = None


@dataclass
class PolicyResult:
    """A policy node."""

    id: str
    name: str
    description: str
    version: int
    reliability: float
    status: str
    created_at: str
    last_updated: str
    superseded_by: str | None = None
    steps: list[PolicyStepResult] = field(default_factory=list)
    applicability: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Phase 5 Dataclasses — Consolidation, Memory Tiers, HippoRAG
# ---------------------------------------------------------------------------


@dataclass
class ConsolidateResult:
    """Result from running a consolidation cycle."""

    semantic_beliefs_created: int
    episodics_pruned: int
    clusters_found: int


@dataclass
class MemoryTierResult:
    """Memory tier metadata for a belief."""

    belief_id: str
    memory_tier: str
    consolidated_from_count: int


@dataclass
class MultihopResultItem:
    """A single result from multi-hop retrieval."""

    belief_id: str
    claim: str
    confidence: float
    truth_state: str


@dataclass
class MultihopResponse:
    """Result from multi-hop query."""

    results: list[MultihopResultItem] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Benchmark Dataclasses — simplified sandbox/attack for benchmark harness
# ---------------------------------------------------------------------------


@dataclass
class BenchmarkSandboxResult:
    """Simplified sandbox result for benchmark."""

    sandbox_id: str
    resolved_truth_state: str
    canonical_unchanged: bool


@dataclass
class BenchmarkAttackResult:
    """Simplified attack result for benchmark."""

    edge_id: str
    attacker_id: str
    target_id: str
