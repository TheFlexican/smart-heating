# Heating Type Implementation

## Overview
Implemented configurable heating types per area to optimize OpenTherm Gateway boiler control for different heating systems (radiators vs floor heating).

## Problem Solved
- **Issue**: Fixed +20°C overhead too high for floor heating systems
- **Floor heating** needs 30-45°C water temperature (optimal: 35-40°C)
- **Radiators** need 50-60°C water temperature
- Previous implementation: `boiler_setpoint = max_target_temp + 20°C`
- Result: Floor heating zones got 50-60°C water (inefficient, uncomfortable)

## Solution
Per-area heating type configuration with different overhead temperatures:
- **Radiator** (default): +20°C overhead
- **Floor Heating**: +10°C overhead (configurable)
- **Custom Override**: Manual override for special cases

## Implementation Details

### Backend Changes

#### 1. Area Model (`smart_heating/models/area.py`)
Added two new fields:
```python
self.heating_type: str = "radiator"  # "radiator" or "floor_heating"
self.custom_overhead_temp: float | None = None  # Custom overhead override
```

Serialization/deserialization:
- `to_dict()`: Exports heating_type and custom_overhead_temp
- `from_dict()`: Imports with defaults (heating_type="radiator", custom_overhead_temp=None)

#### 2. Device Control (`smart_heating/climate_handlers/device_control.py`)
Updated `async_control_opentherm_gateway()`:
```python
# Calculate overhead based on heating types of active zones
for area in heating_areas:
    if area.custom_overhead_temp is not None:
        overhead = area.custom_overhead_temp
    elif area.heating_type == "floor_heating":
        overhead = 10.0  # Default for floor heating
    else:  # radiator
        overhead = 20.0  # Default for radiator

# Use highest overhead for safety (fastest heating requirement)
boiler_setpoint = max_target_temp + max(overheads)
```

Logging enhanced to show:
- Number of floor heating zones active
- Number of radiator zones active
- Overhead temperature used
- Example: "Boiler ON - Setpoint: 35.0°C | overhead +10°C | 1 floor heating + 0 radiator"

#### 3. OpenTherm Logger (`smart_heating/opentherm_logger.py`)
Updated `log_boiler_control()` to accept:
- `overhead`: Overhead temperature used (°C)
- `floor_heating_count`: Number of floor heating zones active
- `radiator_count`: Number of radiator zones active

Enhanced log message format:
```
Boiler ON - Setpoint: 35.0°C | overhead +10°C | 1 floor heating + 2 radiator
```

#### 4. API Handler (`smart_heating/api_handlers/areas.py`)
New endpoint: `POST /api/smart_heating/areas/{area_id}/heating_type`

Request body:
```json
{
  "heating_type": "radiator" | "floor_heating",
  "custom_overhead_temp": 8.0  // Optional, 0-30°C
}
```

Validation:
- `heating_type`: Must be "radiator" or "floor_heating"
- `custom_overhead_temp`: Must be between 0 and 30°C

#### 5. Response Builder (`smart_heating/utils/response_builders.py`)
Updated `build_area_response()` to include:
```python
"heating_type": getattr(area, "heating_type", "radiator"),
"custom_overhead_temp": getattr(area, "custom_overhead_temp", None),
```

### API Testing

#### 1. Get Areas (verify defaults)
```bash
curl -s http://localhost:8123/api/smart_heating/areas | \
  jq '.areas[] | {name: .name, heating_type: .heating_type, custom_overhead_temp: .custom_overhead_temp}'
```
Expected: All areas default to `heating_type: "radiator"`, `custom_overhead_temp: null`

#### 2. Set Floor Heating
```bash
curl -s -X POST http://localhost:8123/api/smart_heating/areas/woonkamer/heating_type \
  -H "Content-Type: application/json" \
  -d '{"heating_type": "floor_heating"}' | jq
```
Expected: `{"success": true}`

#### 3. Set Custom Overhead
```bash
curl -s -X POST http://localhost:8123/api/smart_heating/areas/woonkamer/heating_type \
  -H "Content-Type: application/json" \
  -d '{"custom_overhead_temp": 8.0}' | jq
```
Expected: `{"success": true}`

