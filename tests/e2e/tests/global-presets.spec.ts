import { test, expect } from '@playwright/test';
import { navigateToArea, dismissSnackbar } from './helpers';

test.describe('Global Preset Temperatures', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart-heating');
    await page.waitForLoadState('networkidle');
    await dismissSnackbar(page);
  });

  test('should display preset configuration in area detail settings', async ({ page }) => {
    // Navigate to an area
    await navigateToArea(page, 'Woonkamer');
    
    // Switch to Settings tab
    const settingsTab = page.locator('button[role="tab"]').filter({ hasText: /Settings/i });
    await settingsTab.click();
    await page.waitForTimeout(500);
    
    // Look for Preset Temperature Configuration text
    const presetConfigText = page.getByText(/Preset Temperature Configuration/i);
    await expect(presetConfigText).toBeVisible({ timeout: 5000 });
  });

  test('should show toggle switches for preset modes', async ({ page }) => {
    await navigateToArea(page, 'Woonkamer');
    
    // Switch to Settings tab
    const settingsTab = page.locator('button[role="tab"]').filter({ hasText: /Settings/i });
    await settingsTab.click();
    await page.waitForTimeout(500);
    
    // Find and click Preset Temperature Configuration to expand
    const presetCard = page.getByText(/Preset Temperature Configuration/i);
    await presetCard.click();
    await page.waitForTimeout(500);
    
    // Check for preset toggle labels (at least Home should be visible)
    const homePresetToggle = page.getByText(/Home.*Use Global/i);
    await expect(homePresetToggle).toBeVisible({ timeout: 5000 });
  });

  test('should toggle between global and custom temperatures', async ({ page }) => {
    await navigateToArea(page, 'Woonkamer');
    
    // Switch to Settings tab
    const settingsTab = page.locator('button[role="tab"]').filter({ hasText: /Settings/i });
    await settingsTab.click();
    await page.waitForTimeout(500);
    
    // Expand Preset Temperature Configuration
    const presetCard = page.getByText(/Preset Temperature Configuration/i);
    await presetCard.click();
    await page.waitForTimeout(500);
    
    // Find the Home preset toggle area
    const homePresetSection = page.locator('text=Home').locator('..').locator('..');
    
    // Find the switch input within this section
    const toggleSwitch = homePresetSection.locator('input[type="checkbox"]').first();
    
    // Get initial state
    const initialState = await toggleSwitch.isChecked();
    
    // Click to toggle
    await toggleSwitch.click();
    await page.waitForTimeout(1000); // Wait for API call and WebSocket update
    
    // Verify state changed
    const newState = await toggleSwitch.isChecked();
    expect(newState).not.toBe(initialState);
    
    // Toggle back
    await toggleSwitch.click();
    await page.waitForTimeout(1000);
    
    // Verify returned to original state
    const finalState = await toggleSwitch.isChecked();
    expect(finalState).toBe(initialState);
  });

  test('should display temperature values for presets', async ({ page }) => {
    await navigateToArea(page, 'Woonkamer');
    
    // Switch to Settings tab
    const settingsTab = page.locator('button[role="tab"]').filter({ hasText: /Settings/i });
    await settingsTab.click();
    await page.waitForTimeout(500);
    
    // Expand Preset Temperature Configuration
    const presetCard = page.getByText(/Preset Temperature Configuration/i);
    await presetCard.click();
    await page.waitForTimeout(500);
    
    // Check that temperature values are shown (e.g., "Using global setting: 19.2°C")
    const tempPattern = page.getByText(/\d+(\.\d+)?°C/);
    await expect(tempPattern.first()).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Presence Sensor Simplified UI', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart-heating');
    await page.waitForLoadState('networkidle');
    await dismissSnackbar(page);
  });

  test('should show simplified presence sensor dialog without temperature controls', async ({ page }) => {
    await navigateToArea(page, 'Woonkamer');
    
    // Switch to Settings tab
    const settingsTab = page.locator('button[role="tab"]').filter({ hasText: /Settings/i });
    await settingsTab.click();
    await page.waitForTimeout(500);
    
    // Look for and expand Presence Sensors section
    const presenceSensorsCard = page.getByText(/Presence Sensors/i).first();
    await presenceSensorsCard.click();
    await page.waitForTimeout(500);
    
    // Click Add Presence Sensor button
    const addButton = page.locator('button').filter({ hasText: /Add Presence Sensor/i });
    await addButton.click();
    await page.waitForTimeout(500);
    
    // Verify dialog opened with simplified content
    await expect(page.getByText(/Preset Mode Control/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/switches to.*Away.*preset/i)).toBeVisible({ timeout: 5000 });
    
    // Verify old temperature adjustment controls are NOT present
    await expect(page.getByText(/Action When Away/i)).not.toBeVisible();
    await expect(page.getByText(/Temperature Drop/i)).not.toBeVisible();
    await expect(page.getByText(/Temperature Boost/i)).not.toBeVisible();
    
    // Close dialog
    await page.locator('button').filter({ hasText: /Cancel/i }).click();
  });

  test('should display simplified description for existing presence sensors', async ({ page }) => {
    await navigateToArea(page, 'Woonkamer');
    
    // Switch to Settings tab
    const settingsTab = page.locator('button[role="tab"]').filter({ hasText: /Settings/i });
    await settingsTab.click();
    await page.waitForTimeout(500);
    
    // Expand Presence Sensors section
    const presenceSensorsCard = page.getByText(/Presence Sensors/i).first();
    await presenceSensorsCard.click();
    await page.waitForTimeout(500);
    
    // Check if there are any presence sensors listed
    const sensorDescription = page.getByText(/Controls preset mode/i);
    const count = await sensorDescription.count();
    
    if (count > 0) {
      // If sensors exist, verify new description is shown
      await expect(sensorDescription.first()).toBeVisible();
      
      // Verify old descriptions are NOT shown
      await expect(page.getByText(/When away:/i)).not.toBeVisible();
      await expect(page.getByText(/When home:/i)).not.toBeVisible();
      await expect(page.getByText(/Reduce by.*°C/i)).not.toBeVisible();
      await expect(page.getByText(/Increase by.*°C/i)).not.toBeVisible();
    }
  });
});

test.describe('Manual Override with Presets', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart-heating');
    await page.waitForLoadState('networkidle');
    await dismissSnackbar(page);
  });

  test('should show correct temperature when switching from manual to preset mode', async ({ page }) => {
    await navigateToArea(page, 'Woonkamer');
    await page.waitForTimeout(500);
    
    // Look for the manual override toggle on the main overview
    const manualToggle = page.locator('text=/Using Preset Mode|Manual Mode/i').locator('..').locator('input[type="checkbox"]').first();
    
    if (await manualToggle.isVisible()) {
      // Get current state
      const isPresetMode = await manualToggle.isChecked();
      
      // If in manual mode, switch to preset mode
      if (!isPresetMode) {
        await manualToggle.click();
        await page.waitForTimeout(1000);
        
        // Verify temperature display updated
        const targetTemp = page.getByText(/Target Temperature/i);
        await expect(targetTemp).toBeVisible();
      }
    }
  });
});

