# Agent Workflow Examples

Real-world examples of using the HA specialist agent system.

## Philosophy: Single Entry Point

**You rarely need to think about which agent to use.** Just describe what you need to ha-developer, and it routes to the right specialists automatically.

```bash
# ✅ Simple and effective
claude "Fix the coordinator bug and add tests"

# ❌ Overthinking it
claude "Use ha-code-reviewer to review coordinator.py, then use ha-test-generator to create tests, then..."
```

## Example 1: Bug Fix Workflow

### Scenario
The coordinator isn't properly handling device state changes when the device goes offline.

### Request
```bash
claude "Debug and fix the issue where coordinator crashes when a device goes offline"
```

### What Happens

**Step 1: Analysis**
```
ha-developer:
  Reading coordinator.py to understand state handling...

  Found the issue in _handle_state_change():
  - Line 270: Not checking if new_state is None before accessing attributes
  - This causes AttributeError when device goes offline
```

**Step 2: Consult Expert**
```
ha-developer:
  Consulting ha-expert for proper state change handling pattern...

ha-expert:
  Always check for None state:
  ```python
  if not new_state or new_state.state == "unavailable":
      return
  ```
```

**Step 3: Fix**
```
ha-developer:
  Implementing fix in coordinator.py:270...

  OLD:
    new_temp = new_state.attributes.get("temperature")

  NEW:
    if not new_state or new_state.state == "unavailable":
        _LOGGER.debug("Device %s unavailable, skipping", entity_id)
        return
    new_temp = new_state.attributes.get("temperature")
```

**Step 4: Code Review**
```
ha-developer:
  Calling ha-code-reviewer to verify the fix...

ha-code-reviewer:
  ✅ Fix looks good!
  - Proper None checking
  - Appropriate logging
  - Follows smart_heating patterns
```

**Step 5: Generate Tests**
```
ha-developer:
  Calling ha-test-generator to add test case...

ha-test-generator:
  Created test_coordinator_handles_unavailable_device() in tests/unit/test_coordinator.py

  Test verifies:
  - Coordinator doesn't crash on None state
  - Proper logging occurs
  - No coordinator refresh triggered
```

**Step 6: Verify**
```
ha-developer:
  Running tests...
  $ pytest tests/unit/test_coordinator.py::test_coordinator_handles_unavailable_device -v

  PASSED ✓

  All coordinator tests still passing ✓
```

### Result
Bug fixed, code reviewed, test added, all verified - in one request!

---

## Example 2: New Feature Implementation

### Scenario
Add support for humidity sensors that trigger ventilation when humidity >70%.

### Request
```bash
claude "Add support for humidity sensors. When humidity exceeds 70%, trigger ventilation mode. Include full tests."
```

### What Happens

**Step 1: Architecture Consultation**
```
ha-developer:
  This is a new feature. Consulting ha-expert for architecture...

ha-expert:
  Recommended approach:
  1. Add binary_sensor platform for humidity sensor entities
  2. Add humidity monitoring to coordinator
  3. Add ventilation_mode to Area model
  4. Add state listener for humidity changes
  5. Implement trigger logic in climate_controller
```

**Step 2: Research**
```
ha-developer:
  Researching HA humidity sensor examples...

  WebSearch: "Home Assistant humidity sensor binary_sensor custom integration"

  Found: Official HA binary_sensor with device_class="moisture"
```

**Step 3: Scaffold Components**
```
ha-developer:
  Calling ha-scaffolder for boilerplate...

ha-scaffolder:
  Generated:
  - smart_heating/binary_sensor.py (humidity sensor entity)
  - Extended Area model with ventilation_mode
  - Added humidity_threshold config
```

**Step 4: Implementation**
```
ha-developer:
  Implementing humidity monitoring logic...

  Files modified:
  - binary_sensor.py: HumiditySensor entity
  - models/area.py: Added ventilation_mode, humidity_threshold
  - coordinator.py: Added humidity state listeners
  - climate_controller.py: Ventilation trigger logic
  - const.py: Added HUMIDITY_THRESHOLD constant
```

**Step 5: Generate Tests**
```
ha-developer:
  Calling ha-test-generator for comprehensive tests...

ha-test-generator:
  Generated tests:
  - tests/unit/test_binary_sensor.py (humidity sensor tests)
  - tests/unit/test_humidity_monitoring.py (trigger logic tests)
  - Added fixtures to conftest.py

  Coverage: 87% (exceeds 80% requirement)
```

**Step 6: Code Review**
```
ha-developer:
  Calling ha-code-reviewer for final check...

ha-code-reviewer:
  Review Results:
  ✅ All async patterns correct
  ✅ Proper type hints
  ✅ Good error handling
  ✅ Follows smart_heating conventions

  Suggestion: Add docstring to _check_humidity_threshold()
```

**Step 7: Apply Suggestion**
```
ha-developer:
  Adding docstring...
  Done.
```

