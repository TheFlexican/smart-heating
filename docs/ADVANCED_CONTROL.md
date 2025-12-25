# Advanced Control Guide

This guide covers advanced features and configuration for Smart Heating power users.

## Heating Curve & SAT Optimization
- **Heating curve**: Automatically adjusts flow temperature based on outside temperature and area type (radiator/floor heating)
- **SAT-inspired optimization**: Uses Smart Autotune Thermostat (SAT) algorithms for energy savings
- **OpenTherm Gateway**: Integrate with OpenTherm for boiler modulation and advanced control

## PWM & PID Control
- **PWM control**: Approximates modulation on non-modulating boilers
- **PID controller**: Optional fine-tuning with auto-gains for precise temperature control

## Per-Area Configuration
- **Hysteresis**: Prevents rapid cycling (configurable per area)
- **TRV idle/heating temps**: Fine-tune TRV behavior
- **Frost protection**: Set minimum temperature for all areas

## Migration & Storage
- **JSON/database storage**: Choose between file-based and database storage
- **Seamless migration**: Switch between storage backends without data loss
- **Validation**: Automatic validation before migration

## Logging & Debugging
- **Per-area logs**: Detailed logs for each area
- **Event filtering**: Color-coded event types, one-click filtering
- **Interactive charts**: Customizable time ranges, preset filters

## Tips
- Use analytics to identify efficiency improvements
- Combine window/presence sensors for smart automation
- Use backup/restore before major changes

---
For API and service reference, see ARCHITECTURE.md.
