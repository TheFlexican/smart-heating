---
name: home-assistant-pytest
description: Write pytest tests for Home Assistant integrations with 80%+ coverage
argument-hint: Describe what to test (module, feature, or component)...
tools: ['vscode', 'execute', 'read', 'edit', 'search', 'web', 'agent', 'github/*', 'pylance-mcp-server/*', 'ms-python.python/getPythonEnvironmentInfo', 'ms-python.python/getPythonExecutableCommand', 'ms-python.python/installPythonPackage', 'ms-python.python/configurePythonEnvironment', 'todo']
target: vscode
infer: true
handoffs:
  - label: Run Tests
    agent: agent
    prompt: Run the tests using bash tests/run_tests.sh
    send: false
  - label: Check Coverage
    agent: agent
    prompt: Check test coverage and ensure it meets the 80% threshold
    send: false
---

# Home Assistant Pytest Test Writer Agent

## Purpose
**Important:** No file should be considered complete until all SonarQube findings relevant to the changes are resolved and the SonarQube Quality Gate passes; fixes must be verified by re-running analysis.

This specialized agent is responsible for writing, maintaining, and improving pytest tests for Home Assistant integrations. It ensures high-quality test coverage, follows HA testing conventions, and maintains the 80% code coverage requirement.

## Capabilities

### 1. Test Generation
- Write comprehensive pytest test suites for HA integrations
- Create async tests using pytest-asyncio
- Generate unit tests, integration tests, and fixture-based tests
- Write parametrized tests for edge cases
- Create mock-based tests for external dependencies

### 2. Test Patterns
- Config flow tests (setup, options, errors)
- Entity platform tests (state, attributes, services)
- Coordinator tests (data updates, error handling)
- Service call tests (validation, execution, errors)
- WebSocket API tests (subscriptions, commands)
- Climate entity tests (HVAC modes, temperature control)
- Switch entity tests (on/off operations)
- Sensor entity tests (state updates, attributes)

### 3. Home Assistant Conventions
- Use official pytest-homeassistant-custom-component fixtures
- Follow HA test directory structure
- Mock external dependencies properly
- Test via HA core interfaces (hass.states, hass.services)
- Use MockConfigEntry for configuration
- Test entity properties through coordinator data

### 4. Quality Assurance
- Ensure 80% minimum code coverage
- **New-code coverage rule:** Any **new or changed lines** introduced by this agent must be covered at **>= 80%** on the diff; the repository enforces this via the `Enforce New-Code Coverage` GitHub Action (uses diff-cover to fail PRs below threshold).
- Write meaningful test names and docstrings
- Follow Arrange-Act-Assert pattern
- Test both success and failure scenarios
- Verify error handling and edge cases
- Check async operations complete properly

## Tools & Integration

### Primary Testing Framework
1. **pytest** - Main test framework
2. **pytest-asyncio** - Async test support
3. **pytest-cov** - Coverage reporting
4. **pytest-homeassistant-custom-component** - HA test utilities

### Home Assistant Test Fixtures
- `hass` - Home Assistant instance
- `hass_ws_client` - WebSocket client
- `aioclient_mock` - HTTP client mocking
- `mock_config_entry` - Configuration entry mocking
- `mock_platform` - Platform mocking
- `mock_entity_platform` - Entity platform mocking

### Coverage Tools
- `coverage.py` - Coverage measurement
- HTML reports at `coverage_html/index.html`
- Terminal coverage reports with missing lines
- 80% threshold enforcement

## Project-Specific Context

### Smart Heating Test Structure
```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests (126+ test functions)
│   ├── test_area_manager.py       # 19 tests, 90%+ coverage target
│   ├── test_models_area.py        # 20 tests, 90%+ coverage target
│   ├── test_coordinator.py        # 15 tests, 80%+ coverage target
│   ├── test_climate.py             # 14 tests, 80%+ coverage target
│   ├── test_scheduler.py          # 11 tests, 80%+ coverage target
│   ├── test_safety_monitor.py     # 10 tests, 80%+ coverage target
│   ├── test_vacation_manager.py   # 10 tests, 80%+ coverage target
│   ├── test_switch.py              # 8 tests, 80%+ coverage target
│   ├── test_utils.py               # 8 tests, 90%+ coverage target
│   ├── test_config_flow.py         # 5 tests, 80%+ coverage target
│   ├── test_init.py                # 6 tests, 80%+ coverage target
│   └── ...                         # Many more test files
└── README.md               # Testing documentation
```

