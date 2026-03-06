"""HTTP client for the MnemeBrain REST API."""

from __future__ import annotations

from uuid import uuid4

import httpx

from mnemebrain.models import (
    AskResult,
    BeliefResult,
    EvidenceDetail,
    EvidenceInput,
    ExplanationResult,
    RetrievedBelief,
    SearchResponse,
    SearchResult,
)

DEFAULT_BASE_URL = "http://localhost:8000"


class MnemeBrainClient:
    """Low-level HTTP client wrapping the MnemeBrain REST API."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self._base_url, timeout=timeout)

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
        return [
            BeliefResult(
                id=r["id"],
                truth_state=r["truth_state"],
                confidence=r["confidence"],
                conflict=r["conflict"],
            )
            for r in resp.json()
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
        query_type: str = "FACTUAL",
        agent_id: str | None = None,
        limit: int = 5,
    ) -> AskResult:
        """Ask a question and retrieve relevant beliefs.

        Args:
            question: The question to search for.
            query_type: Query type hint (currently unused, for future routing).
            agent_id: Override agent_id for this query.
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

    def feedback(self, query_id: str, outcome: str = "COMPLETED") -> None:
        """Record feedback for a query. Currently a no-op logged for future use."""
        pass

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Brain:
        return self

    def __exit__(self, *args) -> None:
        self.close()
