Fix manual-override toggle when area is disabled (fixes #13)

This PR updates the behavior to disable the manual override toggle when a zone is disabled to avoid unexpected transitions to manual mode when a preset is disabled. Included unit test covers the disabled state and ensures no API calls occur.
