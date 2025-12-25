# Heating Expert Deep Dive — Algorithms & Tuning

This document explains the control methods used by Smart Heating, the heating-curve
autotune heuristics, PID guidance, TRV behaviour, and practical tuning recipes.

Contents
- Heating curve theory
- Autotune heuristic (how coefficients are computed)
- PID controller notes and tuning
- TRV and valve offsets
- Hysteresis, frost protection and safety overrides
- Data collection, retention and how to use analytics for tuning
- Practical tuning recipes and YAML examples

## Heating curve theory

Smart Heating computes an area flow (or device) target using a heating-curve
approach modeled after SAT-like heuristics. The typical form:

$flow\_temp = base\_offset + coefficient \times (setpoint - outside\_temp)$

Where:
- $base\_offset$ is a small constant offset (system-dependent, e.g. 0–10°C)
- $coefficient$ scales how aggressively the system raises flow temperature as
  outside temperature falls.

The integration implements this as a per-area heating curve with a stored
coefficient and optional autotune adjustments.

## Autotune heuristic

Smart Heating samples heating events (when heating is active) and records:
- setpoint (target temperature)
- outside temperature
- observed indoor response (time to reach setpoint, overshoot)

A simple coefficient estimate used in code (expressed in plain terms):

1. Compute a heating curve value from (setpoint, outside_temp) using the
   heating-curve model (see `heating_curve.py`).
2. If the heating_curve_value != 0 compute coefficient estimate:

$\hat{c} = \frac{4 \times (setpoint - base\_offset)}{heating\_curve\_value}$

3. Apply smoothing and derivative damping (small adjustments per-event). The
   code uses tiny step sizes for stability: see constants like
   `LEARNING_TEMP_ADJUSTMENT_SMALL` (0.02°C) and `LEARNING_TEMP_ADJUSTMENT_MEDIUM` (0.05°C).

Autotune is intentionally conservative: it nudges the coefficient over many
events, avoids reacting to single noisy events, and preserves historical
stability.

### Autotune pseudocode

```
for each completed heating_event:
  measure setpoint, outside_temp, indoor_delta
  estimate c_hat using heating_curve inversion
  c_new = blend(current_coefficient, c_hat, alpha)
  if |c_new - current| > max_step: c_new = current + sign(c_hat-current)*max_step
  persist c_new
```

## PID controller notes and tuning

Smart Heating supports optional per-area PID to smooth final actuation.
Guidance for PID parameters (start conservative):

- Sample period: system records every 5 minutes by default (`HISTORY_RECORD_INTERVAL_SECONDS = 300`).
- Start values (example):
  - Kp = 0.5
  - Ki = 0.02 (integral over long window)
  - Kd = 0.1 (derivative with filtering)
- Anti-windup: clamp integral when actuator saturated.
- Derivative filtering: use a small low-pass to avoid noise amplification.

Practical tuning recipe (iterative):
1. Start with Ki = 0, Kd = 0. Increase Kp until system responds quickly but without sustained oscillation.
2. Add Ki to eliminate steady-state error (small increments).
3. Add Kd if overshoot/oscillation occurs; add derivative filtering.

Use a test schedule (single point change) and examine recorded history (5-minute samples) to evaluate response time and overshoot.

## TRV and valve behaviour

TRVs (thermostatic radiator valves) are handled by mapping area targets to
TRV heating/idle setpoints. Relevant parameters in code and defaults:
- `DEFAULT_TRV_HEATING_TEMP = 25.0` (°C)
- `DEFAULT_TRV_IDLE_TEMP = 10.0` (°C)
- `DEFAULT_TRV_TEMP_OFFSET = 10.0` (°C)

For temperature-controlled valves, Smart Heating computes valve setpoints as
`trv_target = area_target + trv_temp_offset` to ensure valves see a higher
control temperature when active, and a low idle temp when disabled.

## Hysteresis, frost protection and safety overrides

- Hysteresis: small buffer around the target to avoid rapid cycling. Suggested
  per-area range: 0.1–0.7°C (default often 0.3°C).
- Frost protection: default `DEFAULT_FROST_PROTECTION_TEMP = 7.0°C`. When
  enabled, areas will not drop below this temperature (unless explicitly
  overridden with emergency actions).
- Window & presence sensors: window open can trigger either `turn_off` or
  `reduce_temperature` behaviour (see `ATTR_WINDOW_OPEN_ACTION` and
  `DEFAULT_WINDOW_OPEN_TEMP_DROP = 5.0°C`). Presence sensors can trigger
  temporary boosts as configured.

## OpenTherm Gateway specifics

When an OpenTherm Gateway is configured, Smart Heating computes a boiler set
point using an overhead value. Constants in code:
- `OPENTHERM_OVERHEAD_DEFAULT = 20.0°C`
- `OPENTHERM_OVERHEAD_MAX = 27.2°C`

Flow temperature for OpenTherm path is: `boiler_setpoint = flow_temp + overhead`.
Overhead can be limited by the max constant to avoid overdriving boiler temps.

## Data collection and retention

- Sampling interval: 5 minutes (300s) by default. This gives a reasonable
  trade-off between resolution and storage.
- Default history retention: 30 days; configurable up to 365 days.
- Learning engine retains events separately (90 days default) to allow
  long-term pattern extraction while limiting storage use.

## Practical tuning recipes

1) Improve slow warm-up in well-insulated house:
  - Increase heating-curve coefficient slightly (e.g. +0.2), monitor 7–14 days.
  - Reduce hysteresis to 0.2°C.

2) Reduce overshoot in radiator systems:
  - Add small PID derivative term (Kd = 0.1) and enable derivative filtering.
  - Lower coefficient slightly and increase hysteresis to 0.4–0.7°C.

3) TRV-heavy zones not reaching setpoint:
  - Increase TRV offset (e.g. from 10°C to 12–15°C) so valve sees higher control temp.

## YAML examples — autotune trigger and diagnostics

Start a conservative autotune run (pseudo-service shown; implementation depends on UI/service names):

```yaml
service: smart_heating.trigger_autotune
data:
  area_id: living_room
  duration_days: 14
  mode: conservative
```

Collect diagnostic snapshot via REST (curl):

```bash
curl -s -H "Authorization: Bearer <TOKEN>" \
  http://YOUR_HA:8123/api/smart_heating/areas | jq
```

## How to evaluate changes

- Use the `history` endpoint and UI charts to compare pre/post changes for 7–14 days.
- Key metrics: time-to-setpoint, overshoot, on-time percentage, efficiency score.

## References & further reading

- SAT / Smart Autotune Thermostat concepts
- PID tuning literature (Ziegler–Nichols, Cohen–Coon)

---
Add this file to the repo for power users and contributors who need precise
guidance on the algorithms, coefficients and safe tuning practices.
