# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0a1] - 2026-03-06

### Added

- `MnemeBrainClient` — low-level HTTP client wrapping all MnemeBrain REST API endpoints
  - Phase 1: `health()`, `believe()`, `explain()`, `search()`, `retract()`, `revise()`
  - Phase 1: `list_beliefs()` — paginated belief listing with filters (truth_state, belief_type, tag, confidence range)
  - Phase 2: WorkingMemoryFrame endpoints for multi-step reasoning
    - `frame_open()` — open a frame with query and preloaded claims
    - `frame_add()` — add a belief to an active frame
    - `frame_scratchpad()` — write key/value to frame scratchpad
    - `frame_context()` — get full active context (beliefs, scratchpad, conflicts)
    - `frame_commit()` — commit frame results back to belief graph
    - `frame_close()` — close frame without committing
  - Context manager support (`with MnemeBrainClient(...) as client:`)
- `Brain` — high-level experiment-friendly API
  - `believe(claim, evidence, confidence)` — simplified belief storage
  - `ask(question)` — semantic search returning ranked beliefs
  - `feedback(query_id, outcome)` — query feedback (future use)
  - Context manager support
- Data models: `BeliefResult`, `EvidenceInput`, `ExplanationResult`, `SearchResult`, `AskResult`, `RetrievedBelief`, `BeliefListItem`, `BeliefListResponse`, `BeliefSnapshot`, `FrameOpenResult`, `FrameContextResult`, `FrameCommitResult`
- Enums: `TruthState`, `BeliefType`, `Polarity`
- Full test suite with 100% coverage (34 tests, mocked HTTP via respx)
- Proof-the-claim experiment scripts (3-condition HotpotQA evaluation)
- CI workflows: tests, lint, CodeQL, dependency review, pylint
- Release workflow: tag-triggered build + publish to PyPI and GitHub Releases
