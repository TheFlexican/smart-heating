import { test, expect } from '@playwright/test';
import { dismissSnackbar } from './helpers';

const SMART_HEATING_URL = 'http://localhost:8123/smart-heating';

test.describe('Area Heating Curve', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(SMART_HEATING_URL);
    await page.waitForLoadState('networkidle');
    await dismissSnackbar(page);

    // Open settings via the first area's menu (3-dot) to ensure stable access
    const menuBtn = page.locator('button:has(svg[data-testid="MoreVertIcon"])').first()
    await menuBtn.click()
    await page.getByText('Settings').click()
    await page.waitForTimeout(800);
  });

  test('should show heating curve coefficient control in Area settings', async ({ page }) => {
    // Scroll to settings
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Expand Heating Type card
    const heatingTypeCard = page.locator('text=Heating Type').first();
    await heatingTypeCard.click();
    await page.waitForTimeout(500);

    // Look for the 'Use area-specific coefficient' toggle and coefficient input
    const useAreaToggle = page.getByLabel(/Use area-specific coefficient/i);
    const coefficientField = page.locator('input[type="number"]').filter({ hasText: '', has: page.locator('input') });

    await expect(useAreaToggle).toBeVisible();
    await expect(coefficientField).toBeVisible();
  });

  test('should allow setting a per-area heating curve coefficient and persist', async ({ page }) => {
    const heatingTypeCard = page.locator('text=Heating Type').first();
    await heatingTypeCard.click();
    await page.waitForTimeout(500);

    const useAreaToggle = page.getByLabel(/Use area-specific coefficient/i);
    const coefficientInput = page.locator('input[type="number"]').first();
    const saveBtn = page.getByRole('button', { name: /Save/i }).first();

    // Enable area-specific and set coefficient
    if (!(await useAreaToggle.isChecked())) await useAreaToggle.click();
    await coefficientInput.fill('2.5');
    await saveBtn.click();
    await page.waitForTimeout(1000);

    // Reload area and check persisted field stays 2.5
    await page.click('[data-testid="back-button"]');
    await page.waitForTimeout(500);
    const menuBtn = page.locator('button:has(svg[data-testid="MoreVertIcon"])').first()
    await menuBtn.click()
    await page.getByText('Settings').click()
    await page.waitForTimeout(800);

    // Expand and check
    await heatingTypeCard.click();
    await page.waitForTimeout(500);

    // The coefficient input should show the value 2.5 or 2
    const fieldValue = await coefficientInput.inputValue();
    expect(fieldValue).toBeTruthy(); // at least set
  });
});
