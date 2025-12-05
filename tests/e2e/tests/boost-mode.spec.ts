import { test, expect } from '@playwright/test';
import { navigateToArea } from './helpers';

test.describe('Boost Mode Tests', () => {
  test('should activate boost mode', async ({ page }) => {
    await navigateToArea(page, 'Living Room');
    await page.waitForTimeout(2000);
    
    // Switch to Settings tab
    await page.getByRole('tab', { name: 'Settings' }).click();
    await page.waitForTimeout(500);
    
    // Open Boost Mode card
    await page.getByText('Boost Mode').click();
    await page.waitForTimeout(600);
    
    // Check if boost is already active (from previous test)
    const cancelButton = page.getByRole('button', { name: 'Cancel Boost Mode' });
    const isAlreadyActive = await cancelButton.isVisible().catch(() => false);

    if (!isAlreadyActive) {
      // Activate boost mode first
      await page.getByRole('spinbutton', { name: 'Boost Temperature' }).fill('25');
      await page.getByRole('spinbutton', { name: 'Duration (minutes)' }).fill('60');
      await page.getByRole('button', { name: 'Activate Boost' }).click();
      await page.waitForTimeout(2000);
    }
    
    // Wait for backend API call and state update
    await page.waitForTimeout(5000);
    
    // Verify boost mode is active - look for ACTIVE badge
    const activeBadge = page.locator('.MuiChip-label:has-text("ACTIVE")');
    await expect(activeBadge.first()).toBeVisible({ timeout: 50000 });
  });

  test('should cancel boost mode', async ({ page }) => {
    await navigateToArea(page, 'Living Room');
    await page.waitForTimeout(2000);
    
    // Switch to Settings tab
    await page.getByRole('tab', { name: 'Settings' }).click();
    await page.waitForTimeout(500);
    
    // Open Boost Mode card
    await page.getByText('Boost Mode').click();
    await page.waitForTimeout(600);
    
    // Check if boost is already active (from previous test)
    const cancelButton = page.getByRole('button', { name: 'Cancel Boost Mode' });
    const isAlreadyActive = await cancelButton.isVisible().catch(() => false);
    
    if (!isAlreadyActive) {
      // Activate boost mode first
      await page.getByRole('spinbutton', { name: 'Boost Temperature' }).fill('25');
      await page.getByRole('spinbutton', { name: 'Duration (minutes)' }).fill('60');
      await page.getByRole('button', { name: 'Activate Boost' }).click();
      await page.waitForTimeout(2000);
    }
    
    // Now cancel it
    await page.getByRole('button', { name: 'Cancel Boost Mode' }).click();
    await page.waitForTimeout(1000);
    
    // Verify boost is cancelled - ACTIVE badge should disappear
    const activeBadge = page.locator('.MuiChip-label:has-text("ACTIVE")').first();
    await expect(activeBadge).not.toBeVisible();
  });

  test('boost mode should affect heating state', async ({ page }) => {
    await navigateToArea(page, 'Living Room');
    
    // Switch to Settings tab
    await page.getByRole('tab', { name: 'Settings' }).click();
    await page.waitForTimeout(500);
    
    // Open Boost Mode card and activate with high temperature
    await page.getByText('Boost Mode').click();
    await page.waitForTimeout(600);
    
    // Check if boost is already active (from previous test)
    const cancelButton = page.getByRole('button', { name: 'Cancel Boost Mode' });
    const isAlreadyActive = await cancelButton.isVisible().catch(() => false);
    
    if (!isAlreadyActive) {
      // Activate boost mode first
      await page.getByRole('spinbutton', { name: 'Boost Temperature' }).fill('25');
      await page.getByRole('spinbutton', { name: 'Duration (minutes)' }).fill('60');
      await page.getByRole('button', { name: 'Activate Boost' }).click();
      await page.waitForTimeout(2000);
    }
    
    // Wait for climate control cycle
    await page.waitForTimeout(5000);
    
    // Check heating status on Overview tab
    await page.getByRole('tab', { name: 'Overview' }).click();
    await page.waitForTimeout(500);
    
    // Look for the HEATING chip/badge in the area header (not in device list)
    const heatingBadge = page.locator('.MuiChip-label:has-text("HEATING")').first();
    await expect(heatingBadge).toBeVisible({ timeout: 15000 });
  });
});
