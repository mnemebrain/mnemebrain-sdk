# MnemeBrain Python SDK

Python client for the MnemeBrain belief memory API.

## Install

```bash
pip install mnemebrain
```

## Quick Start

```python
from mnemebrain import Brain

brain = Brain(agent_id="my-agent", base_url="http://localhost:8000")

# Store a belief
brain.believe(
    claim="user is vegetarian",
    evidence=["msg_12"],
    confidence=0.9,
)

# Query beliefs
result = brain.ask("Is the user vegetarian?")
for belief in result.retrieved_beliefs:
    print(belief.claim, belief.confidence)
```

## Low-Level Client

```python
from mnemebrain import MnemeBrainClient, EvidenceInput

client = MnemeBrainClient(base_url="http://localhost:8000")

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
print(result.truth_state)  # "true"
```
