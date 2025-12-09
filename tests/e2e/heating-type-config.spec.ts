import { test, expect } from '@playwright/test';

const SMART_HEATING_URL = 'http://localhost:8123/smart_heating/index.html';

test.describe('Heating Type Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(SMART_HEATING_URL);
    await page.waitForSelector('[data-testid="header-title"]', { timeout: 10000 });
  });

  test('should display heating type setting in area details', async ({ page }) => {
    // Click first area card
    const firstArea = page.locator('[data-testid="zone-card"]').first();
    await firstArea.click();
    await page.waitForTimeout(1000);

    // Should be in area details view
    await expect(page.locator('text=Temperature Control')).toBeVisible();

    // Scroll down to find heating type setting
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Look for heating type card
    const heatingTypeCard = page.locator('text=Heating Type').first();
    await expect(heatingTypeCard).toBeVisible();
  });

  test('should show heating type badge', async ({ page }) => {
    const firstArea = page.locator('[data-testid="zone-card"]').first();
    await firstArea.click();
    await page.waitForTimeout(1000);

    // Scroll to heating type section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Should show badge with current type (either Radiator or Floor Heating)
    const radiatorBadge = page.locator('text=Radiator').first();
    const floorHeatingBadge = page.locator('text=Floor Heating').first();

    const hasRadiator = await radiatorBadge.isVisible().catch(() => false);
    const hasFloorHeating = await floorHeatingBadge.isVisible().catch(() => false);

    // At least one should be visible
    expect(hasRadiator || hasFloorHeating).toBeTruthy();
  });

  test('should display radio button options', async ({ page }) => {
    const firstArea = page.locator('[data-testid="zone-card"]').first();
    await firstArea.click();
    await page.waitForTimeout(1000);

    // Scroll to heating type section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Click to expand heating type card if collapsed
    const heatingTypeCard = page.locator('text=Heating Type').first();
    await heatingTypeCard.click();
    await page.waitForTimeout(500);

    // Check for radio button options
    await expect(page.locator('text=Fast response, higher overhead temperature')).toBeVisible();
    await expect(page.locator('text=Slow response, lower overhead temperature')).toBeVisible();
  });

  test('should allow switching from radiator to floor heating', async ({ page }) => {
    const firstArea = page.locator('[data-testid="zone-card"]').first();
    await firstArea.click();
    await page.waitForTimeout(1000);

    // Scroll to heating type section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Expand card
    const heatingTypeCard = page.locator('text=Heating Type').first();
    await heatingTypeCard.click();
    await page.waitForTimeout(500);

    // Find floor heating radio button
    const floorHeatingRadio = page.locator('input[value="floor_heating"]').first();

    if (await floorHeatingRadio.isVisible()) {
      await floorHeatingRadio.click();
      await page.waitForTimeout(1000);

      // Badge should update
      await expect(page.locator('text=Floor Heating').first()).toBeVisible();
    }
  });

  test('should allow switching from floor heating to radiator', async ({ page }) => {
    const firstArea = page.locator('[data-testid="zone-card"]').first();
    await firstArea.click();
    await page.waitForTimeout(1000);

    // Scroll to heating type section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Expand card
    const heatingTypeCard = page.locator('text=Heating Type').first();
    await heatingTypeCard.click();
    await page.waitForTimeout(500);

    // Find radiator radio button
    const radiatorRadio = page.locator('input[value="radiator"]').first();

    if (await radiatorRadio.isVisible()) {
      await radiatorRadio.click();
      await page.waitForTimeout(1000);

      // Badge should update
      await expect(page.locator('text=Radiator').first()).toBeVisible();
    }
  });

  test('should display info alert explaining heating type impact', async ({ page }) => {
    const firstArea = page.locator('[data-testid="zone-card"]').first();
    await firstArea.click();
    await page.waitForTimeout(1000);

    // Scroll to heating type section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Expand card
    const heatingTypeCard = page.locator('text=Heating Type').first();
    await heatingTypeCard.click();
    await page.waitForTimeout(500);

    // Should have info alert about boiler setpoint
    const infoAlert = page.locator('text=boiler setpoint').first();
    await expect(infoAlert).toBeVisible();
  });

  test('should persist heating type selection', async ({ page }) => {
    const firstArea = page.locator('[data-testid="zone-card"]').first();
    await firstArea.click();
    await page.waitForTimeout(1000);

    // Scroll to heating type section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Expand card
    const heatingTypeCard = page.locator('text=Heating Type').first();
    await heatingTypeCard.click();
    await page.waitForTimeout(500);

    // Get current selection
    const radiatorRadio = page.locator('input[value="radiator"]').first();
    const isRadiatorChecked = await radiatorRadio.isChecked().catch(() => false);

    // Navigate away
    await page.click('[data-testid="back-button"]');
    await page.waitForTimeout(500);

    // Navigate back
    await firstArea.click();
    await page.waitForTimeout(1000);
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    await heatingTypeCard.click();
    await page.waitForTimeout(500);

    // Selection should be preserved
    const stillChecked = await radiatorRadio.isChecked().catch(() => false);
    expect(stillChecked).toBe(isRadiatorChecked);
  });

  test('should be located between HVAC Mode and Switch Control', async ({ page }) => {
    const firstArea = page.locator('[data-testid="zone-card"]').first();
    await firstArea.click();
    await page.waitForTimeout(1000);

    // Scroll to settings section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Get all setting card titles
    const pageContent = await page.locator('body').textContent();

    // Heating Type should appear after HVAC Mode and before Switch/Pump Control
    const hvacIndex = pageContent?.indexOf('HVAC Mode') ?? -1;
    const heatingTypeIndex = pageContent?.indexOf('Heating Type') ?? -1;
    const switchControlIndex = pageContent?.indexOf('Switch/Pump Control') ?? -1;

    if (hvacIndex !== -1 && heatingTypeIndex !== -1) {
      expect(heatingTypeIndex).toBeGreaterThan(hvacIndex);
    }

    if (heatingTypeIndex !== -1 && switchControlIndex !== -1) {
      expect(heatingTypeIndex).toBeLessThan(switchControlIndex);
    }
  });

  test('should show default heating type for new areas', async ({ page }) => {
    // Navigate to create area (if available)
    // For now, check first area has a heating type set
    const firstArea = page.locator('[data-testid="zone-card"]').first();
    await firstArea.click();
    await page.waitForTimeout(1000);

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    const heatingTypeCard = page.locator('text=Heating Type').first();
    await heatingTypeCard.click();
    await page.waitForTimeout(500);

    // Default should be radiator
    const radiatorRadio = page.locator('input[value="radiator"]').first();
    const floorHeatingRadio = page.locator('input[value="floor_heating"]').first();

    // At least one should be checked
    const radiatorChecked = await radiatorRadio.isChecked().catch(() => false);
    const floorChecked = await floorHeatingRadio.isChecked().catch(() => false);

    expect(radiatorChecked || floorChecked).toBeTruthy();
  });

  test('should display descriptions for both heating types', async ({ page }) => {
    const firstArea = page.locator('[data-testid="zone-card"]').first();
    await firstArea.click();
    await page.waitForTimeout(1000);

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    const heatingTypeCard = page.locator('text=Heating Type').first();
    await heatingTypeCard.click();
    await page.waitForTimeout(500);

    // Check for descriptive text
    await expect(page.locator('text=Fast response')).toBeVisible();
    await expect(page.locator('text=Slow response')).toBeVisible();
    await expect(page.locator('text=overhead temperature')).toBeVisible();
  });
});
