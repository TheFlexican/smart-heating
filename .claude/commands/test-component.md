---
description: Generate comprehensive tests for a Home Assistant component (pytest, Vitest, or Playwright)
---

Use the ha-test-generator agent to create tests for the specified component. Generate:
- pytest unit tests with proper fixtures from conftest.py
- Proper mocking (AsyncMock for async, MagicMock for sync)
- Coverage for happy path and error cases
- 80%+ coverage target (pytest.ini requirement)
- Vitest tests for React/TypeScript components
- Playwright E2E tests for user workflows
- Following Arrange/Act/Assert structure

Place tests in appropriate tests/unit/ or frontend test directories following naming conventions.
