# Global Presets Feature - Manual Testing Guide

## Overview
This guide covers manual testing for the Global Preset Temperatures feature added in v0.4.3.

## Test Coverage

### 1. Global Preset Temperature Configuration

**Location:** Settings → Global Presets page

**Test Steps:**
1. Navigate to Smart Heating UI (http://localhost:8123/smart-heating)
2. Open menu → Click "Settings"
3. Verify you see "Global Preset Temperatures" section with 6 sliders:
   - Away
   - Eco
   - Comfort
   - Home
   - Sleep
   - Activity

**Expected Results:**
- ✅ All 6 preset modes are visible
- ✅ Each shows current temperature value (e.g., "19.2°C")
- ✅ Sliders allow adjustment in 0.1°C steps
- ✅ Changes are debounced (saved 500ms after last slider movement)
- ✅ Values persist after page refresh

**Test Procedure:**
1. Adjust "Home" preset to 20.5°C
2. Wait 1 second
3. Refresh page (Cmd+Shift+R to clear cache)
4. Verify "Home" preset still shows 20.5°C

---

### 2. Per-Area Preset Configuration

**Location:** Area Detail → Settings Tab → Preset Temperature Configuration

**Test Steps:**
1. Navigate to an area (e.g., "Woonkamer")
2. Click "Settings" tab
3. Find and expand "Preset Temperature Configuration" card

**Expected Results:**
- ✅ Section shows 6 toggle switches (one per preset mode)
- ✅ Each toggle labeled: "{Mode}: Use Global"
- ✅ Each shows current temperature:
  - If using global: "Using global setting: XX°C"
  - If using custom: "Using custom setting: XX°C"
- ✅ Info alert explains: "Global presets can be configured in Settings → Global Presets"

**Test Procedure - Toggle Global/Custom:**
1. Find "Home: Use Global" toggle
2. Note current state (ON = global, OFF = custom)
3. Click toggle to switch
4. Wait 1 second for API call
5. Verify:
   - Toggle visually updated
   - Text changed to reflect new state
   - Temperature value updated (global vs custom)
6. Toggle back to original state
7. Verify state restored correctly

**Test Procedure - Temperature Values:**
1. Set "Home" preset to use **global** (toggle ON)
2. Note displayed temperature (e.g., "Using global setting: 19.2°C")
3. Go to Settings → Global Presets
4. Change "Home" global preset to different value (e.g., 21.0°C)
5. Return to area → Settings tab
6. Verify "Home" preset now shows new global value: "21.0°C"

---

### 3. Manual Override Toggle Integration

**Location:** Area Card (Main Overview)

**Test Steps:**
1. Navigate to Smart Heating main page
2. Find an area card (e.g., "Woonkamer")
3. Locate "Using Preset Mode" / "Manual Mode" toggle

**Expected Results:**
- ✅ Toggle exists on area card
- ✅ Shows current mode:
  - ON (checked) = Using Preset Mode
  - OFF (unchecked) = Manual Mode
- ✅ Clicking toggle switches between modes
- ✅ WebSocket updates reflect immediately
- ✅ Target temperature adjusts based on mode

**Test Procedure:**
1. Ensure area is in Manual Mode (toggle OFF)
2. Set manual temperature to 22.0°C
3. Note "Target Temperature: 22.0°C"
4. Click toggle to enable Preset Mode
5. Wait 1 second
6. Verify:
   - Toggle is now ON (checked)
   - Target temperature changed to match current preset
   - Temperature may be different from 22.0°C

---

### 4. Simplified Presence Sensor Configuration

**Location:** Area Detail → Settings Tab → Presence Sensors

**Test Steps:**
1. Navigate to area → Settings tab
2. Expand "Presence Sensors" section
3. Click "Add Presence Sensor"

**Expected Results - Dialog:**
- ✅ Dialog title: "Add Presence Sensor"
- ✅ Info alert shows:
  - "Preset Mode Control"
  - "When nobody is home, the system will automatically switch to the 'Away' preset mode"
  - "When presence is detected, it switches to the 'Home' preset mode"
- ✅ Only ONE field: "Entity" (dropdown to select sensor)
- ✅ NO temperature adjustment fields:
  - ❌ "Action When Away" - should NOT be visible
  - ❌ "Action When Home" - should NOT be visible
  - ❌ "Temperature Drop" - should NOT be visible
  - ❌ "Temperature Boost" - should NOT be visible

**Test Procedure - Add Sensor:**
1. Click "Add Presence Sensor"
2. Verify simplified dialog (info alert, no temp fields)
3. Select an entity (e.g., "binary_sensor.woonkamer_presence")
4. Click "Add"
5. Verify sensor added to list

**Expected Results - Sensor Description:**
- ✅ Sensor listed with simplified description
- ✅ Shows: "Controls preset mode: switches to 'Away' when nobody is home"
- ✅ Does NOT show old format:
  - ❌ "When away: Reduce by X°C"
  - ❌ "When home: Increase by X°C"

---

### 5. Integration Test - Complete Flow

**Scenario:** Verify global presets work end-to-end with all features

**Test Steps:**

1. **Setup Global Preset**
   - Go to Settings → Global Presets
   - Set "Home" global preset to 19.5°C
   - Set "Away" global preset to 17.0°C

2. **Configure Area to Use Global**
   - Navigate to "Woonkamer" → Settings
   - Expand "Preset Temperature Configuration"
   - Ensure "Home: Use Global" is ON (using global)
   - Ensure "Away: Use Global" is ON (using global)
   - Verify displayed temps: "19.5°C" and "17.0°C"

3. **Set Preset Mode**
   - Go to Overview tab
   - Expand "Preset Modes"
   - Set preset to "Home"
   - Verify target temperature: 19.5°C

4. **Test Preset Switching**
   - Change preset to "Away"
   - Verify target temperature changes to 17.0°C
   - Change back to "Home"
   - Verify target temperature returns to 19.5°C

5. **Test Manual Override**
   - Toggle "Using Preset Mode" to OFF (Manual Mode)
   - Set manual temperature to 22.0°C
   - Verify target shows 22.0°C
   - Toggle back to Preset Mode (ON)
   - Verify target returns to 19.5°C (Home preset)

6. **Test Global Change Reflection**
   - While in Preset Mode = "Home"
   - Note current target: 19.5°C
   - Go to Settings → Global Presets
   - Change "Home" to 20.0°C
   - Return to "Woonkamer" area
   - Verify target temperature updated to 20.0°C

**Expected Results:**
- ✅ All temperature changes reflect immediately via WebSocket
- ✅ Manual mode overrides preset temperature
- ✅ Switching back to preset mode uses correct global temperature
- ✅ Global preset changes immediately affect areas using that preset
- ✅ No temperature adjustments from presence sensors

---

## Automated Test Status

**Note:** Automated E2E tests were created but are currently not functional due to UI selector issues. The test file `global-presets.spec.ts` exists and covers:

- Global Preset Temperature display and updates
- Per-Area Preset Configuration toggles
- Presence Sensor simplified UI
- Manual Override integration

**Test File:** `tests/e2e/tests/global-presets.spec.ts`

**Issue:** Tests cannot locate area elements on the page. This may be due to:
- Routing/URL issues
- Timing problems (React app not fully loaded)
- Incorrect selector patterns

**Recommendation:** Use this manual testing guide until automated tests are debugged. All functionality should be manually verified before each release.

---

## Regression Tests

When testing this feature, also verify these existing features still work:

### Existing Functionality
- ✅ Temperature control (sliders, input fields)
- ✅ Preset mode dropdown shows all 6 modes
- ✅ Window sensors still function
- ✅ Boost mode works correctly
- ✅ Device management not affected
- ✅ Schedule functionality intact

### Presence Sensors - Old vs New Behavior

**OLD Behavior (v0.4.2 and earlier):**
- Presence sensors could add/subtract temperature (±1°C)
- Required action selection and temperature values
- Complex dialog with multiple fields

**NEW Behavior (v0.4.3+):**
- Presence sensors ONLY control preset mode switching
- Away when nobody home → "Away" preset
- Home when presence detected → "Home" preset
- NO temperature adjustments
- Simplified dialog with info alert only

**Verification:**
1. Any existing presence sensors should show simplified description
2. Adding new presence sensors should only ask for entity selection
3. Temperature should match preset exactly (no +1°C boost)

---

## Known Issues

None at this time. All functionality has been tested manually and works correctly.

---

## Version

- **Feature Version:** v0.4.3
- **Test Guide Version:** 1.0
- **Last Updated:** 2024-01-XX
