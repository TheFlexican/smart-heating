import { test, expect } from '@playwright/test';
import { login, navigateToSmartHeating, navigateToArea, switchToTab, dismissSnackbar } from './helpers';

test.describe('Temperature Control Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    await login(page);
    await navigateToSmartHeating(page);
  });

  test('should adjust target temperature', async ({ page }) => {
    await navigateToArea(page, 'Living Room');
    await dismissSnackbar(page);
    
    // Enable area first
    const areaToggle = page.locator('input[type="checkbox"]').last();
    const isEnabled = await areaToggle.isChecked();
    if (!isEnabled) {
      await areaToggle.click();
      await page.waitForTimeout(1000);
    }
    
    // Find temperature slider
    const tempSlider = page.locator('input[type="range"]').first();
    await expect(tempSlider).toBeVisible();
    
    // Set to 22 degrees
    await tempSlider.fill('22');
    await page.waitForTimeout(1000);
    
    // Verify slider value changed
    const newTemp = await tempSlider.getAttribute('value');
    expect(newTemp).toBe('22');
  });

  test('should enable/disable area', async ({ page }) => {
    await navigateToArea(page, 'Living Room');
    await dismissSnackbar(page);
    
    // Find the enable/disable switch
    const toggleSwitch = page.locator('input[type="checkbox"]').first();
    const initialState = await toggleSwitch.isChecked();
    
    // Toggle the area
    await toggleSwitch.click();
    await page.waitForTimeout(1000);
    
    // Verify state changed
    const newState = await toggleSwitch.isChecked();
    expect(newState).toBe(!initialState);
    
    // Toggle back
    await toggleSwitch.click();
    await page.waitForTimeout(1000);
  });

  test('should sync temperature when changed externally via WebSocket', async ({ page }) => {
    // We're already on main overview from beforeEach
    
    // Find Living Room/Woonkamer card and get initial temperature
    const livingRoomCard = page.locator('.MuiCard-root:has-text("Living Room"), .MuiCard-root:has-text("Woonkamer")').first();
    await expect(livingRoomCard).toBeVisible();
    
    const initialTempDisplay = livingRoomCard.locator('.MuiTypography-h5').filter({ hasText: /\d+°C/ }).first();
    const initialTemp = await initialTempDisplay.textContent();
    console.log(`Initial temperature display: ${initialTemp}`);
    
    // Navigate to area detail and change temperature
    await navigateToArea(page, 'Living Room');
    await dismissSnackbar(page);
    
    const tempSlider = page.locator('input[type="range"]').first();
    await tempSlider.fill('23');
    await page.waitForTimeout(2000); // Wait for WebSocket update
    
    // Go back to main overview using helper
    await navigateToSmartHeating(page);
    await page.waitForTimeout(2000); // Wait for WebSocket reconnect and data sync
    
    // Verify card updated with new temperature
    const updatedCard = page.locator('.MuiCard-root:has-text("Living Room"), .MuiCard-root:has-text("Woonkamer")').first();
    await expect(updatedCard).toBeVisible();
    
    const updatedTempDisplay = updatedCard.locator('.MuiTypography-h5').filter({ hasText: /\d+°C/ }).first();
    const updatedTemp = await updatedTempDisplay.textContent();
    console.log(`Updated temperature display: ${updatedTemp}`);
    
    // Check if temperature is 23°C
    expect(updatedTemp).toContain('23');
    
    console.log('✓ Temperature display synced correctly after external change');
  });
});
