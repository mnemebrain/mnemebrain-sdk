# MnemeBrain Python SDK

[![CI](https://github.com/mnemebrain/mnemebrain-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/mnemebrain/mnemebrain-sdk/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/mnemebrain.svg)](https://pypi.org/project/mnemebrain/)
[![Python](https://img.shields.io/pypi/pyversions/mnemebrain.svg)](https://pypi.org/project/mnemebrain/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/mnemebrain/mnemebrain-sdk)

Python client for [MnemeBrain](https://mnemebrain.ai) — biological belief memory for LLM agents.

Beliefs carry evidence, confidence, provenance, and revision logic. Unlike flat key-value memory, MnemeBrain can explain, retract, and revise what it knows.

## Install

```bash
pip install mnemebrain
```

> **Requires:** Python 3.10+ and a running [MnemeBrain backend](https://github.com/mnemebrain/mnemebrain-lite).

## Quick Start

### Brain (high-level API)

The `Brain` class provides a simple interface for experiments and agent integration:

```python
from mnemebrain import Brain

brain = Brain(agent_id="my-agent", base_url="http://localhost:8000")

# Store a belief with evidence
brain.believe(
    claim="user is vegetarian",
    evidence=["msg_12"],
    confidence=0.9,
)

# Query beliefs semantically
result = brain.ask("Is the user vegetarian?")
for belief in result.retrieved_beliefs:
    print(f"{belief.claim} (confidence={belief.confidence:.2f})")
```

### MnemeBrainClient (low-level API)

For full control over the REST API:

```python
from mnemebrain import MnemeBrainClient, EvidenceInput

with MnemeBrainClient(base_url="http://localhost:8000") as client:
    # Store a belief with detailed evidence
    result = client.believe(
        claim="user is vegetarian",
        evidence=[EvidenceInput(
            source_ref="msg_12",
            content="They said no meat please",
            polarity="supports",
            weight=0.8,
            reliability=0.9,
        )],
        belief_type="preference",
        tags=["dietary"],
    )
    print(result.truth_state)  # "true"
    print(result.confidence)   # 0.65

    # Explain a belief
    explanation = client.explain("user is vegetarian")
    if explanation:
        print(f"Supporting: {len(explanation.supporting)}")
        print(f"Attacking: {len(explanation.attacking)}")

    # Search beliefs
    results = client.search(query="dietary preferences", limit=5)
    for hit in results.results:
        print(f"{hit.claim} (sim={hit.similarity:.2f})")

    # List beliefs with filters
    page = client.list_beliefs(truth_state="true", belief_type="preference", limit=20)
    print(f"Total: {page.total}")

    # Revise with new evidence
    client.revise(
        belief_id=result.id,
        evidence=EvidenceInput(
            source_ref="msg_50",
            content="confirmed vegetarian",
            polarity="supports",
            weight=0.9,
            reliability=0.95,
        ),
    )

    # Retract evidence
    client.retract(evidence_id="<uuid>")
```

### WorkingMemoryFrame (multi-step reasoning)

Ephemeral context buffer for complex reasoning tasks:

```python
with MnemeBrainClient(base_url="http://localhost:8000") as client:
    # Open a frame with a reasoning query
    frame = client.frame_open(
        query="should we refactor auth?",
        preload_claims=["auth uses JWT"],
        ttl_seconds=600,
    )

    # Add more beliefs as reasoning progresses
    client.frame_add(frame.frame_id, "JWT tokens expire after 1 hour")

    # Use the scratchpad for intermediate reasoning
    client.frame_scratchpad(frame.frame_id, "step_1", "JWT is well established")

    # Get full context at any point
    ctx = client.frame_context(frame.frame_id)
    print(f"Beliefs: {len(ctx.beliefs)}, Steps: {ctx.step_count}")

    # Commit new beliefs back to the graph
    client.frame_commit(
        frame.frame_id,
        new_beliefs=[{"claim": "auth refactor not needed", "evidence": [], "belief_type": "inference"}],
    )

    # Or close without committing
    # client.frame_close(frame.frame_id)
```

## API Reference

### Brain

| Method | Description |
|--------|-------------|
| `believe(claim, evidence, confidence, belief_type)` | Store a belief with evidence references |
| `ask(question, query_type, limit)` | Semantic search returning ranked beliefs |
| `feedback(query_id, outcome)` | Record query feedback (future use) |

### MnemeBrainClient

| Method | Description |
|--------|-------------|
| `health()` | Check backend health |
| `believe(claim, evidence, belief_type, tags, source_agent)` | Store a belief with detailed evidence |
| `explain(claim)` | Get full justification chain for a belief |
| `search(query, limit, alpha, conflict_policy)` | Semantic search with ranking |
| `retract(evidence_id)` | Invalidate evidence and recompute beliefs |
| `revise(belief_id, evidence)` | Add new evidence to an existing belief |
| `list_beliefs(truth_state, belief_type, tag, ...)` | List beliefs with filters and pagination |
| `frame_open(query, preload_claims, ttl_seconds)` | Open a working memory frame |
| `frame_add(frame_id, claim)` | Add a belief to an active frame |
| `frame_scratchpad(frame_id, key, value)` | Write to frame scratchpad |
| `frame_context(frame_id)` | Get full frame context |
| `frame_commit(frame_id, new_beliefs, revisions)` | Commit frame to belief graph |
| `frame_close(frame_id)` | Close frame without committing |

### Models

| Model | Description |
|-------|-------------|
| `BeliefResult` | Result from believe/revise (id, truth_state, confidence, conflict) |
| `EvidenceInput` | Evidence to attach (source_ref, content, polarity, weight, reliability) |
| `ExplanationResult` | Full justification chain (supporting, attacking, expired evidence) |
| `SearchResult` | Search hit (belief_id, claim, similarity, rank_score) |
| `AskResult` | Brain.ask result (query_id, retrieved_beliefs) |
| `RetrievedBelief` | Simplified belief (claim, confidence, similarity) |
| `BeliefListItem` | Belief in list response (id, claim, type, confidence, timestamps) |
| `BeliefListResponse` | Paginated belief list (beliefs, total, offset, limit) |
| `BeliefSnapshot` | Belief snapshot in a frame (belief_id, claim, confidence, conflict) |
| `FrameOpenResult` | Frame open result (frame_id, beliefs_loaded, conflicts, snapshots) |
| `FrameContextResult` | Frame context (query, beliefs, scratchpad, conflicts, step_count) |
| `FrameCommitResult` | Frame commit result (frame_id, beliefs_created, beliefs_revised) |

### Enums

| Enum | Values |
|------|--------|
| `TruthState` | `TRUE`, `FALSE`, `BOTH` (contradiction), `NEITHER` (insufficient) |
| `BeliefType` | `FACT`, `PREFERENCE`, `INFERENCE`, `PREDICTION` |
| `Polarity` | `SUPPORTS`, `ATTACKS` |

Full documentation: [docs/api-reference.md](docs/api-reference.md)

## Proof the Claim: 7B + MnemeBrain vs 70B

The `examples/proof_the_claim/` directory contains a complete experiment demonstrating that a 7B model with MnemeBrain can outperform a 70B model on knowledge-intensive tasks.

```bash
# 1. Start the MnemeBrain backend
cd mnemebrain-lite && uv run python -m mnemebrain_core

# 2. Download data
pip install mnemebrain[experiment]
cd examples/proof_the_claim
python 1_download_data.py

# 3. Load knowledge into MnemeBrain
python 2_load_brain.py

# 4. Run the 3-condition evaluation
ollama pull mistral
ollama pull llama3.1:70b  # or set USE_GROQ=1 GROQ_API_KEY=...
python 3_evaluate.py
```

## Development

```bash
git clone git@github.com:mnemebrain/mnemebrain-sdk.git
cd mnemebrain-sdk
uv sync --extra dev
uv run pytest tests/ -v --cov=mnemebrain --cov-fail-under=100
uv run ruff check src/ tests/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

## License

MIT
