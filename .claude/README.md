# Smart Heating Claude Code Agents

Custom AI agents specialized in Home Assistant integration development for the **smart_heating** project.

## Quick Start

**Just describe what you need!** The `ha-developer` orchestrator handles everything:

```bash
# Fix a bug
claude "Fix the temperature debouncing issue in coordinator.py"

# Add a feature
claude "Add support for humidity sensors"

# Update tests
claude "Update E2E tests for the vacation mode dialog"

# Review code
claude "Review my changes in climate.py before I commit"

# Get architecture guidance
claude "Should I use a coordinator for this new feature?"
```

## Architecture: Single Entry Point

The agent system uses an **orchestrator pattern** with one primary agent that routes to specialists:

```
Your Request
    ↓
[ha-developer] ← PRIMARY ENTRY POINT
    ↓ (intelligently routes to)
    ├─→ [ha-code-reviewer] - Code review specialist
    ├─→ [ha-test-generator] - Test generation specialist
    ├─→ [ha-scaffolder] - Component scaffolding specialist
    └─→ [ha-expert] - HA knowledge consultant
```

## Available Agents

### ha-developer (Orchestrator) ⭐ PRIMARY

**Use this for everything!**

- **Analyzes** your request (bug fix, feature, test, review, etc.)
- **Researches** HA documentation when needed
- **Delegates** to specialist agents
- **Coordinates** multi-step workflows
- **Ensures** quality standards (80%+ test coverage, HA compliance)

**Tools:** Read, Write, Edit, Grep, Glob, Bash, Task, WebSearch, WebFetch

**Examples:**
- "Fix the coordinator state listener bug"
- "Add binary sensor support for window sensors"
- "Generate tests for area_manager.py"
- "Review coordinator.py for HA compliance"
- "Refactor the API handlers to reduce code duplication"

### ha-code-reviewer (Specialist)

Expert code reviewer focusing on:
- Home Assistant integration patterns
- Async/await correctness
- Entity and coordinator patterns
- Type hints and docstrings
- Code quality (ruff/ESLint)
- Test coverage adequacy

**When called:** Automatically by ha-developer after code changes, or directly for reviews

### ha-test-generator (Specialist)

Test generation expert creating:
- pytest unit tests with proper fixtures
- Vitest tests for React components
- Playwright E2E tests for workflows
- 80%+ coverage following conftest.py patterns

**When called:** Automatically by ha-developer for test needs, or directly

### ha-scaffolder (Specialist)

Component scaffolding specialist generating:
- Coordinators with state listeners
- Entities (climate, sensor, etc.)
- API handlers with error handling
- React components with TypeScript
- Service handlers with schemas

**When called:** Automatically by ha-developer for new components, or directly

### ha-expert (Specialist)

Home Assistant architecture consultant providing:
- Pattern explanations
- Design decision guidance
- Best practices recommendations
- Smart_heating pattern references

**When called:** Automatically by ha-developer for architecture questions, or directly

## Common Use Cases

### Bug Fixes

```bash
claude "Fix the bug where temperature sensors don't update after coordinator refresh"
```

**What happens:**
1. ha-developer reads the relevant code
2. Identifies the issue
3. Consults ha-expert for pattern guidance if needed
4. Fixes the code
5. Calls ha-code-reviewer to verify
6. Calls ha-test-generator to add test case
7. Runs tests to verify fix

### New Features

```bash
claude "Add support for window sensors to trigger heating shutoff"
```

**What happens:**
1. ha-developer consults ha-expert for architecture
2. Researches similar HA integrations (WebSearch)
3. Calls ha-scaffolder for boilerplate
4. Implements the feature
5. Calls ha-test-generator for tests
6. Calls ha-code-reviewer for final check
7. Verifies 80%+ coverage

### Test Updates

```bash
claude "Update E2E tests to cover the new vacation mode settings dialog"
```

**What happens:**
1. ha-developer reads the dialog component code
2. Calls ha-test-generator with Playwright focus
3. Generates E2E tests
4. Runs tests to verify they work

### Code Reviews

```bash
claude "Review my changes before I commit"
```

**What happens:**
1. ha-developer identifies changed files (git diff)
2. Calls ha-code-reviewer for each file
3. Summarizes findings (Critical/Warning/Suggestion)
4. Offers to fix issues if found

### Architecture Questions

```bash
claude "Should I use a coordinator or direct polling for this new sensor?"
```

**What happens:**
1. ha-developer forwards to ha-expert
2. ha-expert provides detailed explanation with pros/cons
3. References smart_heating examples
4. Recommends best approach

## Slash Commands

Shortcuts for common operations:

```bash
# Primary command
claude /ha-dev "your request here"

# Specific operations
claude /review-component climate.py
claude /test-component area_manager.py
claude /scaffold-component sensor platform
```

**Note:** You rarely need these - just describing what you want to ha-developer works great!

## How Delegation Works

The ha-developer orchestrator uses the **Task tool** to invoke specialist agents:

```
You: "Fix the coordinator bug and add tests"

ha-developer:
  1. Reads coordinator.py
  2. Identifies the bug
  3. [Task tool → ha-expert] "Explain coordinator debouncing pattern"
  4. Fixes the bug based on guidance
  5. [Task tool → ha-code-reviewer] "Review fixed code"
  6. [Task tool → ha-test-generator] "Create test for bug scenario"
  7. Runs tests
  8. Reports completion
```