**Step 8: Verify**
```
ha-developer:
  Running full test suite...
  $ pytest tests/unit/ --cov=smart_heating

  342 tests passed
  Coverage: 83%

  All checks passed ✓
```

### Result
Complete feature implementation with 87% test coverage, all in one request!

---

## Example 3: Test Update Workflow

### Scenario
Need to add E2E tests for the new vacation mode settings dialog.

### Request
```bash
claude "Create comprehensive Playwright E2E tests for the vacation mode settings dialog"
```

### What Happens

**Step 1: Analysis**
```
ha-developer:
  Reading vacation mode dialog component...

  Found: frontend/src/components/VacationModeDialog.tsx

  Features to test:
  - Dialog open/close
  - Date picker interactions
  - Frost protection toggle
  - Temperature setting
  - Save/Cancel buttons
  - API integration
```

**Step 2: Generate E2E Tests**
```
ha-developer:
  Calling ha-test-generator with Playwright focus...

ha-test-generator:
  Created: tests/e2e/tests/vacation-mode.spec.ts

  Test suite includes:
  - test('opens vacation mode dialog')
  - test('sets vacation dates')
  - test('enables frost protection')
  - test('saves vacation settings')
  - test('cancels without saving')
  - test('validates date range')
  - test('calls API correctly')
```

**Step 3: Verify Tests**
```
ha-developer:
  Running E2E tests...
  $ cd tests/e2e && npx playwright test vacation-mode

  7 tests passed

  All scenarios covered ✓
```

### Result
Complete E2E test suite generated and verified!

---

## Example 4: Code Review Before Commit

### Scenario
Made changes to several files, want to review before committing.

### Request
```bash
claude "Review my changes before I commit"
```

### What Happens

**Step 1: Identify Changes**
```
ha-developer:
  Checking git status...
  $ git diff --name-only

  Modified files:
  - smart_heating/coordinator.py
  - smart_heating/climate.py
  - smart_heating/api_handlers/areas.py
```

**Step 2: Review Each File**
```
ha-developer:
  Calling ha-code-reviewer for each file...

ha-code-reviewer (coordinator.py):
  ✅ Changes look good
  - Improved debouncing logic
  - Proper error handling

ha-code-reviewer (climate.py):
  ⚠️ Warning found:
  - Line 145: Missing type hint on new method

  Suggested fix:
  ```python
  def get_effective_mode(self) -> str:
  ```

ha-code-reviewer (api_handlers/areas.py):
  ✅ Changes look good
  - API responses properly formatted
```

**Step 3: Fix Issues**
```
ha-developer:
  Applying suggested fix to climate.py:145...
  Done.

  Re-reviewing...

ha-code-reviewer:
  ✅ All issues resolved!
```

**Step 4: Summary**
```
ha-developer:
  Review Summary:
  - 3 files reviewed
  - 1 warning fixed
  - All code passes HA compliance
  - Ready to commit ✓
```

### Result
Code reviewed and issues fixed before commit!

---

## Example 5: Architecture Question

### Scenario
Planning a new feature, unsure of the best approach.

### Request
```bash
claude "I want to add support for external weather data to optimize heating. Should I use a coordinator or direct API calls?"
```

### What Happens

**Step 1: Forward to Expert**
```
ha-developer:
  This is an architecture question. Forwarding to ha-expert...

ha-expert:
  For external weather data integration:

  **Recommended: Use DataUpdateCoordinator**

  Pros:
  - Automatic polling (every 30 minutes for weather is typical)
  - Built-in error handling and retry
  - Multiple entities can share weather data
  - Follows HA best practices

  Cons:
  - Slightly more setup than direct calls

  **Alternative: Direct API calls**
  Only if you need real-time updates (webhook/push)

  **Smart_heating example:**
  The WeatherCoordinator in opentherm_logger.py uses this pattern.

  **Implementation:**
  1. Create WeatherCoordinator(DataUpdateCoordinator)
  2. Poll weather API every 30 minutes
  3. Store in coordinator.data
  4. Reference from climate entities
```

**Step 2: Offer Implementation**
```
ha-developer:
  Would you like me to implement the WeatherCoordinator following this pattern?
```

### Result
Clear architectural guidance with reasoning and examples!

---

## Example 6: Refactoring Workflow

### Scenario
API handlers have duplicate error handling code that should be centralized.

### Request
```bash
claude "Refactor API handlers to centralize error handling logic"
```

### What Happens

**Step 1: Analysis**
```
ha-developer:
  Reading API handlers to identify duplication...

  Found duplicate pattern in 8 files:
  ```python
  try:
      # Logic
  except Exception as e:
      _LOGGER.error("Error: %s", e, exc_info=True)
      return web.json_response({"error": str(e)}, status=400)
  ```
```

