"""Tests for MnemeBrain SDK data models."""

from mnemebrain.models import (
    AskResult,
    BeliefResult,
    BeliefType,
    EvidenceDetail,
    EvidenceInput,
    ExplanationResult,
    Polarity,
    RetrievedBelief,
    SearchResponse,
    SearchResult,
    TruthState,
)


class TestEnums:
    def test_truth_state_values(self):
        assert TruthState.TRUE == "true"
        assert TruthState.FALSE == "false"
        assert TruthState.BOTH == "both"
        assert TruthState.NEITHER == "neither"

    def test_belief_type_values(self):
        assert BeliefType.FACT == "fact"
        assert BeliefType.PREFERENCE == "preference"
        assert BeliefType.INFERENCE == "inference"
        assert BeliefType.PREDICTION == "prediction"

    def test_polarity_values(self):
        assert Polarity.SUPPORTS == "supports"
        assert Polarity.ATTACKS == "attacks"


class TestEvidenceInput:
    def test_to_dict_without_scope(self):
        ev = EvidenceInput(source_ref="ref1", content="test content")
        d = ev.to_dict()
        assert d == {
            "source_ref": "ref1",
            "content": "test content",
            "polarity": "supports",
            "weight": 0.7,
            "reliability": 0.8,
        }
        assert "scope" not in d

    def test_to_dict_with_scope(self):
        ev = EvidenceInput(
            source_ref="ref1",
            content="test content",
            polarity="attacks",
            weight=0.5,
            reliability=0.6,
            scope="global",
        )
        d = ev.to_dict()
        assert d["scope"] == "global"
        assert d["polarity"] == "attacks"
        assert d["weight"] == 0.5
        assert d["reliability"] == 0.6

    def test_defaults(self):
        ev = EvidenceInput(source_ref="r", content="c")
        assert ev.polarity == "supports"
        assert ev.weight == 0.7
        assert ev.reliability == 0.8
        assert ev.scope is None


class TestDataclasses:
    def test_belief_result(self):
        r = BeliefResult(id="abc", truth_state="true", confidence=0.9, conflict=False)
        assert r.id == "abc"
        assert r.conflict is False

    def test_evidence_detail(self):
        e = EvidenceDetail(
            id="e1",
            source_ref="s",
            content="c",
            polarity="supports",
            weight=0.7,
            reliability=0.8,
        )
        assert e.scope is None
        e2 = EvidenceDetail(
            id="e2",
            source_ref="s",
            content="c",
            polarity="attacks",
            weight=0.5,
            reliability=0.6,
            scope="local",
        )
        assert e2.scope == "local"

    def test_explanation_result_defaults(self):
        r = ExplanationResult(claim="test", truth_state="true", confidence=0.9)
        assert r.supporting == []
        assert r.attacking == []
        assert r.expired == []

    def test_search_response_defaults(self):
        r = SearchResponse()
        assert r.results == []

    def test_search_result(self):
        r = SearchResult(
            belief_id="b1",
            claim="test",
            truth_state="true",
            confidence=0.9,
            similarity=0.8,
            rank_score=0.85,
        )
        assert r.rank_score == 0.85

    def test_retrieved_belief(self):
        b = RetrievedBelief(claim="test", confidence=0.9, similarity=0.8)
        assert b.claim == "test"

    def test_ask_result_defaults(self):
        r = AskResult(query_id="q1")
        assert r.retrieved_beliefs == []
