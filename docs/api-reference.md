# API Reference

## Brain

High-level experiment-friendly API.

### `Brain(agent_id, base_url, timeout)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent_id` | `str` | `"default"` | Agent identifier for provenance tracking |
| `base_url` | `str` | `"http://localhost:8000"` | MnemeBrain backend URL |
| `timeout` | `float` | `30.0` | HTTP request timeout in seconds |

### `brain.believe(claim, evidence, confidence, belief_type)`

Store a belief with evidence.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `claim` | `str` | required | The belief claim text |
| `evidence` | `list[str] \| None` | `None` | Evidence source references. If None, uses `["auto"]` |
| `confidence` | `float` | `0.8` | Evidence weight and reliability (0.0-1.0) |
| `belief_type` | `str` | `"inference"` | One of: `"fact"`, `"preference"`, `"inference"`, `"prediction"` |

**Returns:** `BeliefResult`

### `brain.ask(question, query_type, agent_id, limit)`

Semantic search returning ranked beliefs.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `question` | `str` | required | The question to search for |
| `query_type` | `str` | `"FACTUAL"` | Query type hint (future use) |
| `agent_id` | `str \| None` | `None` | Override agent_id for this query |
| `limit` | `int` | `5` | Maximum beliefs to retrieve |

**Returns:** `AskResult`

### `brain.feedback(query_id, outcome)`

Record feedback for a query. Currently a no-op reserved for future use.

---

## MnemeBrainClient

Low-level HTTP client wrapping the MnemeBrain REST API.

### `MnemeBrainClient(base_url, timeout)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | `str` | `"http://localhost:8000"` | MnemeBrain backend URL |
| `timeout` | `float` | `30.0` | HTTP request timeout in seconds |

### `client.health()`

Check backend health. Returns `{"status": "ok"}`.

### `client.believe(claim, evidence, belief_type, tags, source_agent)`

Store a belief with detailed evidence items.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `claim` | `str` | required | The belief claim text |
| `evidence` | `list[EvidenceInput]` | required | Evidence items |
| `belief_type` | `str` | `"inference"` | Belief type |
| `tags` | `list[str] \| None` | `None` | Optional tags |
| `source_agent` | `str` | `""` | Source agent identifier |

**Returns:** `BeliefResult`

### `client.explain(claim)`

Get full justification chain for a belief.

**Returns:** `ExplanationResult | None`

### `client.search(query, limit, alpha, conflict_policy)`

Semantic search with ranking.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | Search query |
| `limit` | `int` | `10` | Max results |
| `alpha` | `float` | `0.7` | Ranking alpha (similarity vs confidence weight) |
| `conflict_policy` | `str` | `"surface"` | One of: `"surface"`, `"conservative"`, `"optimistic"` |

**Returns:** `SearchResponse`

### `client.retract(evidence_id)`

Invalidate evidence and recompute affected beliefs.

**Returns:** `list[BeliefResult]`

### `client.revise(belief_id, evidence)`

Add new evidence to an existing belief and recompute.

**Returns:** `BeliefResult`

---

## Models

### EvidenceInput

```python
@dataclass
class EvidenceInput:
    source_ref: str           # Evidence source reference
    content: str              # Evidence content text
    polarity: str = "supports"  # "supports" or "attacks"
    weight: float = 0.7       # Evidence weight (0.0-1.0)
    reliability: float = 0.8  # Source reliability (0.0-1.0)
    scope: str | None = None  # Optional scope qualifier
```

### BeliefResult

```python
@dataclass
class BeliefResult:
    id: str              # Belief UUID
    truth_state: str     # "true", "false", "both", "neither"
    confidence: float    # Computed confidence (0.0-1.0)
    conflict: bool       # True if truth_state is "both"
```

### ExplanationResult

```python
@dataclass
class ExplanationResult:
    claim: str
    truth_state: str
    confidence: float
    supporting: list[EvidenceDetail]
    attacking: list[EvidenceDetail]
    expired: list[EvidenceDetail]
```

### AskResult

```python
@dataclass
class AskResult:
    query_id: str
    retrieved_beliefs: list[RetrievedBelief]
```

### RetrievedBelief

```python
@dataclass
class RetrievedBelief:
    claim: str
    confidence: float
    similarity: float
```
