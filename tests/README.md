# Tests

## Structure

- tests/unit/
  - Unit tests only (no external services, no network, no disk IO).
- tests/integration/
  - Integration tests that exercise external systems or cross-module flows.
- tests/fixtures/
  - Static test data (json, txt, images, etc.).
- tests/conftest.py
  - Shared pytest fixtures (code-based), kept small and domain-focused.

## Naming

- Test files: test_*.py
- Test functions: test_*
- Fixtures: use domain terms; prefer local fixtures in the test module unless shared.

## Running

- Run all: pytest
- Unit only: pytest tests/unit
- Integration only: pytest tests/integration