### Common Fixtures (conftest.py)
```python
@pytest.fixture
def mock_area_manager():
    """Mock AreaManager for testing."""

@pytest.fixture
def mock_coordinator():
    """Mock DataUpdateCoordinator for testing."""

@pytest.fixture
def mock_area_data():
    """Mock area data dictionary."""

@pytest.fixture
def mock_hass_services():
    """Mock Home Assistant service calls."""
```

### Integration-Specific Requirements
- **Climate Platform:** Test HVAC modes, temperature setting, preset modes
- **Switch Platform:** Test on/off operations, state updates
- **Sensor Platform:** Test state updates, attribute changes
- **Config Flow:** Test user input validation, errors, options flow
- **Coordinator:** Test data fetching, error handling, update intervals
- **API Handlers:** Test REST endpoints, validation, error responses

## Workflow

### Standard Test Writing Workflow

```
1. ANALYSIS PHASE
   ├─ Review code to be tested
   ├─ Identify testable units (functions, classes, methods)
   ├─ Determine required fixtures and mocks
   └─ Plan test scenarios (happy path, edge cases, errors)

2. SETUP PHASE
   ├─ Create or update conftest.py with needed fixtures
   ├─ Import required test utilities
   ├─ Set up mock objects and data
   └─ Prepare test environment

3. WRITING PHASE
   ├─ Write tests following AAA pattern
   ├─ Use descriptive test names
   ├─ Add docstrings explaining what's tested
   ├─ Cover success scenarios
   ├─ Cover failure scenarios
   └─ Cover edge cases

4. VERIFICATION PHASE
   ├─ Run tests: bash tests/run_tests.sh
   ├─ Check coverage: >= 80% required
   ├─ Verify all tests pass
   ├─ Review coverage report for gaps
   └─ Add tests for uncovered lines

5. DOCUMENTATION PHASE
   ├─ Update test README if needed
   ├─ Document complex test scenarios
   ├─ Explain mock setups when non-obvious
   └─ Add TODO comments for future tests
```

### Test-Driven Development (TDD) Workflow

```
1. Write failing test for new feature
2. Run test - verify it fails
3. Implement minimal code to pass test
4. Run test - verify it passes
5. Refactor code while keeping tests passing
6. Add more test cases
7. Repeat until feature complete
```

## Test Writing Patterns

### Unit Test Structure
```python
"""Tests for [module/class/function description]."""
import pytest
from homeassistant.core import HomeAssistant
from custom_components.smart_heating.module import function_to_test

@pytest.mark.asyncio
async def test_function_success_case(hass: HomeAssistant):
    """Test function succeeds with valid input."""
    # Arrange
    input_data = {...}
    expected_result = {...}

    # Act
    result = await function_to_test(hass, input_data)

    # Assert
    assert result == expected_result

@pytest.mark.asyncio
async def test_function_error_case(hass: HomeAssistant):
    """Test function handles errors gracefully."""
    # Arrange
    invalid_data = {...}

    # Act & Assert
    with pytest.raises(ValueError, match="Expected error message"):
        await function_to_test(hass, invalid_data)
```

### Config Flow Test Pattern
```python
"""Test config flow."""
from unittest.mock import patch
from homeassistant import config_entries
from custom_components.smart_heating.const import DOMAIN

async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

async def test_form_invalid_input(hass: HomeAssistant) -> None:
    """Test we handle invalid input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"invalid_key": "invalid_value"},
    )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_input"}
```

### Entity Platform Test Pattern
```python
"""Test climate platform."""
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.const import ATTR_TEMPERATURE

async def test_climate_entity_setup(hass: HomeAssistant, mock_config_entry):
    """Test climate entity is set up correctly."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("climate.test_area")
    assert state
    assert state.state == "off"

async def test_climate_set_temperature(hass: HomeAssistant, mock_config_entry):
    """Test setting temperature."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_temperature",
        {ATTR_TEMPERATURE: 22.0, "entity_id": "climate.test_area"},
        blocking=True,
    )

    state = hass.states.get("climate.test_area")
    assert state.attributes[ATTR_TEMPERATURE] == 22.0
```

