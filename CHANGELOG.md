# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0a1] - 2026-03-06

### Added

- `MnemeBrainClient` — low-level HTTP client wrapping all MnemeBrain REST API endpoints
  - `health()`, `believe()`, `explain()`, `search()`, `retract()`, `revise()`
  - Context manager support (`with MnemeBrainClient(...) as client:`)
- `Brain` — high-level experiment-friendly API
  - `believe(claim, evidence, confidence)` — simplified belief storage
  - `ask(question)` — semantic search returning ranked beliefs
  - `feedback(query_id, outcome)` — query feedback (future use)
  - Context manager support
- Data models: `BeliefResult`, `EvidenceInput`, `ExplanationResult`, `SearchResult`, `AskResult`, `RetrievedBelief`
- Enums: `TruthState`, `BeliefType`, `Polarity`
- Full test suite with 100% coverage (mocked HTTP via respx)
- Proof-the-claim experiment scripts (3-condition HotpotQA evaluation)
- CI workflows: tests, lint, CodeQL, dependency review, pylint
- Release workflow: tag-triggered build + publish to PyPI and GitHub Releases
