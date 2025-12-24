# Google Nest-like Thermostat Features (Design & Implementation Roadmap)

This document outlines a roadmap and design for implementing Nest-like thermostat functionality in Smart Heating. It aims to guide future feature development with clear priorities, approaches, and safety constraints.

## Goals
- Implement Nest-style features incrementally while keeping the integration safe, modular, and opt-in.
- Prioritize features that deliver comfort and energy savings while ensuring boiler safety and respecting physical constraints.
- Provide testing, observability, and rollback strategies for each incremental feature.

## Feature Set (High-level)
1. Presence-aware learning
   - Automatic learning of schedules based on occupancy and behavior.
   - Adaptive temperature presets based on time-of-day and occupancy.
2. Auto-scheduling & Learning
   - Learning-based schedule generation that predicts user routines.
   - Day-of-week and seasonal adjustments.
3. Energy-aware optimization
   - Balance between comfort and efficiency using heuristics and optimization APIs
   - Provide an energy-efficiency score similar to Smart Assist (Nest)
4. Auto-away (presence inference)
   - Automatic switching to Away preset based on aggregated presence sensors and combined heuristics
5. Weather-aware adjustments
   - Predictive control using external weather data plus fallback strategies
6. Auto-sensitivity & Adaptive Gains
   - Automatically tune PID gains based on observed heating dynamics
7. Safety-minded learning
   - Prevent learned schedules if they conflict with frost protection or safety sensors
8. User feedback loop & hints
   - UI experiences to confirm or correct learned changes

## Minimum Viable Implementation (MVP)
- Implement per-area learning engine that listens to user changes (manual temperature changes) and learns heuristics: "X tends to set warmer at 6:30 AM on weekdays".
- Add a learning toggle at account/global level for controlled rollout (disabled by default).
- Provide UI + API to preview learned schedules and accept/reject them.

## Architecture
- New module: `smart_heating/learning_agents` (per-area agent) with pluggable backends (statistical, simple linear regression, or small ML model).
- Data flow: sensors -> coordinator -> learning agent -> suggestions -> user confirmation -> scheduled actions.
- Keep learning logic separate from control logic: learning only suggests changes; user approval or acceptance policy is required before automatic activation.

## Safety & Constraints
- Respect global `frost_protection` and safety sensors; never override to a lower limit that can cause freezing or unsafe conditions.
- Add sanity checks for setpoint ranges: min/max allowed values and hysteresis constraints.
- Add an approval policy: learned schedules are suggested and optionally auto-enabled depending on settings.

## Implementation Steps
1. Core Learning Framework
   - Add an area-level LearningAgent class with event-driven API to track changes and produce suggestions.
   - Add storage for training data sanitized and aggregated for privacy.
2. Suggestion UI
   - Add a 'Learned Schedules' tab in Area settings to preview suggestions.
   - Add accept/reject controls and a 'preview' toggle for a limited time period.
3. Background / Batch Learning job
   - Periodic background job that checks learning logs and updates suggestions (non-blocking).
4. Auto-enabling & Confidence
   - Use confidence thresholds before auto-enabling features; provide logs and revert ability.
5. Testing and A/B experiments
   - Create local simulation harness for validating scheduling changes at various seasons and weather patterns.

## Non-functional Requirements
- Backward-compatible: if learning is disabled, behavior unchanged
- Testable: Provide unit & integration tests for agent & suggestion behavior
- Privacy aware: respect user's data choices; learning data stored only locally, not shared remotely

## Milestone & Timeline
- Phase 0 (Research & Prototypes): Define heuristics and data models — 2 weeks
- Phase 1 (MVP): Implement LearningAgent + UI for suggestions — 4–6 weeks
- Phase 2 (Auto-Enabling & Gains): Implement auto-enabling and PID automatic gains under toggle — 6–8 weeks

## Metrics & Observability
- Add logging for learning suggestions and acceptance rates
- Add telemetry for energy efficiency improvements and user acceptance
- Add dashboards showing learning progress and schedule adoption metrics

## Risks & Mitigation
- Incorrect learned schedules: Implement a 'rehearse' or 'suggest & prompt' mode
- Boiler interactions & safety: Limit learning to schedules that comply with our safety policies

## Next steps
- Create a `learning_agents` skeleton with unit tests
- Add a UI in Area settings to show and accept suggested schedules
- Implement privacy-friendly storage for learning artifacts

---

Author: Smart Heating Team
Created: 2025-12-10