You don't need to manage this - ha-developer handles it automatically!

## Direct Specialist Invocation

You can also call specialists directly (but usually not needed):

```bash
# Direct code review
claude "Use ha-code-reviewer to review coordinator.py for async patterns"

# Direct test generation
claude "Use ha-test-generator to create Playwright tests for settings page"

# Direct scaffolding
claude "Use ha-scaffolder to create a new binary_sensor platform"

# Direct expert consultation
claude "Ask ha-expert: when should I use UpdateFailed vs ConfigEntryAuthFailed?"
```

## Quality Standards

All code produced by the agents meets these standards:

- **HA Compliance:** Follows Home Assistant integration patterns
- **Test Coverage:** 80%+ (pytest.ini requirement)
- **Code Style:** Passes ruff (Python) and ESLint (TypeScript)
- **Type Hints:** All function signatures typed
- **Docstrings:** Google style with Args/Returns
- **Async Patterns:** No blocking I/O
- **Smart_heating Conventions:** Follows project patterns exactly

## Project-Specific Patterns

The agents encode these smart_heating patterns:

### Coordinator Pattern
- 30-second update interval
- State listeners with debouncing (2s)
- Startup grace period (10s)
- Proper async_setup and async_shutdown
- Reference: `smart_heating/coordinator.py`

### Entity Pattern
- CoordinatorEntity before platform entity
- unique_id: `f"{entry.entry_id}_{platform}_{id}"`
- Properties from coordinator.data
- Type hints: `float | None` (Python 3.9+)
- Reference: `smart_heating/climate.py`

### Test Pattern
- Fixtures from conftest.py
- AsyncMock for async, MagicMock for sync
- Arrange/Act/Assert structure
- 80%+ coverage requirement
- Reference: `tests/conftest.py`

### API Pattern
- Async handlers with try/except
- JSON responses with status codes
- Manager pattern for business logic
- Reference: `smart_heating/api_handlers/`

### Frontend Pattern
- TypeScript with strict mode
- Material-UI components
- useTranslation for i18n
- Reference: `smart_heating/frontend/src/components/`

## Troubleshooting

### Agent not responding as expected?

1. **Be specific:** Instead of "fix it", say "fix the debouncing bug in coordinator.py"
2. **Provide context:** Mention file names, error messages, or behavior
3. **State your goal:** "I want to add humidity sensors" vs just "sensors"

### Wrong specialist called?

The orchestrator usually routes correctly, but you can be explicit:
```bash
claude "Have ha-code-reviewer check climate.py for async issues"
```

### Need to see agent descriptions?

```bash
claude /agents  # List all agents
```

Or read the agent files in `.claude/agents/`

### Agent making wrong assumptions?

Provide more detail in your request:
```bash
# Vague
claude "Add sensors"

# Better
claude "Add binary_sensor platform for window/door sensors that trigger heating shutoff"
```

## Tips for Best Results

1. **Start with ha-developer:** Let it route to specialists
2. **Be descriptive:** More context = better results
3. **Mention files:** "in coordinator.py" helps target the work
4. **State requirements:** "with 80%+ test coverage" ensures quality
5. **Ask for explanations:** "Explain why..." gets detailed reasoning
6. **Request reviews:** "Review before committing" catches issues early

## Example Workflows

### Full Feature Development

```bash
# Step 1: Add the feature
claude "Add support for occupancy sensors that pause heating when room is empty for 15 minutes"

# The agent will:
# - Consult ha-expert for architecture
# - Scaffold necessary components
# - Implement the feature
# - Generate comprehensive tests
# - Review the implementation
# - Verify tests pass

# Step 2: Review before committing
claude "Review all my changes for HA compliance"

# Step 3: Create PR (if you want)
# (ha-developer doesn't create PRs, but can prepare commit)
```

### Bug Investigation and Fix

```bash
# Single request handles everything
claude "The coordinator isn't detecting manual temperature changes correctly. Debug and fix this with proper tests."

# Agent will:
# - Read coordinator code
# - Identify the issue
# - Consult expert for pattern
# - Fix the bug
# - Add test case
# - Verify fix works
```

### Test-Driven Development

```bash
# 1. Generate tests first
claude "Create tests for a new vacation mode manager that handles start/end dates and frost protection"

# 2. Review test structure
claude "Review the generated tests"

# 3. Implement to pass tests
claude "Implement the vacation mode manager to pass the tests we created"
```

## Advanced Usage

### Custom Agent Combinations

```bash
# Scaffold + Test + Review in one request
claude "Scaffold a binary_sensor platform, generate tests, and review everything"
```

### Research Then Implement

```bash
# Agent will research latest HA patterns
claude "Research current HA best practices for climate entities, then update our climate.py to match"
```

### Batch Operations

```bash
# Review multiple files
claude "Review coordinator.py, climate.py, and area_manager.py for any issues"
```

## Learn More

- **Agent Development:** See `.claude/AGENT_GUIDE.md`
- **Workflow Examples:** See `.claude/EXAMPLES.md`
- **Claude Code Docs:** https://code.claude.com/docs

## Need Help?

```bash
# Ask the agents!
claude "How do I use the ha-developer agent effectively?"
claude "What patterns does smart_heating follow for coordinators?"
claude "Show me an example of proper entity implementation"
```

The agents are here to help you build better Home Assistant integrations!
