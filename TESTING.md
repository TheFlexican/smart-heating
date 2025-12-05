# Smart Heating v0.3.5 - Testing & Bug Fixes

## Summary

Successfully implemented comprehensive end-to-end testing infrastructure with Playwright and fixed critical bugs in boost mode and sensor handling that were discovered during the testing process.

## Changes Made

### 1. Bug Fixes (v0.3.5)

#### Backend Fixes
- **Climate Controller Crash**: Fixed "unhashable type: 'dict'" error when handling window/presence sensors
  - Root Cause: Sensors stored as dicts with `entity_id` field, but code tried to use them directly as strings
  - Solution: Extract `entity_id` from sensor dicts before using with `hass.states.get()`
  
- **Boost Mode Not Working**: Fixed boost mode not triggering heating
  - Root Cause: `check_boost_expiry()` being called with wrong number of arguments
  - Solution: Removed incorrect `current_time` parameter from call
  
- **Boost Mode Persistence**: Fixed boost mode state not being saved/loaded
  - Root Cause: `boost_mode_active` and `boost_end_time` not included in storage serialization
  - Solution: Added fields to `to_dict()` and `from_dict()` methods with ISO datetime parsing
  
- **v0.3.0 Data Flow**: Fixed missing fields in coordinator, API, and WebSocket
  - Root Cause: New v0.3.0 fields (preset modes, HVAC mode, sensors, boost) not propagated through all layers
  - Solution: Added all v0.3.0 fields to coordinator updates, API GET endpoints, and WebSocket responses

#### Frontend Improvements
- **Draggable Settings**: Replaced large list with 3-column grid of draggable cards
  - Uses react-beautiful-dnd for drag-and-drop
  - Responsive: 3 columns (desktop), 2 columns (tablet), 1 column (mobile)
  - Persists custom order in localStorage per area
  
- **Better UX**: Improved sensor configuration dialogs
  - Better error messages
  - Don't close dialog on errors
  - Enhanced entity filtering

- **History Retention**: Changed slider from 1-365 days to 1-30 days for cleaner UI

### 2. Testing Infrastructure (Playwright)

#### Test Suite Coverage
- **Basic Navigation**: Panel load, area list, detail view
- **Temperature Control**: Adjust temperature, enable/disable areas
- **Boost Mode**: Activate, cancel, verify heating state changes
- **Preset Modes**: Change between different preset modes
- **Sensor Management**: Add/remove presence and window sensors
- **Draggable Settings**: Verify drag handles, localStorage persistence
- **Schedule & History**: Navigation and display
- **Error Handling**: Backend errors, invalid input
- **Real-time Updates**: WebSocket temperature updates

#### Test Commands
```bash
cd tests/e2e
npm test                 # Run all tests headless
npm run test:headed      # Run with browser visible
npm run test:debug       # Step-through debugging
npm run test:ui          # Interactive UI mode
npm run report           # View test report
npm run codegen          # Generate new tests
```

#### Test Structure
```
tests/e2e/
├── playwright.config.ts          # Playwright configuration
├── tsconfig.json                 # TypeScript configuration
├── package.json                  # Dependencies and scripts
├── tests/
│   └── smart-heating.spec.ts     # Main test suite (17 tests)
└── README.md                     # Testing documentation
```

## Files Modified

### Backend
- `smart_heating/__init__.py` - Added full error tracebacks
- `smart_heating/climate_controller.py` - Fixed sensor handling and boost expiry
- `smart_heating/area_manager.py` - Added boost persistence
- `smart_heating/coordinator.py` - Added all v0.3.0 fields
- `smart_heating/api.py` - Added all v0.3.0 fields to GET endpoints
- `smart_heating/websocket.py` - Added all v0.3.0 fields to WebSocket
- `smart_heating/manifest.json` - Version bump to 0.3.5

