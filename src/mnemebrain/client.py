"""HTTP client for the MnemeBrain REST API."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx

from mnemebrain.models import (
    AskResult,
    BeliefListItem,
    BeliefListResponse,
    BeliefResult,
    ConsolidateResult,
    EvidenceDetail,
    EvidenceInput,
    ExplanationResult,
    MemoryTierResult,
    MultihopResponse,
    MultihopResultItem,
    RetrievedBelief,
    SearchResponse,
    SearchResult,
)
from mnemebrain.v4 import (
    AttackClient,
    BenchmarkClient,
    DebugClient,
    FrameClient,
    GoalClient,
    PolicyClient,
    ReconsolidationClient,
    RevisionClient,
    SandboxClient,
)

DEFAULT_BASE_URL = "http://localhost:8000"


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
        self._benchmark: BenchmarkClient | None = None
        self._frames: FrameClient | None = None
        self._debug: DebugClient | None = None

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

    @property
    def benchmark(self) -> BenchmarkClient:
        if self._benchmark is None:
            self._benchmark = BenchmarkClient(self._client)
        return self._benchmark

    @property
    def frames(self) -> FrameClient:
        if self._frames is None:
            self._frames = FrameClient(self._client)
        return self._frames

    @property
    def debug(self) -> DebugClient:
        if self._debug is None:
            self._debug = DebugClient(self._client)
        return self._debug

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
        brain.believe(claim="Paris is the capital of France",
                      evidence=["wiki_123"], confidence=0.9)
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
            confidence: Confidence weight for the evidence (0.0-1.0).
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

    def consolidate(self) -> ConsolidateResult:
        """Run one consolidation cycle."""
        return self._client.consolidate()

    def get_memory_tier(self, belief_id: str) -> MemoryTierResult:
        """Return memory-tier metadata for a belief."""
        return self._client.get_memory_tier(belief_id)

    def multihop(self, query: str) -> MultihopResponse:
        """HippoRAG multi-hop retrieval."""
        return self._client.query_multihop(query)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Brain:
        return self

    def __exit__(self, *args) -> None:
        self.close()
