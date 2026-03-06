"""Tests for the MnemeBrain Python SDK client."""

import httpx
import respx

from mnemebrain import Brain, EvidenceInput, MnemeBrainClient

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
            return_value=httpx.Response(
                200,
                json={
                    "id": "abc-123",
                    "truth_state": "true",
                    "confidence": 0.85,
                    "conflict": False,
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.believe(
            claim="user is vegetarian",
            evidence=[
                EvidenceInput(
                    source_ref="msg_12",
                    content="They said no meat please",
                    polarity="supports",
                    weight=0.8,
                    reliability=0.9,
                )
            ],
        )
        assert result.id == "abc-123"
        assert result.truth_state == "true"
        assert result.confidence == 0.85
        assert result.conflict is False
        client.close()

    @respx.mock
    def test_search(self):
        respx.get(f"{BASE_URL}/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "belief_id": "b-1",
                            "claim": "user is vegetarian",
                            "truth_state": "true",
                            "confidence": 0.85,
                            "similarity": 0.92,
                            "rank_score": 0.88,
                        }
                    ]
                },
            )
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
            return_value=httpx.Response(
                200,
                json={
                    "claim": "user is vegetarian",
                    "truth_state": "true",
                    "confidence": 0.85,
                    "supporting": [
                        {
                            "id": "e-1",
                            "source_ref": "msg_12",
                            "content": "no meat",
                            "polarity": "supports",
                            "weight": 0.8,
                            "reliability": 0.9,
                        }
                    ],
                    "attacking": [],
                    "expired": [],
                },
            )
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
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "b-1",
                        "truth_state": "neither",
                        "confidence": 0.0,
                        "conflict": False,
                    }
                ],
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        results = client.retract("e-1")
        assert len(results) == 1
        assert results[0].truth_state == "neither"
        client.close()

    @respx.mock
    def test_revise(self):
        respx.post(f"{BASE_URL}/revise").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "b-1",
                    "truth_state": "true",
                    "confidence": 0.95,
                    "conflict": False,
                },
            )
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


