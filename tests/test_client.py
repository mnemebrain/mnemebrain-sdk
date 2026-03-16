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
            query_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            top_k=20,
            ttl_seconds=600,
        )
        assert result.frame_id == "f-123"
        assert result.beliefs_loaded == 1
        assert result.conflicts == 0
        assert len(result.snapshots) == 1
        assert result.snapshots[0].claim == "auth uses JWT"

        # Verify request payload
        import json

        body = json.loads(respx.calls.last.request.content)
        assert body["query_id"] == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert body["top_k"] == 20
        assert body["ttl_seconds"] == 600
        assert "goal_id" not in body
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
                    "active_query": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "active_goal": None,
                    "beliefs": [self.SNAPSHOT],
                    "scratchpad": {"step_1": "JWT is well established"},
                    "conflicts": [],
                    "step_count": 1,
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.frame_context("f-123")
        assert result.active_query == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert result.active_goal is None
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
    def test_feedback_not_implemented(self):
        brain = Brain(agent_id="test-agent", base_url=BASE_URL)
        import pytest

        with pytest.raises(NotImplementedError):
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


class TestPhase5Client:
    """Tests for Phase 5 endpoints on MnemeBrainClient."""

    @respx.mock
    def test_reset(self):
        respx.post(f"{BASE_URL}/reset").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        client.reset()  # should not raise
        client.close()

    @respx.mock
    def test_set_time_offset(self):
        respx.post(f"{BASE_URL}/debug/set_time_offset").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        client.set_time_offset(days=30)
        req = respx.calls.last.request
        import json

        body = json.loads(req.content)
        assert body["days"] == 30
        client.close()

    @respx.mock
    def test_consolidate(self):
        respx.post(f"{BASE_URL}/consolidate").mock(
            return_value=httpx.Response(
                200,
                json={
                    "semantic_beliefs_created": 2,
                    "episodics_pruned": 5,
                    "clusters_found": 3,
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.consolidate()
        assert result.semantic_beliefs_created == 2
        assert result.episodics_pruned == 5
        assert result.clusters_found == 3
        client.close()

    @respx.mock
    def test_get_memory_tier(self):
        respx.get(f"{BASE_URL}/memory_tier/b-1%231").mock(
            return_value=httpx.Response(
                200,
                json={
                    "belief_id": "b-1#1",
                    "memory_tier": "semantic",
                    "consolidated_from_count": 4,
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.get_memory_tier("b-1#1")
        assert result.memory_tier == "semantic"
        assert result.consolidated_from_count == 4
        client.close()

    @respx.mock
    def test_query_multihop(self):
        respx.post(f"{BASE_URL}/query_multihop").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "belief_id": "b-1",
                            "claim": "Paris is capital of France",
                            "confidence": 0.95,
                            "truth_state": "true",
                        },
                        {
                            "belief_id": "b-2",
                            "claim": "France is in Europe",
                            "confidence": 0.88,
                            "truth_state": "true",
                        },
                    ]
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.query_multihop("What is the capital of France?")
        assert len(result.results) == 2
        assert result.results[0].claim == "Paris is capital of France"
        assert result.results[1].belief_id == "b-2"
        client.close()

    @respx.mock
    def test_query_multihop_empty(self):
        respx.post(f"{BASE_URL}/query_multihop").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.query_multihop("nonexistent topic")
        assert result.results == []
        client.close()

    @respx.mock
    def test_retract_with_results_wrapper(self):
        """Test that retract handles the {results: [...]} response format."""
        respx.post(f"{BASE_URL}/retract").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": "b-1",
                            "truth_state": "neither",
                            "confidence": 0.0,
                            "conflict": False,
                        }
                    ],
                    "affected_beliefs": 1,
                    "truth_states_changed": 1,
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        results = client.retract("e-1")
        assert len(results) == 1
        assert results[0].truth_state == "neither"
        client.close()


class TestBenchmarkEndpoints:
    """Tests for benchmark sandbox/attack endpoints on MnemeBrainClient."""

    @respx.mock
    def test_benchmark_sandbox_fork(self):
        respx.post(f"{BASE_URL}/benchmark/sandbox/fork").mock(
            return_value=httpx.Response(
                200,
                json={
                    "sandbox_id": "sb-1",
                    "resolved_truth_state": "",
                    "canonical_unchanged": True,
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.benchmark_sandbox_fork("test-scenario")
        assert result.sandbox_id == "sb-1"
        assert result.canonical_unchanged is True
        client.close()

    @respx.mock
    def test_benchmark_sandbox_assume(self):
        respx.post(f"{BASE_URL}/benchmark/sandbox/sb-1/assume").mock(
            return_value=httpx.Response(
                200,
                json={
                    "sandbox_id": "sb-1",
                    "resolved_truth_state": "false",
                    "canonical_unchanged": True,
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.benchmark_sandbox_assume("sb-1", "b-1", "false")
        assert result.resolved_truth_state == "false"
        client.close()

    @respx.mock
    def test_benchmark_sandbox_resolve(self):
        respx.get(f"{BASE_URL}/benchmark/sandbox/sb-1/resolve/b-1%231").mock(
            return_value=httpx.Response(
                200,
                json={
                    "sandbox_id": "sb-1",
                    "resolved_truth_state": "true",
                    "canonical_unchanged": True,
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.benchmark_sandbox_resolve("sb-1", "b-1#1")
        assert result.resolved_truth_state == "true"
        client.close()

    @respx.mock
    def test_benchmark_sandbox_discard(self):
        respx.delete(f"{BASE_URL}/benchmark/sandbox/sb-1").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        client.benchmark_sandbox_discard("sb-1")  # should not raise
        client.close()

    @respx.mock
    def test_benchmark_attack(self):
        respx.post(f"{BASE_URL}/benchmark/attack").mock(
            return_value=httpx.Response(
                200,
                json={
                    "edge_id": "e-1",
                    "attacker_id": "b-1",
                    "target_id": "b-2",
                },
            )
        )
        client = MnemeBrainClient(base_url=BASE_URL)
        result = client.benchmark_attack("b-1", "b-2", "undermining", 0.5)
        assert result.edge_id == "e-1"
        assert result.attacker_id == "b-1"
        assert result.target_id == "b-2"
        client.close()