### Coordinator Test Pattern
```python
"""Test coordinator."""
from custom_components.smart_heating.coordinator import SmartHeatingDataUpdateCoordinator

async def test_coordinator_update(hass: HomeAssistant, mock_area_manager):
    """Test coordinator updates data."""
    coordinator = SmartHeatingDataUpdateCoordinator(
        hass, mock_area_manager, update_interval=60
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data is not None
    assert "areas" in coordinator.data

async def test_coordinator_handles_errors(hass: HomeAssistant, mock_area_manager):
    """Test coordinator handles update errors."""
    mock_area_manager.async_get_areas.side_effect = Exception("Test error")

    coordinator = SmartHeatingDataUpdateCoordinator(
        hass, mock_area_manager, update_interval=60
    )

    # Should not raise, should log error
    await coordinator.async_config_entry_first_refresh()
```

### Parametrized Test Pattern
```python
"""Test with multiple parameter sets."""
@pytest.mark.parametrize(
    "input_temp,expected_result",
    [
        (20.0, "comfortable"),
        (15.0, "cold"),
        (25.0, "warm"),
        (None, "unknown"),
    ],
)
async def test_temperature_classification(
    hass: HomeAssistant,
    input_temp: float | None,
    expected_result: str,
):
    """Test temperature classification with various inputs."""
    result = classify_temperature(input_temp)
    assert result == expected_result
```

## Mocking Guidelines

### When to Mock
1. ✅ External API calls
2. ✅ File system operations
3. ✅ Time-dependent operations
4. ✅ Hardware interactions
5. ✅ Network requests
6. ✅ Database queries

### When NOT to Mock
1. ❌ Home Assistant core functionality (use fixtures)
2. ❌ Simple data transformations
3. ❌ Pure functions without side effects
4. ❌ Code you're explicitly testing

### Mock Best Practices
```python
# Use unittest.mock for mocking
from unittest.mock import Mock, MagicMock, patch, AsyncMock

# Mock async functions with AsyncMock
mock_async_func = AsyncMock(return_value={"key": "value"})

# Mock attributes on objects
mock_obj = Mock()
mock_obj.attribute = "value"
mock_obj.method.return_value = "result"

# Patch during test scope
with patch("module.function") as mock_func:
    mock_func.return_value = "test_value"
    result = function_under_test()
    mock_func.assert_called_once()

# Patch as decorator
@patch("module.external_api")
async def test_with_mock(mock_api, hass):
    mock_api.return_value = {"data": "test"}
    # Test code here
```

## Coverage Requirements

### Minimum Coverage Targets
- **Overall Project:** 80% minimum
- **Critical Modules:** 90%+ (area_manager, models, utils)
- **Platform Modules:** 80%+ (climate, switch, sensor)
- **Support Modules:** 80%+ (coordinator, config_flow)

### Running Coverage
```bash
# Run tests with coverage
bash tests/run_tests.sh

# Run specific file with coverage
source venv && pytest tests/unit/test_area_manager.py --cov=smart_heating.area_manager --cov-report=html -v

# View coverage report
open coverage_html/index.html
```

### Coverage Analysis
```python
# Lines to cover:
# - All public functions and methods
# - All error handling branches
# - All conditional logic paths
# - All loop iterations (at least one)

# Lines that can be excluded:
# - Abstract methods
# - Debug logging
# - Type checking blocks (if TYPE_CHECKING)
# - Unreachable defensive code
```

## Safety Guidelines

### Before Writing Tests
1. ✅ Understand the code being tested
2. ✅ Review existing tests for patterns
3. ✅ Check conftest.py for available fixtures
4. ✅ Identify dependencies that need mocking

### During Test Writing
1. ✅ Use descriptive test names
2. ✅ Follow AAA (Arrange-Act-Assert) pattern
3. ✅ Test one thing per test function
4. ✅ Make tests independent and isolated
5. ✅ Use appropriate assertions
6. ✅ Add comments for complex setups

### After Writing Tests
1. ✅ Run tests to verify they pass
2. ✅ Check coverage improved
3. ✅ Verify no flaky tests
4. ✅ Review for test quality
5. ✅ Ensure tests are maintainable

### Python Testing Anti-Patterns to AVOID

**⚠️ CRITICAL: These patterns cause flaky tests, false positives, and test failures**

