# Quick Start Optimization Guide (SAT Users)

**For users migrating from SAT (Smart Autotune Thermostat) or looking for maximum energy efficiency**

Smart Heating implements all core SAT optimization features, providing intelligent boiler control for optimal energy consumption and comfort. This guide helps you enable and configure these features for best results.

---

## 🎯 What Smart Heating Shares with SAT

Smart Heating's advanced control features are **explicitly modeled after SAT**, providing equivalent or superior optimization:

| Feature | SAT | Smart Heating | Status |
|---------|-----|---------------|--------|
| **Heating Curve** | ✅ | ✅ **Auto-enabled** | Identical algorithm |
| **PWM Control** | ✅ | ✅ Available | For non-modulating boilers |
| **PID Controller** | ✅ | ✅ Available | Auto-tuning supported |
| **Overshoot Protection** | ✅ | ✅ Available | OPV calibration API |
| **Minimum Setpoint** | ✅ | ✅ **Always active** | Dynamic adjustment |
| **Per-Area Heating Types** | ✅ | ✅ **Full support** | Floor vs Radiator |
| **Modulation Optimization** | ✅ | ✅ **Built-in** | Real-time monitoring |

---

## 🚀 Quick Start: 3-Step Setup

### Step 1: Configure OpenTherm Gateway ✅

1. Go to **Global Settings → OpenTherm** tab
2. Select your OpenTherm Gateway from the dropdown
3. Click **Save Configuration**

**Result**: Heating curve is **automatically enabled** for optimal efficiency! 🎉

### Step 2: Set Heating Types per Area ✅

Configure each area based on your heating system:

1. Navigate to each **Area Details → Settings**
2. Find the **"Heating Type"** card
3. Select:
   - **Floor Heating** - For underfloor systems (30-40°C flow)
   - **Radiator** - For traditional radiators (50-60°C flow)

**Why this matters:**
- Floor heating: +10°C overhead → Lower flow temps → 20-30% better modulation efficiency
- Radiators: +20°C overhead → Higher flow temps for adequate heat output

### Step 3: Enable Advanced Features (Optional) ⚙️

For maximum SAT-like optimization, enable in **Global Settings → Advanced Control**:

- ✅ **Heating Curve**: Auto-enabled when gateway configured *(Already ON!)*
- ✅ **PWM Control**: For boilers without native modulation
- ✅ **PID Controller**: Fine-tuning with auto-gains
- ✅ **OPV Calibration**: Run via API for overshoot protection

---

## 📊 Expected Energy Savings

Based on SAT's proven results and our implementation:

| Configuration | Typical Savings | Notes |
|--------------|----------------|-------|
| **Heating Curve Only** | 10-20% | Safe, proven, auto-enabled |
| **+ Floor Heating Config** | +5-10% | Lower flow temps, better modulation |
| **+ PWM (non-mod boilers)** | +5-15% | Reduces cycling losses |
| **+ PID Fine-tuning** | +2-5% | Per-system optimization |
| **Total Potential** | **20-35%** | Compared to on/off control |

---

## 🎨 Understanding Heating Curve

The heating curve calculates optimal boiler flow temperature based on:

```
Flow Temp = Base Offset + (Coefficient × Heating Curve Value)

Where:
- Base Offset: 40°C (floor) or 55°C (radiator)
- Coefficient: 1.0 default (tunable per area)
- Heating Curve Value: f(room_target, outdoor_temp)
```

**Example (Floor Heating)**:
- Outdoor: 5°C
- Room Target: 21°C
- Result: ~35°C flow temperature
- vs. Traditional: 50°C+ (wastes 30% energy!)

**Example (Radiators)**:
- Outdoor: 5°C
- Room Target: 21°C
- Result: ~58°C flow temperature
- vs. Fixed: 70°C (wastes 15-20% energy!)

---

## 🔧 Advanced Tuning (Power Users)

### Per-Area Coefficient Adjustment

If an area heats too slowly or too fast:

```bash
# API call to adjust coefficient
curl -X POST "http://your-ha:8123/api/smart_heating/areas/{area_id}/heating_curve" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"heating_curve_coefficient": 1.2}'
```

- **Increase** (1.2-1.5): For larger radiators or better insulation
- **Decrease** (0.8-0.9): For smaller radiators or poor insulation

### PWM Configuration

For boilers without modulation support:

1. Enable in **Global Settings → Advanced Control → PWM**
2. Default cycle: 60-600 seconds ON/OFF
3. Automatically adjusts duty cycle based on setpoint

**Result**: Approximates modulation behavior on simple on/off boilers