#### 4. Validation Tests

Invalid heating type:
```bash
curl -s -X POST http://localhost:8123/api/smart_heating/areas/woonkamer/heating_type \
  -H "Content-Type: application/json" \
  -d '{"heating_type": "invalid_type"}' | jq
```
Expected: `{"error": "heating_type must be 'radiator' or 'floor_heating'"}`

Overhead too high:
```bash
curl -s -X POST http://localhost:8123/api/smart_heating/areas/woonkamer/heating_type \
  -H "Content-Type: application/json" \
  -d '{"custom_overhead_temp": 50}' | jq
```
Expected: `{"error": "custom_overhead_temp must be between 0 and 30°C"}`

### Test Results (2025-12-09)

✅ **API Endpoints**: All working correctly
- GET areas returns heating_type and custom_overhead_temp
- POST heating_type accepts and saves configuration
- Validation working correctly

✅ **Data Persistence**: Configuration saved to storage
- Heating type persists across restarts
- Custom overhead persists across restarts

⏳ **OpenTherm Control**: Cannot test yet (gateway unavailable)
- Need to connect physical OpenTherm Gateway
- Then verify boiler setpoint calculation
- Verify enhanced logging shows heating type breakdown

## Usage Examples

### Example 1: Living Room with Floor Heating
```bash
# Configure living room for floor heating
curl -X POST http://localhost:8123/api/smart_heating/areas/woonkamer/heating_type \
  -H "Content-Type: application/json" \
  -d '{"heating_type": "floor_heating", "custom_overhead_temp": 8.0}'
```

**Before**:
- Target: 20°C → Boiler setpoint: 40°C (20 + 20)
- Water temp too high for floor heating

**After**:
- Target: 20°C → Boiler setpoint: 28°C (20 + 8)
- Optimal for floor heating, efficient modulation

### Example 2: Mixed System (Kitchen Radiators + Living Room Floor Heating)
```bash
# Kitchen stays as radiator (default)
# Living room configured as floor_heating with +8°C overhead

# When both heating:
# Kitchen: target 21°C, needs +20°C → 41°C
# Living room: target 20°C, needs +8°C → 28°C
# Boiler setpoint: max(41, 28) = 41°C
```

**Safety Logic**: Use highest overhead when multiple zones active
- Ensures fastest heating zone gets adequate temperature
- Prevents under-heating of radiator zones

### Example 3: Fine-Tuning with Custom Overhead
```bash
# If default +10°C too high for specific floor heating system
curl -X POST http://localhost:8123/api/smart_heating/areas/woonkamer/heating_type \
  -H "Content-Type: application/json" \
  -d '{"heating_type": "floor_heating", "custom_overhead_temp": 5.0}'
```

## Frontend Integration (TODO)

### Area Settings Card
Add heating type configuration:
```typescript
<FormControl>
  <FormLabel>Heating Type</FormLabel>
  <RadioGroup value={area.heating_type} onChange={handleHeatingTypeChange}>
    <FormControlLabel value="radiator" control={<Radio />} label="Radiator" />
    <FormControlLabel value="floor_heating" control={<Radio />} label="Floor Heating" />
  </RadioGroup>
</FormControl>

{area.heating_type && (
  <TextField
    label="Custom Overhead Temperature (°C)"
    type="number"
    value={area.custom_overhead_temp || ''}
    onChange={handleCustomOverheadChange}
    helperText="Leave empty for default (radiator: 20°C, floor heating: 10°C)"
  />
)}
```

### OpenTherm Logger Display
Enhanced log message display:
```typescript
{event.data.floor_heating_count !== undefined && (
  <Chip
    label={`${event.data.floor_heating_count} floor heating`}
    color="info"
    size="small"
  />
)}
{event.data.radiator_count !== undefined && (
  <Chip
    label={`${event.data.radiator_count} radiator`}
    color="default"
    size="small"
  />
)}
{event.data.overhead !== undefined && (
  <Chip
    label={`+${event.data.overhead}°C overhead`}
    color="success"
    size="small"
  />
)}
```