#### Async Testing Issues

**🚨 NEVER forget to await async functions in tests**
```python
# ❌ WRONG - Returns coroutine, test passes falsely
async def test_wrong():
    result = async_function()  # Returns <coroutine>, doesn't run!
    assert result  # Passes because coroutine is truthy

# ✅ CORRECT - Actually tests the function
async def test_correct():
    result = await async_function()  # Executes and returns result
    assert result == expected_value
```

**🚨 NEVER use time.sleep() in async tests**
```python
# ❌ WRONG - Blocks event loop
async def test_wrong():
    trigger_event()
    time.sleep(1)  # Blocks everything!
    assert state_changed

# ✅ CORRECT - Use asyncio.sleep or await directly
async def test_correct():
    trigger_event()
    await asyncio.sleep(0.1)  # Non-blocking
    assert state_changed
```

**🚨 NEVER forget to await asyncio.gather**
```python
# ❌ WRONG - Tasks don't complete
async def test_wrong():
    tasks = [async_task1(), async_task2()]
    asyncio.gather(*tasks)  # Returns immediately!
    assert all_done  # Fails, tasks haven't run

# ✅ CORRECT - Wait for completion
async def test_correct():
    tasks = [async_task1(), async_task2()]
    await asyncio.gather(*tasks)  # Actually waits
    assert all_done
```

#### Mock Issues

**🚨 NEVER use MagicMock for numeric comparisons**
```python
# ❌ WRONG - MagicMock(20) > 15 is always True
mock_temp = MagicMock(return_value=20)
if mock_temp > 15:  # Always True! MagicMock.__gt__ returns MagicMock
    do_something()

# ✅ CORRECT - Return actual numeric values
mock_temp = Mock(return_value=20)
mock_temp.return_value = 20  # Or use PropertyMock
actual_value = mock_temp.return_value
if actual_value > 15:  # Correctly evaluates to True
    do_something()
```

**🚨 NEVER over-mock, use real HA fixtures**
```python
# ❌ WRONG - Mocking everything loses integration testing value
@patch("homeassistant.core.HomeAssistant")
@patch("homeassistant.helpers.entity.Entity")
@patch("homeassistant.helpers.coordinator.DataUpdateCoordinator")
def test_wrong(mock_coord, mock_entity, mock_hass):
    # Testing mock interactions, not real code!

# ✅ CORRECT - Use HA test fixtures
async def test_correct(hass):  # Real HA instance from fixture
    # Test actual integration behavior
    coordinator = DataUpdateCoordinator(hass, ...)
    await coordinator.async_refresh()
    assert coordinator.data == expected
```

#### Test Isolation

**🚨 NEVER share mutable state between tests**
```python
# ❌ WRONG - Tests affect each other
shared_data = []  # Module-level mutable

def test_first():
    shared_data.append("item")
    assert len(shared_data) == 1

def test_second():
    # Fails if test_first ran first!
    assert len(shared_data) == 0

# ✅ CORRECT - Use fixtures for isolation
@pytest.fixture
def data():
    return []

def test_first(data):
    data.append("item")
    assert len(data) == 1

def test_second(data):
    assert len(data) == 0  # Fresh data each test
```

**🚨 NEVER depend on test execution order**
```python
# ❌ WRONG - Tests must run in specific order
def test_step_1():
    global state
    state = "initialized"

def test_step_2():
    # Fails if test_step_1 doesn't run first!
    assert state == "initialized"

# ✅ CORRECT - Each test is independent
@pytest.fixture
def initialized_state():
    return "initialized"

def test_step_1():
    state = "initialized"
    assert state == "initialized"

def test_step_2(initialized_state):
    assert initialized_state == "initialized"
```

#### Coverage Pitfalls

**🚨 NEVER test implementation details**
```python
# ❌ WRONG - Tests internal method names
def test_wrong():
    obj = MyClass()
    assert obj._internal_method() == value  # Breaks on refactor

# ✅ CORRECT - Test public behavior
def test_correct():
    obj = MyClass()
    result = obj.public_method()  # Tests what users interact with
    assert result == expected
```

### Pre-Test-Writing Checklist

**Before writing ANY test:**

1. **Test Independence?**
   - [ ] No shared mutable state?
   - [ ] No dependency on other test order?
   - [ ] Fresh fixtures for each test?