class TestListBeliefs:
    """Tests for list_beliefs endpoint."""

    @respx.mock
    def test_list_beliefs(self):
        respx.get(f"{BASE_URL}/beliefs").mock(
            return_value=httpx.Response(
                200,
                json={
                    "beliefs": [
                        {
                            "id": "b-1",
                            "claim": "user is vegetarian",
                            "belief_type": "preference",
                            "truth_state": "true",
                            "confidence": 0.92,
                            "tag_count": 2,
                            "evidence_count": 3,
                            "created_at": "2026-01-15T10:00:00+00:00",
                            "last_revised": "2026-01-18T14:30:00+00:00",
                        }
                    ],
                    "total": 1,
                    "offset": 0,
                    "limit": 50,
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.list_beliefs(truth_state="true", belief_type="preference", tag="food")
        assert result.total == 1
        assert len(result.beliefs) == 1
        assert result.beliefs[0].claim == "user is vegetarian"
        assert result.beliefs[0].belief_type == "preference"
        assert result.beliefs[0].tag_count == 2
        client.close()

    @respx.mock
    def test_list_beliefs_no_filters(self):
        respx.get(f"{BASE_URL}/beliefs").mock(
            return_value=httpx.Response(
                200,
                json={"beliefs": [], "total": 0, "offset": 0, "limit": 50},
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.list_beliefs()
        assert result.total == 0
        assert result.beliefs == []
        client.close()


class TestWorkingMemoryFrame:
    """Tests for Phase 2 WorkingMemoryFrame endpoints."""

    SNAPSHOT = {
        "belief_id": "b-1",
        "claim": "auth uses JWT",
        "truth_state": "true",
        "confidence": 0.92,
        "belief_type": "fact",
        "evidence_count": 3,
        "conflict": False,
    }

    @respx.mock
    def test_frame_open(self):
        respx.post(f"{BASE_URL}/frame/open").mock(
            return_value=httpx.Response(
                200,
                json={
                    "frame_id": "f-123",
                    "beliefs_loaded": 1,
                    "conflicts": 0,
                    "snapshots": [self.SNAPSHOT],
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.frame_open(
            query="should we refactor auth?",
            preload_claims=["auth uses JWT"],
            ttl_seconds=600,
            source_agent="planner",
        )
        assert result.frame_id == "f-123"
        assert result.beliefs_loaded == 1
        assert result.conflicts == 0
        assert len(result.snapshots) == 1
        assert result.snapshots[0].claim == "auth uses JWT"
        client.close()

    @respx.mock
    def test_frame_add(self):
        respx.post(f"{BASE_URL}/frame/f-123/add").mock(
            return_value=httpx.Response(200, json=self.SNAPSHOT)
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.frame_add("f-123", "auth uses JWT")
        assert result.belief_id == "b-1"
        assert result.confidence == 0.92
        client.close()

    @respx.mock
    def test_frame_scratchpad(self):
        respx.post(f"{BASE_URL}/frame/f-123/scratchpad").mock(return_value=httpx.Response(204))
        client = MnemeBrainClient(base_url=BASE_URL)
        client.frame_scratchpad("f-123", "step_1", "JWT is well established")
        client.close()

    @respx.mock
    def test_frame_context(self):
        respx.get(f"{BASE_URL}/frame/f-123/context").mock(
            return_value=httpx.Response(
                200,
                json={
                    "query": "should we refactor auth?",
                    "beliefs": [self.SNAPSHOT],
                    "scratchpad": {"step_1": "JWT is well established"},
                    "conflicts": [],
                    "step_count": 1,
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.frame_context("f-123")
        assert result.query == "should we refactor auth?"
        assert len(result.beliefs) == 1
        assert result.scratchpad["step_1"] == "JWT is well established"
        assert result.step_count == 1
        assert result.conflicts == []
        client.close()

    @respx.mock
    def test_frame_commit(self):
        respx.post(f"{BASE_URL}/frame/f-123/commit").mock(
            return_value=httpx.Response(
                200,
                json={
                    "frame_id": "f-123",
                    "beliefs_created": 1,
                    "beliefs_revised": 0,
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.frame_commit(
            "f-123",
            new_beliefs=[{"claim": "new fact", "evidence": [], "belief_type": "fact"}],
        )
        assert result.frame_id == "f-123"
        assert result.beliefs_created == 1
        assert result.beliefs_revised == 0
        client.close()

    @respx.mock
    def test_frame_close(self):
        respx.delete(f"{BASE_URL}/frame/f-123").mock(return_value=httpx.Response(204))
        client = MnemeBrainClient(base_url=BASE_URL)
        client.frame_close("f-123")
        client.close()


class TestMnemeBrainClientContextManager:
    """Test MnemeBrainClient as context manager."""

    @respx.mock
    def test_context_manager(self):
        respx.get(f"{BASE_URL}/health").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        with MnemeBrainClient(base_url=BASE_URL) as client:
            result = client.health()
            assert result == {"status": "ok"}


class TestBrain:
    """Tests for the high-level Brain API."""

    @respx.mock
    def test_believe_simple(self):
        respx.post(f"{BASE_URL}/believe").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "abc-123",
                    "truth_state": "true",
                    "confidence": 0.9,
                    "conflict": False,
                },
            )
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
    def test_believe_without_evidence(self):
        respx.post(f"{BASE_URL}/believe").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "abc-456",
                    "truth_state": "true",
                    "confidence": 0.8,
                    "conflict": False,
                },
            )
        )
        brain = Brain(agent_id="test-agent", base_url=BASE_URL)
        result = brain.believe(claim="sky is blue")
        assert result.id == "abc-456"

        # Verify auto evidence was used
        import json

        body = json.loads(respx.calls.last.request.content)
        assert len(body["evidence"]) == 1
        assert body["evidence"][0]["source_ref"] == "auto"
        assert body["belief_type"] == "inference"
        brain.close()

    @respx.mock
    def test_ask(self):
        respx.get(f"{BASE_URL}/search").mock(
            return_value=httpx.Response(
                200,
                json={
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
                },
            )
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