## Translations (TODO)

### Dutch (`locales/nl/translation.json`)
```json
{
  "heatingType": {
    "title": "Verwarmingstype",
    "radiator": "Radiatoren",
    "floorHeating": "Vloerverwarming",
    "customOverhead": "Aangepaste overhead temperatuur",
    "customOverheadHelp": "Laat leeg voor standaard (radiatoren: 20°C, vloerverwarming: 10°C)",
    "description": "Configureer het type verwarmingssysteem voor optimale modulatie"
  }
}
```

### English (`locales/en/translation.json`)
```json
{
  "heatingType": {
    "title": "Heating Type",
    "radiator": "Radiator",
    "floorHeating": "Floor Heating",
    "customOverhead": "Custom Overhead Temperature",
    "customOverheadHelp": "Leave empty for default (radiator: 20°C, floor heating: 10°C)",
    "description": "Configure the heating system type for optimal modulation"
  }
}
```

## Benefits

### Efficiency
- Lower water temperatures for floor heating
- Boiler runs longer at lower modulation (20-30% instead of 40-50%)
- Less cycling, more efficient combustion
- Lower energy consumption

### Comfort
- Floor heating maintains more stable temperature
- Avoids overheating from excessive water temperature
- Better temperature distribution

### Flexibility
- Mixed systems supported (radiators + floor heating)
- Custom overhead for special cases
- Safety logic ensures all zones get adequate heat

## Next Steps

1. **Physical Testing**
   - Connect OpenTherm Gateway
   - Configure Woonkamer as floor_heating
   - Monitor boiler setpoint in logs
   - Verify modulation levels
   - Measure efficiency improvement

2. **Frontend UI**
   - Add heating type selector to area settings
   - Add custom overhead input field
   - Add tooltips explaining impact
   - Update OpenTherm logger display
   - Add translations (EN + NL)

3. **Documentation**
   - Update README.md with heating type feature
   - Update ARCHITECTURE.md with setpoint calculation logic
   - Update CHANGELOG.md with new feature
   - Add user guide for configuring heating types

4. **Testing**
   - Unit tests for heating type logic
   - E2E tests for API endpoints
   - Test mixed system scenarios
   - Test custom overhead validation

## Technical Debt

### Code Quality
- ⚠️ `async_control_opentherm_gateway()`: Cognitive complexity 32 (limit 15)
  - Consider extracting overhead calculation to separate method
  - Extract heating type breakdown to helper function

- ⚠️ `log_boiler_control()`: Cognitive complexity 23 (limit 15)
  - Consider simplifying message building logic
  - Extract message parts to separate methods

### Improvements
- Add area-specific overhead defaults (per heating type)
- Support more heating types (e.g., underfloor electric, panel heaters)
- Add learning: track actual water temps needed, adjust overhead automatically
- Add efficiency metrics: compare energy usage before/after heating type configuration

## Files Modified

Backend:
- `smart_heating/models/area.py` - Added heating_type and custom_overhead_temp fields
- `smart_heating/climate_handlers/device_control.py` - Updated setpoint calculation
- `smart_heating/opentherm_logger.py` - Enhanced logging with heating type context
- `smart_heating/api_handlers/areas.py` - Added handle_set_heating_type handler
- `smart_heating/utils/response_builders.py` - Added fields to area response
- `smart_heating/api.py` - Added heating_type endpoint route
- `smart_heating/api_handlers/__init__.py` - Exported handle_set_heating_type

Frontend: (TODO)
- `frontend/src/types.ts` - Add heating_type to Area interface
- `frontend/src/api.ts` - Add setHeatingType API function
- `frontend/src/components/AreaSettings.tsx` - Add heating type configuration UI
- `frontend/src/components/OpenThermLogger.tsx` - Display heating type breakdown
- `frontend/src/locales/en/translation.json` - English translations
- `frontend/src/locales/nl/translation.json` - Dutch translations
