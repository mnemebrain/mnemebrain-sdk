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
