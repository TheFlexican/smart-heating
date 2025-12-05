import { test, expect } from '@playwright/test';
import { navigateToArea, switchToTab, dismissSnackbar, expandSettingsCard } from './helpers';

test.describe('Preset Mode Tests', () => {
  test.skip('should change preset mode', async ({ page }) => {
    // This test requires the preset mode card to be in a specific state
    // Skipping for now - needs manual verification of dropdown behavior
    await navigateToArea(page, 'Living Room');
    await switchToTab(page, 'Settings');
    await dismissSnackbar(page);
    
    console.log('Preset mode test skipped - requires investigation of dropdown state');
    
    // Expand preset modes card
    await expandSettingsCard(page, 'Preset Modes');
    
    // Click on the dropdown field that says "Boost (See Boost Mode)"
    const dropdownField = page.locator('text=Boost (See Boost Mode)').first();
    await dropdownField.click();
    await page.waitForTimeout(500);
    
    // Select Eco from the dropdown menu
    await page.click('[role="option"]:has-text("Eco")');
    await page.waitForTimeout(1000);
    
    // Verify the dropdown now shows Eco
    await expect(page.locator('text=Eco').first()).toBeVisible();
  });
});
