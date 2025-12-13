import { test, expect } from '@playwright/test';
import { navigateToSmartHeating, navigateToArea, switchToTab, dismissSnackbar, expandSettingsCard } from './helpers';

// E2E test: navigate to Area -> Settings -> Expand 'Preset Modes' -> verify Select is disabled when area is disabled/off

test('preset select is disabled when area is disabled/off', async ({ page }) => {
  await navigateToSmartHeating(page);
  await navigateToArea(page, 'Living Room');
  await dismissSnackbar(page);

  // Toggle disable area using the top-right switch if currently enabled
  const enableSwitch = page.locator('input[type="checkbox"]').last();
  const wasEnabled = await enableSwitch.isChecked();
  if (wasEnabled) {
    await enableSwitch.click();
    await page.waitForTimeout(1000);
  }

  await switchToTab(page, 'Settings');
  await dismissSnackbar(page);

  // Expand preset modes card
  await expandSettingsCard(page, 'Preset Modes');

  // Wait for the Select (combobox) to appear and assert it's disabled
  const combobox = page.getByRole('combobox');
  await expect(combobox).toBeDisabled();

  // Restore original enabled state
  if (wasEnabled) {
    await enableSwitch.click();
    await page.waitForTimeout(1000);
  }
});