### PID Auto-Tuning

For fine-tuned temperature control:

1. Enable in **Global Settings → Advanced Control → PID**
2. System learns optimal gains automatically
3. Reduces overshoot and temperature oscillation

**Best for**: Systems with slow thermal response (floor heating)

### OPV Calibration

Prevents overshoot during low-load conditions:

```bash
# Run calibration routine
curl -X POST "http://your-ha:8123/api/smart_heating/opentherm/calibrate" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**When to use**: Many closed valves causing return temp to rise quickly

---

## 📈 Monitoring Optimization

### 1. OpenTherm Dashboard

View real-time boiler metrics:
- Modulation level (aim for 20-40% for floor, 40-60% for radiators)
- Flow temperature (should match heating curve output)
- Return temperature (should be 10-15°C below flow)
- Flame status (fewer on/off cycles = better)

### 2. Efficiency Reports

Navigate to **Analytics → Efficiency Reports**:
- Energy score: 0-100 (80+ is excellent)
- Heating cycles: Fewer is better
- Temperature deviation: Lower is better
- Smart recommendations: Follow suggestions

### 3. Log Analysis

Check logs for optimization confirmation:
```
OpenTherm gateway: Boiler ON, setpoint=37.2°C (overhead=10.0°C, 1 floor heating, 0 radiator)
```

**Good signs**:
- Setpoints match heating curve formula
- Overhead matches heating type
- Modulation levels stable (not bouncing 0-100%)

---

## ⚠️ Safety Notes

All optimization features respect safety limits:

- ✅ Frost protection: Minimum 7°C (configurable)
- ✅ Maximum flow temp: 80°C hard limit
- ✅ Emergency shutdown: Safety sensors (smoke/CO)
- ✅ Manual override: Always available on thermostat

---

## 🆚 SAT vs Smart Heating: Key Differences

| Aspect | SAT | Smart Heating | Notes |
|--------|-----|---------------|-------|
| **Default State** | Optimizations ON | Optimizations ON (when OpenTherm configured) | Smart Heating auto-enables |
| **Multi-Zone** | Single zone focus | Full multi-zone support | Areas can have different types |
| **UI** | Minimal | Full React dashboard | Real-time monitoring |
| **Installation** | Manual setup | HACS + GUI config | Easier setup |
| **Device Support** | MQTT only | Universal (any HA integration) | Works with Nest, Ecobee, etc. |

---

## 📚 Additional Resources

- **Architecture**: [docs/en/ARCHITECTURE.md](ARCHITECTURE.md) - Technical deep dive
- **Advanced Control**: [docs/en/ADVANCED_CONTROL.md](ADVANCED_CONTROL.md) - Detailed settings
- **OpenTherm**: [docs/en/OPENTHERM.md](OPENTHERM.md) - Gateway integration guide
- **API Reference**: [README.md](../../README.md#rest-api) - Programmatic control

---

## 🎓 Pro Tips

1. **Start Simple**: Let heating curve run for 1-2 days before enabling PID/PWM
2. **Monitor Logs**: Check modulation levels and cycle counts daily for first week
3. **Tune Gradually**: Adjust coefficients by 0.1-0.2 increments only
4. **Seasonal Adjustment**: May need different coefficients summer vs winter
5. **Floor Heating**: Be patient! Thermal mass means 2-3 hour response times

---

## 🆘 Troubleshooting

**"Area heats too slowly"**
- Increase `heating_curve_coefficient` by 0.2
- Check heating type is set correctly
- Verify boiler reaches calculated setpoint

**"Area overshoots target"**
- Decrease `heating_curve_coefficient` by 0.1
- Enable PID for tighter control
- Run OPV calibration

**"Boiler cycles too much"**
- Enable PWM if boiler lacks modulation
- Increase hysteresis (0.5 → 0.8°C)
- Check minimum setpoints are enforced

**"No optimization happening"**
- Verify OpenTherm gateway is selected in Global Settings
- Check logs for "Auto-enabled heating curve" message
- Ensure `advanced_control_enabled` is true

---

## ✅ Verification Checklist

After setup, confirm optimization is active:

- [ ] OpenTherm gateway selected in Global Settings
- [ ] "Auto-enabled heating curve" appears in logs
- [ ] Heating types configured per area (floor vs radiator)
- [ ] Boiler setpoints match heating curve formula (check logs)
- [ ] Modulation levels appropriate for heating type
- [ ] Energy score improving in Efficiency Reports (after 7 days)

---

**Last Updated**: December 2025 (v0.5.13+)
**Compatibility**: Requires OpenTherm Gateway integration in Home Assistant