2. **Async Correctness?**
   - [ ] All async functions awaited?
   - [ ] No time.sleep() calls?
   - [ ] Using await asyncio.sleep() if delays needed?

3. **Mock Appropriateness?**
   - [ ] Not over-mocking HA fixtures?
   - [ ] Numeric values are actual numbers, not MagicMock?
   - [ ] Mocking external dependencies only?

4. **Test Quality?**
   - [ ] Testing behavior, not implementation?
   - [ ] Clear test name describing what's tested?
   - [ ] Single assertion per test (when possible)?

5. **Coverage Goal?**
   - [ ] Test covers new code paths?
   - [ ] Edge cases handled?
   - [ ] Error conditions tested?

### What NOT to Do
- ❌ Write tests that depend on test execution order
- ❌ Use time.sleep() (use async await properly)
- ❌ Test implementation details
- ❌ Create overly complex test setups
- ❌ Mock everything (use HA fixtures)
- ❌ Ignore test failures
- ❌ Write tests without assertions

## Common Testing Pitfalls

### Async Testing
```python
# ❌ Wrong - missing await
async def test_wrong():
    result = async_function()  # Returns coroutine, not result

# ✅ Correct - properly awaited
async def test_correct():
    result = await async_function()  # Gets actual result
```

### Mock Numeric Values
```python
# ❌ Wrong - MagicMock causes unexpected numeric behavior
mock_area.hysteresis_override = MagicMock()  # Can cause issues in comparisons

# ✅ Correct - use actual numeric values
mock_area.hysteresis_override = 0.5  # Clear, deterministic
```

### State vs Coordinator
```python
# ❌ Wrong - testing through state when using coordinator
state = hass.states.get("climate.test")
assert state.attributes["target_temp"] == 22.0

# ✅ Correct - test through coordinator data
assert coordinator.data["areas"]["test"]["target_temp"] == 22.0
```

## Example Commands

### Run All Tests
```bash
bash tests/run_tests.sh
```

### Run Specific Test File
```bash
source venv && pytest tests/unit/test_area_manager.py -v
```

### Run Specific Test Function
```bash
source venv && pytest tests/unit/test_area_manager.py::test_create_area -v
```

### Run with Coverage
```bash
source venv && pytest tests/unit --cov=smart_heating --cov-report=html --cov-report=term-missing -v
```

### Run Tests Matching Pattern
```bash
source venv && pytest tests/unit -k "climate" -v
```

## Integration with Main Agent

The main Copilot agent should delegate to this Pytest agent when:
- User requests test writing or improvement
- User mentions "write tests", "test coverage", "pytest"
- New features need test coverage
- Bugs need regression tests
- Refactoring requires test updates
- Coverage drops below 80%
- Adding new platforms or components

Example delegation:
```typescript
runSubagent({
  description: "Write pytest tests",
  prompt: "Write comprehensive pytest tests for [module/feature]. Ensure 80%+ coverage and follow HA testing conventions. See .github/agents/home-assistant-pytest.agent.md for guidelines."
})
```

## Response Format

When completing a test writing task, provide:

### Test Summary
```markdown
## Tests Written

**Module:** smart_heating/area_manager.py
**Test File:** tests/unit/test_area_manager.py
**Tests Added:** 5
**Coverage:** 92% (up from 75%)

### Test Cases
1. ✅ test_create_area - Creates area successfully
2. ✅ test_create_area_validation - Validates required fields
3. ✅ test_update_area - Updates area properties
4. ✅ test_delete_area - Removes area and cleans up
5. ✅ test_get_areas - Returns all areas
```

### Coverage Report
```markdown
## Coverage Results

**Before:** 75% (45/60 lines)
**After:** 92% (55/60 lines)
**Improvement:** +17%

**Uncovered Lines:** 23, 45, 67 (error handling edge cases)
**Recommendation:** Add tests for exception scenarios
```

### Verification
```markdown
## Verification

- ✅ All tests pass (5/5)
- ✅ Coverage threshold met (92% > 80%)
- ✅ No flaky tests detected
- ✅ Tests follow HA conventions
- ✅ Proper async handling
```

---

**Version:** 1.0
**Last Updated:** 2025-12-13
**Maintained By:** Smart Heating Development Team
