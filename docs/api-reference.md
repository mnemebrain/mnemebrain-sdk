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

### `client.list_beliefs(truth_state, belief_type, tag, min_confidence, max_confidence, limit, offset)`

List beliefs with optional filters.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `truth_state` | `str \| None` | `None` | Filter by truth state |
| `belief_type` | `str \| None` | `None` | Filter by belief type |
| `tag` | `str \| None` | `None` | Filter by tag |
| `min_confidence` | `float` | `0.0` | Minimum confidence |
| `max_confidence` | `float` | `1.0` | Maximum confidence |
| `limit` | `int` | `50` | Page size |
| `offset` | `int` | `0` | Pagination offset |

**Returns:** `BeliefListResponse`

---

## WorkingMemoryFrame (Phase 2)

Ephemeral context buffer for multi-step reasoning. Open a frame, load beliefs, use a scratchpad, then commit or discard.

### `client.frame_open(query, preload_claims, ttl_seconds, source_agent)`

Open a working memory frame.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | The reasoning query |
| `preload_claims` | `list[str] \| None` | `None` | Claims to preload into the frame |
| `ttl_seconds` | `int` | `300` | Frame time-to-live |
| `source_agent` | `str` | `""` | Source agent identifier |

**Returns:** `FrameOpenResult`

### `client.frame_add(frame_id, claim)`

Add a belief to an active frame by claim text.

**Returns:** `BeliefSnapshot`

### `client.frame_scratchpad(frame_id, key, value)`

Write a key/value pair to the frame's scratchpad.

**Returns:** `None` (204 No Content)

### `client.frame_context(frame_id)`

Get the full active context of a frame — beliefs, scratchpad, conflicts, step count.

**Returns:** `FrameContextResult`

### `client.frame_commit(frame_id, new_beliefs, revisions)`

Commit frame results back to the belief graph.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frame_id` | `str` | required | Frame identifier |
| `new_beliefs` | `list[dict] \| None` | `None` | New beliefs to create |
| `revisions` | `list[dict] \| None` | `None` | Existing beliefs to revise |

**Returns:** `FrameCommitResult`

### `client.frame_close(frame_id)`

Close a frame without committing. Discards all frame state.

**Returns:** `None` (204 No Content)

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

### BeliefListItem

```python
@dataclass
class BeliefListItem:
    id: str
    claim: str
    belief_type: str
    truth_state: str
    confidence: float
    tag_count: int
    evidence_count: int
    created_at: str
    last_revised: str
```

### BeliefListResponse

```python
@dataclass
class BeliefListResponse:
    beliefs: list[BeliefListItem]
    total: int
    offset: int
    limit: int
```

### BeliefSnapshot

```python
@dataclass
class BeliefSnapshot:
    belief_id: str
    claim: str
    truth_state: str
    confidence: float
    belief_type: str
    evidence_count: int
    conflict: bool
```

### FrameOpenResult

```python
@dataclass
class FrameOpenResult:
    frame_id: str
    beliefs_loaded: int
    conflicts: int
    snapshots: list[BeliefSnapshot]
```

### FrameContextResult

```python
@dataclass
class FrameContextResult:
    query: str
    beliefs: list[BeliefSnapshot]
    scratchpad: dict
    conflicts: list[BeliefSnapshot]
    step_count: int
```

### FrameCommitResult

```python
@dataclass
class FrameCommitResult:
    frame_id: str
    beliefs_created: int
    beliefs_revised: int
```