**Step 2: Consult Expert**
```
ha-developer:
  Asking ha-expert for error handling pattern...

ha-expert:
  Recommended approach: Decorator pattern

  ```python
  def handle_api_errors(handler):
      async def wrapper(*args, **kwargs):
          try:
              return await handler(*args, **kwargs)
          except Exception as e:
              _LOGGER.error("API error: %s", e, exc_info=True)
              return web.json_response({"error": str(e)}, status=400)
      return wrapper
  ```
```

**Step 3: Implement**
```
ha-developer:
  Creating utils/api_decorators.py with handle_api_errors decorator...

  Refactoring 8 handler files to use decorator...

  OLD:
    async def handle_get_areas(hass, manager):
        try:
            data = manager.get_all_areas()
            return web.json_response(...)
        except Exception as e:
            _LOGGER.error(...)
            return web.json_response(...)

  NEW:
    @handle_api_errors
    async def handle_get_areas(hass, manager):
        data = manager.get_all_areas()
        return web.json_response(...)
```

**Step 4: Review**
```
ha-developer:
  Calling ha-code-reviewer...

ha-code-reviewer:
  ✅ Refactoring looks excellent!
  - DRY principle applied
  - Decorator pattern appropriate
  - All handlers simplified
  - Consistent error handling
```

**Step 5: Update Tests**
```
ha-developer:
  Calling ha-test-generator to update tests...

ha-test-generator:
  Added tests for handle_api_errors decorator
  Updated existing API handler tests
  All tests passing ✓
```

### Result
Code refactored, reviewed, tested - cleaner and maintainable!

---

## Example 7: Multi-Step Complex Task

### Scenario
Add complete vacation mode feature with frost protection, date range, API, frontend, and tests.

### Request
```bash
claude "Implement complete vacation mode: backend model, API endpoints, frontend UI, E2E tests, everything"
```

### What Happens

**Step 1: Planning**
```
ha-developer:
  This is a complex multi-step task. Creating plan...

  Plan:
  1. Consult expert for architecture
  2. Extend Area model for vacation data
  3. Add API handlers (enable/disable/configure)
  4. Create React components (dialog, controls)
  5. Generate backend tests
  6. Generate frontend tests
  7. Generate E2E tests
  8. Review everything
```

**Step 2-8: Execution**
```
ha-developer executes the plan, delegating to specialists:
  - ha-expert for architecture
  - ha-scaffolder for boilerplate
  - ha-test-generator for all tests
  - ha-code-reviewer for final check
```

**Step 9: Summary**
```
ha-developer:
  Vacation Mode Feature Complete!

  Created/Modified:
  - models/area.py: Added vacation_mode fields
  - vacation_manager.py: New manager class
  - api_handlers/vacation.py: API endpoints
  - frontend/src/components/VacationModeDialog.tsx: UI
  - Tests: 15 pytest, 8 Vitest, 5 E2E

  Test Coverage: 89%
  All Reviews: Passed

  Next steps:
  1. Review the implementation
  2. Test manually in HA
  3. Create PR when ready
```

### Result
Complete feature implementation across backend, frontend, and tests!

---

## Tips for Complex Workflows

### 1. Let the Orchestrator Work

Don't micro-manage:
```bash
# ✅ Good - Let ha-developer orchestrate
claude "Add humidity sensor support with tests"

# ❌ Over-specified - Unnecessary
claude "First use ha-expert to ask about sensors, then use ha-scaffolder to create sensor.py, then use ha-test-generator for tests, then use ha-code-reviewer"
```

### 2. Provide Context

Help the agent understand:
```bash
# ✅ Good - Clear context
claude "Fix the coordinator debouncing bug that causes rapid API calls when temperature changes quickly"

# ❌ Vague
claude "Fix coordinator bug"
```

### 3. State Requirements

Be clear about what you need:
```bash
# ✅ Good - Clear requirements
claude "Add window sensor support with automatic heating shutoff after 5 minutes open, including E2E tests"

# ❌ Unclear
claude "Add window sensors"
```

### 4. Trust the Process

The orchestrator will:
- Analyze your request
- Research if needed
- Delegate appropriately
- Coordinate specialists
- Ensure quality

You don't need to manage the workflow!

### 5. Review Before Committing

Good practice:
```bash
# After implementation
claude "Review all my changes before I commit"
```

---

## Common Patterns

### Quick Bug Fix
```bash
claude "Fix [specific bug description]"
```

### New Feature
```bash
claude "Add support for [feature] with [requirements]"
```

### Test Generation
```bash
claude "Generate tests for [component]"
```

### Code Review
```bash
claude "Review [files] for HA compliance"
```

### Architecture Question
```bash
claude "Should I use [approach A] or [approach B] for [feature]?"
```

### Refactoring
```bash
claude "Refactor [component] to [improvement]"
```

---

## Remember

The agent system is designed to handle complexity for you. Just describe what you need in natural language, and ha-developer will:

1. ✅ Understand your request
2. ✅ Research best practices
3. ✅ Delegate to specialists
4. ✅ Coordinate the work
5. ✅ Ensure quality
6. ✅ Report results

**You focus on what to build. The agents handle how to build it!**
