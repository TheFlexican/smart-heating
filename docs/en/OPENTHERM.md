# OpenTherm Gateway (opentherm_gw) Integration

Smart Heating integrates with the Home Assistant OpenTherm Gateway integration to provide global boiler control across areas.

Key points:
- Smart Heating expects the OpenTherm Gateway integration's ID/`id` field (slug), not the climate entity ID. The `id` is often a short slug (e.g. `gateway1`).
- To add a gateway via the Home Assistant UI: Settings → Devices & Services → Add Integration → OpenTherm Gateway, then fill the fields (Name, Path/URL, ID). Use a slug in the ID field.
- After creating an OpenTherm Gateway config entry, go to Smart Heating → Settings → OpenTherm and select your gateway from the dropdown list and Save.
- For automated setups, prefer Home Assistant REST config flow to safely add integrations.

Troubleshooting:
- If the OTGW integration is not installed, the dropdown will show no entries.
- If you use MQTT to mock an OTGW climate device, Smart Heating will not read the OTGW-specific services — prefer the official integration for correct behavior.
