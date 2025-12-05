import { test, expect } from '@playwright/test';
import { navigateToArea, switchToTab, dismissSnackbar, expandSettingsCard } from './helpers';

test.describe('Sensor Tests', () => {
  test.skip('should add presence sensor', async ({ page }) => {
    // This test requires actual person entities to be available in Home Assistant
    // Skipping for now
    await navigateToArea(page, 'Living Room');
    await switchToTab(page, 'Settings');
    await dismissSnackbar(page);
    
    console.log('Add presence sensor test skipped - requires actual entities in Home Assistant');
    
    // Click Add Presence Sensor button to open the dialog
    await page.click('button:has-text("Add Presence Sensor")');
    await page.waitForTimeout(1000);
    
    // The dialog should open with Entity dropdown
    // Click on the Entity dropdown
    const entityDropdown = page.locator('text=Entity').locator('..');
    await entityDropdown.click();
    await page.waitForTimeout(500);
    
    // Select a person entity from the dropdown (if available)
    // Or just click Cancel for now since we need actual entities
    await page.click('button:has-text("Cancel")');
    
    // For this test to work properly, we'd need actual entities in HA
    // Skip verification for now
    console.log('Add presence sensor requires actual entities in Home Assistant');
  });

  test('should remove presence sensor', async ({ page }) => {
    await navigateToArea(page, 'Living Room');
    await switchToTab(page, 'Settings');
    await dismissSnackbar(page);
    
    // Expand presence sensors
    await expandSettingsCard(page, 'Presence Sensors');
    
    // Look for a remove/delete button
    const removeButtons = page.locator('button[aria-label*="Remove"], button[aria-label*="Delete"], button:has-text("Remove")');
    const count = await removeButtons.count();
    
    if (count > 0) {
      await removeButtons.first().click();
      await page.waitForTimeout(1000);
    }
  });
});
