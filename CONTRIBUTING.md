# Contributing to MnemeBrain Python SDK

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Getting Started

```bash
# Clone the repository
git clone git@github.com:mnemebrain/mnemebrain-sdk.git
cd mnemebrain-sdk

# Install dependencies (including dev extras)
uv sync --extra dev

# Run all tests
uv run pytest tests/ -v

# Run tests with coverage (must be 100%)
uv run pytest tests/ -v --cov=mnemebrain --cov-fail-under=100
```

## Project Structure

```
src/mnemebrain/
├── __init__.py        # Public API re-exports
├── models.py          # Data classes (BeliefResult, EvidenceInput, etc.)
└── client.py          # MnemeBrainClient (low-level) + Brain (high-level)

tests/
├── test_models.py     # Model unit tests
└── test_client.py     # Client + Brain tests (mocked HTTP)

examples/
└── proof_the_claim/   # 7B vs 70B experiment scripts
```

## How to Contribute

### Reporting Bugs

Open an issue using the **Bug Report** template. Include:
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

### Suggesting Features

Open an issue using the **Feature Request** template. Describe:
- The problem you're solving
- Your proposed approach
- Alternatives you considered

### Submitting Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Write tests for your changes (**100% coverage required**)
4. Ensure all tests pass: `uv run pytest tests/ -v --cov=mnemebrain --cov-fail-under=100`
5. Follow the code style (we use ruff for linting)
6. Commit with conventional commits: `feat(scope): description`
7. Push and open a Pull Request

### Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Usage |
|--------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `chore` | Maintenance tasks |

Example: `feat(client): add async client support`

### Code Guidelines

- All public functions must have docstrings
- New features must include tests (100% coverage enforced in CI)
- No `# type: ignore` or `# noqa` without justification
- Use dataclasses for models, not Pydantic (keep the SDK lightweight)
- HTTP errors should raise `httpx.HTTPStatusError` — don't swallow them

## Questions?

Open an issue with the **Question** template, or start a discussion.
