# Getting Started

## Prerequisites

- Python 3.10+
- A running [MnemeBrain backend](https://github.com/mnemebrain/mnemebrain-lite)

## Installation

```bash
pip install mnemebrain
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add mnemebrain
```

## Start the Backend

```bash
# Clone and start the MnemeBrain backend
git clone https://github.com/mnemebrain/mnemebrain-lite.git
cd mnemebrain-lite
uv sync --extra all
uv run python -m mnemebrain_core
# Server running at http://localhost:8000
```

## Your First Belief

```python
from mnemebrain import Brain

# Connect to the backend
brain = Brain(agent_id="my-agent", base_url="http://localhost:8000")

# Store a belief
result = brain.believe(
    claim="The user prefers dark mode",
    evidence=["settings_page_visit"],
    confidence=0.85,
    belief_type="preference",
)
print(f"Stored: {result.truth_state}, confidence={result.confidence:.2f}")

# Query it back
answer = brain.ask("What UI theme does the user prefer?")
for belief in answer.retrieved_beliefs:
    print(f"  {belief.claim} (similarity={belief.similarity:.2f})")
```

## Two API Levels

### Brain (high-level)

Designed for experiments and quick agent integration. Simplified `believe()` / `ask()` / `feedback()` interface.

### MnemeBrainClient (low-level)

Full control over the REST API. Direct access to `believe()`, `explain()`, `search()`, `retract()`, `revise()`, `list_beliefs()`.

### WorkingMemoryFrame (multi-step reasoning)

For complex reasoning tasks that span multiple steps, open a frame, load beliefs, use a scratchpad for intermediate results, then commit or discard:

```python
from mnemebrain import MnemeBrainClient

with MnemeBrainClient() as client:
    frame = client.frame_open(query="should we refactor auth?")
    client.frame_add(frame.frame_id, "auth uses JWT")
    client.frame_scratchpad(frame.frame_id, "step_1", "JWT is well established")
    ctx = client.frame_context(frame.frame_id)
    client.frame_commit(frame.frame_id, new_beliefs=[...])
```

See the [API Reference](api-reference.md) for details.
