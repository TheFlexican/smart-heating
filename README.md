# Smart Heating

# Smart Heating for Home Assistant

A powerful, adaptive multi-zone heating control integration for Home Assistant, featuring a modern web interface, intelligent scheduling, device-agnostic support, and advanced learning capabilities.

## Features

- **Uses Home Assistant Areas**: Zones are managed in Home Assistant, not in the app.
- **Device Assignment**: Assign any HA climate device (thermostats, TRVs, ACs) to areas.
- **Universal Device Support**: Works with all HA climate integrations (Nest, Ecobee, Zigbee2MQTT, Tado, etc.)
- **Flexible Scheduling**: Time-based, preset, date-specific, cross-day schedules per area.
- **Boost & Vacation Modes**: Temporary and scheduled overrides for comfort and energy savings.
- **Safety & Automation**: Integrates smoke/CO/gas sensors, window/presence sensors for smart shutoff and automation.
- **Adaptive Learning**: Heating curve, weather-aware, persistent stats, and analytics.
- **Advanced Configuration**: Hysteresis, TRV, OpenTherm, frost protection, per-area settings.
- **Backup & Restore**: JSON/database storage, migration, validation, and seamless switching.
- **Modern UI**: Responsive React SPA, Material-UI, dark/light themes, drag-and-drop, i18n (EN/NL).
- **Real-time Updates**: WebSocket-based live monitoring and control.

## Installation & Setup

1. **Install via HACS (Recommended):**
   - Add custom repository: `https://github.com/TheFlexican/smart_heating`
   - Search for "Smart Heating" in HACS and install
   - Restart Home Assistant
2. **Manual Installation:**
   - Clone or copy to `/config/custom_components/smart_heating`
   - Restart Home Assistant
3. **Configuration:**
   - Go to Settings → Devices & Services → Add Integration
   - Search for "Smart Heating" and follow the setup wizard
   - Assign devices to Home Assistant areas (zones)

## Using Smart Heating

- **Access the Web Interface:**
  - Sidebar link in Home Assistant UI
  - View and control all areas, devices, and schedules
- **Assign Devices:**
  - Assign climate devices to HA areas via the UI
- **Configure Schedules:**
  - Set up time-based, preset, or date-specific schedules for each area
- **Boost & Vacation:**
  - Activate boost for temporary comfort
  - Schedule vacation mode for energy savings
- **Safety & Automation:**
  - Integrate window, presence, smoke, CO, and gas sensors for automation and safety
- **Analytics & History:**
  - View temperature history, efficiency reports, and recommendations
- **Backup & Restore:**
  - Export/import configuration, migrate between JSON and database storage

## Supported Devices & Integrations

- Any Home Assistant climate entity (Nest, Ecobee, Zigbee2MQTT, Tado, LG ThinQ, etc.)
- TRVs, radiators, underfloor heating, heat pumps, ACs
- Zigbee2MQTT, Z-Wave, WiFi, and more
- Safety sensors: smoke, CO, gas
- Window/presence sensors for smart shutoff
- OpenTherm Gateway integration

## Troubleshooting & Support

- Check Home Assistant logs for errors
- Use the UI for configuration validation
- For help, visit [GitHub Issues](https://github.com/TheFlexican/smart_heating/issues)

## Internationalization & Accessibility

- Full support for English and Dutch (Nederlands)
- Accessible UI with keyboard navigation and ARIA labels

## Links & Resources

- [GitHub Repository](https://github.com/TheFlexican/smart_heating)
- [Home Assistant](https://www.home-assistant.io/)
- [HACS Integration](https://hacs.xyz/)
- [Releases](https://github.com/TheFlexican/smart_heating/releases)

---
For developer, technical, and advanced usage, see DEVELOPER.md and ARCHITECTURE.md.

## How Smart Heating maps to Home Assistant

- Smart Heating uses Home Assistant Areas as the authoritative "zone" concept. Do not create zones inside the app — create them in HA (Settings → Areas) and then assign devices in the Smart Heating UI.
- Devices are standard Home Assistant entities (climate.*, switch.*, sensor.*, binary_sensor.*). The integration discovers capabilities and exposes per-area control entities.

## Service examples (YAML)

Set a boost on an area for 60 minutes:
```yaml
service: smart_heating.set_boost_mode
data:
  area_id: living_room
  duration_minutes: 60
  temperature: 24
```

Set frost protection globally:
```yaml
service: smart_heating.set_frost_protection
data:
  enabled: true
  temp: 7.0
```

Add a window sensor to an area:
```yaml
service: smart_heating.add_window_sensor
data:
  area_id: kitchen
  entity_id: binary_sensor.kitchen_window
```

## REST API examples (curl)

List areas:
```bash
curl -s -H "Authorization: Bearer <LONG_LIVED_TOKEN>" \
  http://YOUR_HA:8123/api/smart_heating/areas | jq
```

Set an area temperature via API:
```bash
curl -s -X POST -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"temperature":21.5}' \
  http://YOUR_HA:8123/api/smart_heating/areas/area_1/temperature
```

## HACS & Packaging notes

See `HACS_NOTES.md` for the reviewer checklist and packaging guidance (config flow, manifest, static assets, no hard-coded secrets).
