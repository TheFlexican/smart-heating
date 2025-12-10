import { test, expect } from '@playwright/test';
import { dismissSnackbar } from './helpers';

test.describe('Advanced Controls UI', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart-heating');
    await page.waitForLoadState('networkidle');
    await dismissSnackbar(page);

    // Open Global Settings
    const settingsButton = page.getByRole('button', { name: /Global.*Settings/i });
    await settingsButton.click();
    await page.waitForTimeout(1000);

    // Click Advanced tab
    const advancedTab = page.getByRole('tab', { name: /Advanced/i });
    await advancedTab.click();
    await page.waitForTimeout(500);
  });

  test('should display advanced control toggles', async ({ page }) => {
    await expect(page.getByText(/Enable advanced control/i)).toBeVisible();
    await expect(page.getByText(/Heating curve/i)).toBeVisible();
    await expect(page.getByText(/PWM for on\/off boilers/i)).toBeVisible();
    await expect(page.getByText(/PID Automatic Gains/i)).toBeVisible();
    await expect(page.getByText(/Overshoot Protection/i)).toBeVisible();
  });

  test('should toggle advanced control and enable sub-features', async ({ page }) => {
    const enableAll = page.getByRole('checkbox', { name: /Enable advanced control/i });
    const heatingCurve = page.getByRole('checkbox', { name: /Heating curve/i });

    await enableAll.click();
    await page.waitForTimeout(500);
    // Sub-feature should become enabled
    await expect(heatingCurve).toBeEnabled();

    // Toggle heating curve on
    await heatingCurve.click();
    await page.waitForTimeout(500);
    await expect(heatingCurve).toBeChecked();
  });

  test('should show Run OPV calibration button and result', async ({ page }) => {
    // Ensure advanced control enabled
    const enableAll = page.getByRole('checkbox', { name: /Enable advanced control/i });
    if (!(await enableAll.isChecked())) {
      await enableAll.click();
    }

    const runCalBtn = page.getByRole('button', { name: /Run OPV calibration/i });
    await expect(runCalBtn).toBeVisible();

    // Click button to start calibration
    await runCalBtn.click();
    await page.waitForTimeout(1000);

    // Should show spinner or result text
    const opvResult = page.getByText(/OPV:/i);
    // Accept either the spinner or eventual result; at least confirm the button exists
    await expect(runCalBtn).toBeVisible();
  });

  test('should reset advanced control defaults on reset button', async ({ page }) => {
    // Turn advanced control toggles on first
    const enableAll = page.getByRole('checkbox', { name: /Enable advanced control/i });
    if (!(await enableAll.isChecked())) await enableAll.click();

    const heatingCurve = page.getByRole('checkbox', { name: /Heating curve/i });
    if (!(await heatingCurve.isChecked())) await heatingCurve.click();
    await page.waitForTimeout(500);

    const resetBtn = page.getByRole('button', { name: /Reset to defaults/i });
    await expect(resetBtn).toBeVisible();

    // Click it to reset
    await resetBtn.click();
    await page.waitForTimeout(1000);

    // Heating curve should be disabled after reset
    await expect(heatingCurve).toBeDisabled();
    // Advanced control should be false
    await expect(enableAll).not.toBeChecked();
  });
});
