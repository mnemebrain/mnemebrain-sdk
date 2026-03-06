"""Tests for the MnemeBrain Python SDK client."""

import httpx
import pytest
import respx

from mnemebrain import Brain, MnemeBrainClient, EvidenceInput


BASE_URL = "http://localhost:8000"


class TestMnemeBrainClient:
    """Tests for the low-level HTTP client."""

    @respx.mock
    def test_health(self):
        respx.get(f"{BASE_URL}/health").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.health()
        assert result == {"status": "ok"}
        client.close()

    @respx.mock
    def test_believe(self):
        respx.post(f"{BASE_URL}/believe").mock(
            return_value=httpx.Response(200, json={
                "id": "abc-123",
                "truth_state": "true",
                "confidence": 0.85,
                "conflict": False,
            })
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.believe(
            claim="user is vegetarian",
            evidence=[EvidenceInput(
                source_ref="msg_12",
                content="They said no meat please",
                polarity="supports",
                weight=0.8,
                reliability=0.9,
            )],
        )
        assert result.id == "abc-123"
        assert result.truth_state == "true"
        assert result.confidence == 0.85
        assert result.conflict is False
        client.close()

    @respx.mock
    def test_search(self):
        respx.get(f"{BASE_URL}/search").mock(
            return_value=httpx.Response(200, json={
                "results": [{
                    "belief_id": "b-1",
                    "claim": "user is vegetarian",
                    "truth_state": "true",
                    "confidence": 0.85,
                    "similarity": 0.92,
                    "rank_score": 0.88,
                }]
            })
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.search(query="vegetarian")
        assert len(result.results) == 1
        assert result.results[0].claim == "user is vegetarian"
        assert result.results[0].similarity == 0.92
        client.close()

    @respx.mock
    def test_explain(self):
        respx.get(f"{BASE_URL}/explain").mock(
            return_value=httpx.Response(200, json={
                "claim": "user is vegetarian",
                "truth_state": "true",
                "confidence": 0.85,
                "supporting": [{
                    "id": "e-1",
                    "source_ref": "msg_12",
                    "content": "no meat",
                    "polarity": "supports",
                    "weight": 0.8,
                    "reliability": 0.9,
                }],
                "attacking": [],
                "expired": [],
            })
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.explain("user is vegetarian")
        assert result is not None
        assert result.truth_state == "true"
        assert len(result.supporting) == 1
        assert result.supporting[0].source_ref == "msg_12"
        client.close()

    @respx.mock
    def test_explain_not_found(self):
        respx.get(f"{BASE_URL}/explain").mock(
            return_value=httpx.Response(404, json={"detail": "Belief not found"})
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.explain("nonexistent claim")
        assert result is None
        client.close()

    @respx.mock
    def test_retract(self):
        respx.post(f"{BASE_URL}/retract").mock(
            return_value=httpx.Response(200, json=[{
                "id": "b-1",
                "truth_state": "neither",
                "confidence": 0.0,
                "conflict": False,
            }])
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        results = client.retract("e-1")
        assert len(results) == 1
        assert results[0].truth_state == "neither"
        client.close()

    @respx.mock
    def test_revise(self):
        respx.post(f"{BASE_URL}/revise").mock(
            return_value=httpx.Response(200, json={
                "id": "b-1",
                "truth_state": "true",
                "confidence": 0.95,
                "conflict": False,
            })
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.revise(
            belief_id="b-1",
            evidence=EvidenceInput(
                source_ref="msg_50",
                content="confirmed",
                polarity="supports",
                weight=0.9,
                reliability=0.95,
            ),
        )
        assert result.confidence == 0.95
        client.close()


class TestBrain:
    """Tests for the high-level Brain API."""

    @respx.mock
    def test_believe_simple(self):
        respx.post(f"{BASE_URL}/believe").mock(
            return_value=httpx.Response(200, json={
                "id": "abc-123",
                "truth_state": "true",
                "confidence": 0.9,
                "conflict": False,
            })
        )
        brain = Brain(agent_id="test-agent", base_url=BASE_URL)
        result = brain.believe(
            claim="Paris is the capital of France",
            evidence=["wiki_paris"],
            confidence=0.9,
        )
        assert result.id == "abc-123"
        assert result.truth_state == "true"

        # Verify the request payload
        req = respx.calls.last.request
        import json
        body = json.loads(req.content)
        assert body["claim"] == "Paris is the capital of France"
        assert body["source_agent"] == "test-agent"
        assert len(body["evidence"]) == 1
        assert body["evidence"][0]["source_ref"] == "wiki_paris"
        brain.close()

    @respx.mock
    def test_ask(self):
        respx.get(f"{BASE_URL}/search").mock(
            return_value=httpx.Response(200, json={
                "results": [
                    {
                        "belief_id": "b-1",
                        "claim": "Paris: Paris is the capital of France.",
                        "truth_state": "true",
                        "confidence": 0.9,
                        "similarity": 0.88,
                        "rank_score": 0.89,
                    },
                    {
                        "belief_id": "b-2",
                        "claim": "France: France is in Europe.",
                        "truth_state": "true",
                        "confidence": 0.85,
                        "similarity": 0.72,
                        "rank_score": 0.78,
                    },
                ]
            })
        )
        brain = Brain(agent_id="test-agent", base_url=BASE_URL)
        result = brain.ask(question="What is the capital of France?")
        assert len(result.retrieved_beliefs) == 2
        assert "Paris" in result.retrieved_beliefs[0].claim
        assert result.query_id  # should be a UUID string
        brain.close()

    @respx.mock
    def test_feedback_noop(self):
        brain = Brain(agent_id="test-agent", base_url=BASE_URL)
        # feedback is a no-op — should not raise
        brain.feedback("some-query-id", outcome="COMPLETED")
        brain.close()

    @respx.mock
    def test_context_manager(self):
        respx.get(f"{BASE_URL}/health").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        with Brain(agent_id="test", base_url=BASE_URL) as brain:
            result = brain._client.health()
            assert result["status"] == "ok"
