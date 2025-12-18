---
description: Review a Home Assistant component for best practices and compliance with HA patterns
---

Use the ha-code-reviewer agent to review the specified component. Check for:
- Home Assistant integration patterns compliance
- Async/await correctness (no blocking I/O)
- Type hints and docstrings (Google style)
- Error handling and logging
- Test coverage adequacy
- Code quality (ruff/ESLint compliance)
- Coordinator and entity patterns
- Smart_heating conventions

Provide actionable feedback with specific file:line references and code examples.