### Frontend
- `smart_heating/frontend/src/pages/AreaDetail.tsx` - Integrated draggable settings
- `smart_heating/frontend/src/components/DraggableSettings.tsx` - NEW: Grid layout container
- `smart_heating/frontend/src/components/SettingsSection.tsx` - NEW: Collapsible card component
- `smart_heating/frontend/src/components/SensorConfigDialog.tsx` - Improved error handling

### Testing
- `tests/e2e/playwright.config.ts` - NEW: Playwright configuration
- `tests/e2e/tsconfig.json` - NEW: TypeScript config
- `tests/e2e/package.json` - NEW: Test dependencies and scripts
- `tests/e2e/tests/smart-heating.spec.ts` - NEW: Main test suite
- `tests/e2e/README.md` - NEW: Testing documentation
- `tests/e2e/.gitignore` - NEW: Ignore test artifacts

## Testing Approach

### Why Playwright?
- **End-to-End**: Tests the complete stack (frontend + backend + Home Assistant)
- **Real Browser**: Tests actual user interactions, not mocked
- **Visual Debugging**: Can see tests running, inspect elements
- **Backend Integration**: Can verify backend logs during tests
- **CI/CD Ready**: Headless mode for automation

### Test Philosophy
1. **Test User Flows**: Focus on what users actually do (activate boost, add sensors, etc.)
2. **Verify Backend State**: Check that UI actions trigger correct backend behavior
3. **Check Error Handling**: Ensure errors are shown to users appropriately
4. **Monitor Logs**: Watch for backend errors during test execution

### How to Use Tests for Debugging
1. **Run tests after changes**: `npm test`
2. **If test fails**:
   - Look at screenshot in `test-results/`
   - Check backend logs: `docker logs -f homeassistant-test`
   - Run in debug mode: `npm run test:debug`
3. **Fix the bug**
4. **Re-run tests**: `npm test`
5. **Add new test**: Cover the bug scenario to prevent regression

## Example: How Tests Would Have Caught Our Bugs

### Boost Mode Bug
The test `should activate boost mode` would have failed with:
```
Error: Timed out waiting for heating badge to appear
Expected: text=HEATING to be visible
Actual: text=IDLE was visible
```

This would have led us to:
1. Check backend logs → See "Error in climate control: Area.check_boost_expiry() takes 1 positional argument but 2 were given"
2. Fix the bug
3. Re-run test → Pass ✓

### Sensor Crash Bug
The test `should add presence sensor` would have crashed with:
```
Error: unhashable type: 'dict'
```

Backend logs would show the full traceback pointing to the exact line in `climate_controller.py`.

## Next Steps

### Running Tests
1. Make sure Home Assistant container is running
2. Navigate to test directory: `cd tests/e2e`
3. Run tests: `npm test`
4. View report: `npm run report`

### Adding New Tests
When adding new features:
1. Add test to `tests/smart-heating.spec.ts`
2. Follow existing patterns (use helper functions)
3. Always clean up after test (cancel boost, remove sensors, etc.)
4. Run test locally before committing

### CI/CD Integration (Future)
```yaml
# GitHub Actions example
- name: Run E2E Tests
  run: |
    cd tests/e2e
    npm ci
    npx playwright install --with-deps chromium
    npm test
```

## Lessons Learned

1. **Data Flow Matters**: A feature isn't complete until it flows through ALL layers (storage → model → coordinator → API → WebSocket → frontend)
2. **Test Early**: E2E tests catch integration bugs that unit tests miss
3. **Debug Logging**: Full tracebacks (`exc_info=True`) are essential for debugging
4. **Type Safety**: TypeScript caught many potential bugs in frontend
5. **User Testing**: Clicking through the UI revealed bugs that code review didn't

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Testing Best Practices](https://playwright.dev/docs/best-practices)
- [Test Results Location](tests/e2e/playwright-report/)
- [Test README](tests/e2e/README.md)

---

**Commits:**
- `2491203` - v0.3.5 - Fix boost mode, sensor handling, and add draggable settings UI
- `fef6b4d` - Add Playwright E2E test suite for Smart Heating

**Version:** 0.3.5  
**Date:** December 5, 2025  
**Status:** ✅ All changes committed and pushed
