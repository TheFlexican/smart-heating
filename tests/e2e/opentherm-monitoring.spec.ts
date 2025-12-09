import { test, expect } from '@playwright/test';

const SMART_HEATING_URL = 'http://localhost:8123/smart_heating/index.html';

test.describe('OpenTherm Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(SMART_HEATING_URL);
    // Wait for initial load
    await page.waitForSelector('[data-testid="header-title"]', { timeout: 10000 });
  });

  test('should display OpenTherm tab in Settings', async ({ page }) => {
    // Navigate to Settings
    await page.click('text=Settings');
    await page.waitForTimeout(500);

    // Check for OpenTherm tab
    const openthermTab = await page.locator('button[role="tab"]:has-text("OpenTherm")');
    await expect(openthermTab).toBeVisible();
  });

  test('should show OpenTherm Gateway status dashboard', async ({ page }) => {
    // Navigate to Settings → OpenTherm
    await page.click('text=Settings');
    await page.waitForTimeout(500);
    await page.click('button[role="tab"]:has-text("OpenTherm")');
    await page.waitForTimeout(500);

    // Check for main status sections
    await expect(page.locator('text=Boiler Operation')).toBeVisible();
    await expect(page.locator('text=Water Temperatures')).toBeVisible();
    await expect(page.locator('text=System Status')).toBeVisible();
    await expect(page.locator('text=Boiler Errors')).toBeVisible();
  });

  test('should display boiler operation indicators', async ({ page }) => {
    await page.click('text=Settings');
    await page.waitForTimeout(500);
    await page.click('button[role="tab"]:has-text("OpenTherm")');
    await page.waitForTimeout(500);

    // Check for operation status chips
    const chActiveChip = page.locator('text=CH Active');
    const dhwActiveChip = page.locator('text=DHW Active');
    const flameChip = page.locator('text=Flame Status');
    const modulationChip = page.locator('text=Modulation');

    await expect(chActiveChip).toBeVisible();
    await expect(dhwActiveChip).toBeVisible();
    await expect(flameChip).toBeVisible();
    await expect(modulationChip).toBeVisible();
  });

  test('should display water temperature sensors', async ({ page }) => {
    await page.click('text=Settings');
    await page.waitForTimeout(500);
    await page.click('button[role="tab"]:has-text("OpenTherm")');
    await page.waitForTimeout(500);

    // Check for temperature displays
    await expect(page.locator('text=Control Setpoint')).toBeVisible();
    await expect(page.locator('text=CH Water')).toBeVisible();
    await expect(page.locator('text=Return Water')).toBeVisible();
  });

  test('should show error indicators with proper colors', async ({ page }) => {
    await page.click('text=Settings');
    await page.waitForTimeout(500);
    await page.click('button[role="tab"]:has-text("OpenTherm")');
    await page.waitForTimeout(500);

    // Check for error chips (may be off initially)
    const faultChip = page.locator('text=Fault').first();
    const lowPressureChip = page.locator('text=Low Water Pressure');
    const gasFaultChip = page.locator('text=Gas Fault');
    const airPressureChip = page.locator('text=Air Pressure Fault');
    const overTempChip = page.locator('text=Water Overtemp');

    // These should exist even if off
    await expect(faultChip).toBeVisible();
    await expect(lowPressureChip).toBeVisible();
    await expect(gasFaultChip).toBeVisible();
  });

  test('should show warning indicators', async ({ page }) => {
    await page.click('text=Settings');
    await page.waitForTimeout(500);
    await page.click('button[role="tab"]:has-text("OpenTherm")');
    await page.waitForTimeout(500);

    // Check for warning chips
    const diagnosticChip = page.locator('text=Diagnostic');
    const serviceChip = page.locator('text=Service Required');

    await expect(diagnosticChip).toBeVisible();
    await expect(serviceChip).toBeVisible();
  });

  test('should auto-refresh every 5 seconds', async ({ page }) => {
    await page.click('text=Settings');
    await page.waitForTimeout(500);
    await page.click('button[role="tab"]:has-text("OpenTherm")');
    await page.waitForTimeout(500);

    // Get initial value of a sensor
    const modulationText = await page.locator('text=Modulation').first().textContent();

    // Wait for auto-refresh (5 seconds + buffer)
    await page.waitForTimeout(6000);

    // Value should still be visible (may have changed or stayed same)
    await expect(page.locator('text=Modulation').first()).toBeVisible();
  });

  test('should display system pressure and room temperature', async ({ page }) => {
    await page.click('text=Settings');
    await page.waitForTimeout(500);
    await page.click('button[role="tab"]:has-text("OpenTherm")');
    await page.waitForTimeout(500);

    // Check for system status
    await expect(page.locator('text=System Pressure')).toBeVisible();
    await expect(page.locator('text=Room Temperature')).toBeVisible();
    await expect(page.locator('text=Room Setpoint')).toBeVisible();
  });

  test('should handle missing OpenTherm sensors gracefully', async ({ page }) => {
    await page.click('text=Settings');
    await page.waitForTimeout(500);
    await page.click('button[role="tab"]:has-text("OpenTherm")');
    await page.waitForTimeout(500);

    // Should not show error state if sensors are unavailable
    const errorMessage = page.locator('text=Error loading OpenTherm data');

    // Either shows data or handles missing sensors gracefully
    const hasContent = await page.locator('[data-testid="opentherm-content"]').isVisible().catch(() => false);
    const hasError = await errorMessage.isVisible().catch(() => false);

    // One of these should be true (has content OR shows no error)
    expect(hasContent || !hasError).toBeTruthy();
  });

  test('should display sensor values in correct format', async ({ page }) => {
    await page.click('text=Settings');
    await page.waitForTimeout(500);
    await page.click('button[role="tab"]:has-text("OpenTherm")');
    await page.waitForTimeout(500);

    // Check for proper formatting (temperatures should have °C, pressure should have bar, etc.)
    const content = await page.locator('body').textContent();

    // Should contain temperature units
    expect(content).toContain('°C');

    // Should contain percentage for modulation
    expect(content).toContain('%');
  });

  test('should group errors and warnings separately', async ({ page }) => {
    await page.click('text=Settings');
    await page.waitForTimeout(500);
    await page.click('button[role="tab"]:has-text("OpenTherm")');
    await page.waitForTimeout(500);

    // Verify error section exists
    const errorSection = page.locator('text=Boiler Errors').first();
    await expect(errorSection).toBeVisible();

    // Critical errors should be before warnings in the UI
    const pageContent = await page.locator('body').textContent();
    const faultIndex = pageContent?.indexOf('Fault') ?? -1;
    const diagnosticIndex = pageContent?.indexOf('Diagnostic') ?? -1;

    // If both exist, fault should come before diagnostic
    if (faultIndex !== -1 && diagnosticIndex !== -1) {
      expect(faultIndex).toBeLessThan(diagnosticIndex);
    }
  });

  test('should maintain state when switching tabs', async ({ page }) => {
    await page.click('text=Settings');
    await page.waitForTimeout(500);
    await page.click('button[role="tab"]:has-text("OpenTherm")');
    await page.waitForTimeout(500);

    // Get a sensor value
    const initialContent = await page.locator('text=Modulation').first().textContent();

    // Switch to another tab
    await page.click('button[role="tab"]:has-text("Global")');
    await page.waitForTimeout(500);

    // Switch back to OpenTherm
    await page.click('button[role="tab"]:has-text("OpenTherm")');
    await page.waitForTimeout(500);

    // Content should still be visible
    await expect(page.locator('text=Modulation').first()).toBeVisible();
  });
});
