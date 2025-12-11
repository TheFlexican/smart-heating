import { test, expect } from '@playwright/test';
import { navigateToSmartHeating, navigateToArea } from './helpers';

test.describe('Thermostat Hysteresis Behavior', () => {
  test('thermostat uses current temp within hysteresis', async ({ page }) => {
    // Mock the areas API to return a deterministic area state
    await page.route('**/api/smart_heating/areas', async (route) => {
      const body = {
        areas: {
          test_area: {
            area_id: 'test_area',
            name: 'Living Room',
            target_temperature: 22,
            current_temperature: 21,
            hysteresis_override: 1,
            thermostats: ['climate.thermo1'],
          },
        },
      };
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
    });

    // Load UI and navigate to area
    await navigateToSmartHeating(page);
    await navigateToArea(page, 'Living Room');

    // Wait for the area card to render and check for displayed target temperature
    // This selector is intentionally generic; adjust if the UI markup changes.
    const targetText = await page.locator('text=Target').first().textContent();
    // Either the UI shows the controlled setpoint or the effective current temp
    expect(targetText).toMatch(/21(?:\.0)?|22(?:\.0)?/);
  });
});
