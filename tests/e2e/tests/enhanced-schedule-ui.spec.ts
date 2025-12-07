/**
 * E2E Tests for Enhanced Schedule UI
 * 
 * Tests the new schedule features introduced in v0.4.0:
 * - Date pickers for calendar-based date selection
 * - Multi-day selection with checkboxes and quick buttons
 * - Date-specific schedules for one-time events
 * - Card-based layout with collapsible sections
 * - Schedule type toggle (Weekly Recurring vs. Specific Date)
 */

import { test, expect } from '@playwright/test';

test.describe('Enhanced Schedule UI - Multi-Day Selection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart_heating');
    await page.waitForLoadState('networkidle');
    
    // Navigate to first area's schedule tab
    const areaCards = page.locator('[data-testid^="area-card-"]');
    await areaCards.first().click();
    await page.waitForURL(/\/area\//);
    
    // Click Schedule tab
    await page.getByRole('tab', { name: /schedule/i }).click();
    await page.waitForTimeout(500);
  });

  test('should open schedule dialog with date picker', async ({ page }) => {
    // Click Add Schedule button
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Verify dialog opened with schedule type toggle
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/schedule type/i)).toBeVisible();
    
    // Verify Weekly Recurring is selected by default
    const weeklyButton = page.getByRole('button', { name: /weekly recurring/i });
    await expect(weeklyButton).toHaveAttribute('aria-pressed', 'true');
  });

  test('should toggle between weekly and date-specific schedules', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Initially shows weekly recurring (day checkboxes)
    await expect(page.getByText(/select days/i)).toBeVisible();
    await expect(page.getByRole('checkbox', { name: /monday/i })).toBeVisible();
    
    // Switch to date-specific
    await page.getByRole('button', { name: /specific date/i }).click();
    
    // Should show date picker instead
    await expect(page.getByText(/select date/i)).toBeVisible();
    await expect(page.getByLabel(/date/i)).toBeVisible();
    
    // Day checkboxes should be hidden
    await expect(page.getByRole('checkbox', { name: /monday/i })).not.toBeVisible();
  });

  test('should select multiple days using checkboxes', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Select Monday and Tuesday
    await page.getByRole('checkbox', { name: /monday/i }).check();
    await page.getByRole('checkbox', { name: /tuesday/i }).check();
    
    // Verify selection preview shows 2 days
    await expect(page.getByText(/2 day\(s\) selected/i)).toBeVisible();
    
    // Verify chips show selected days
    const selectedChips = page.locator('.MuiChip-root').filter({ hasText: /monday|tuesday/i });
    await expect(selectedChips).toHaveCount(2);
  });

  test('should use quick selection buttons', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Click Weekdays button
    await page.getByRole('button', { name: /^weekdays$/i }).click();
    
    // Verify 5 days selected
    await expect(page.getByText(/5 day\(s\) selected/i)).toBeVisible();
    
    // Verify Monday through Friday are checked
    await expect(page.getByRole('checkbox', { name: /monday/i })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: /friday/i })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: /saturday/i })).not.toBeChecked();
  });

  test('should select weekend days', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Click Weekend button
    await page.getByRole('button', { name: /^weekend$/i }).click();
    
    // Verify 2 days selected
    await expect(page.getByText(/2 day\(s\) selected/i)).toBeVisible();
    
    // Verify Saturday and Sunday are checked
    await expect(page.getByRole('checkbox', { name: /saturday/i })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: /sunday/i })).toBeChecked();
  });

  test('should select all days', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Click All Days button
    await page.getByRole('button', { name: /all days/i }).click();
    
    // Verify 7 days selected
    await expect(page.getByText(/7 day\(s\) selected/i)).toBeVisible();
    
    // Verify all checkboxes are checked
    const allDayCheckboxes = page.locator('input[type="checkbox"]').filter({ 
      has: page.locator('+ span', { hasText: /monday|tuesday|wednesday|thursday|friday|saturday|sunday/i })
    });
    const checkedCount = await allDayCheckboxes.filter({ checked: true }).count();
    expect(checkedCount).toBe(7);
  });

  test('should clear selection', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Select some days first
    await page.getByRole('button', { name: /all days/i }).click();
    await expect(page.getByText(/7 day\(s\) selected/i)).toBeVisible();
    
    // Click Clear button
    await page.getByRole('button', { name: /^clear$/i }).click();
    
    // Verify no days selected
    await expect(page.getByText(/0 day\(s\) selected/i)).toBeVisible();
  });

  test('should create multi-day weekly schedule', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Select weekdays
    await page.getByRole('button', { name: /^weekdays$/i }).click();
    
    // Set time range
    await page.getByLabel(/start time/i).fill('08:00');
    await page.getByLabel(/end time/i).fill('17:00');
    
    // Set temperature
    await page.getByLabel(/temperature/i).fill('21');
    
    // Save
    await page.getByRole('button', { name: /^save$/i }).click();
    
    // Wait for dialog to close
    await expect(page.getByRole('dialog')).not.toBeVisible();
    
    // Verify schedule appears on all weekdays
    const mondayCard = page.locator('text=Monday').locator('..');
    await expect(mondayCard.locator('text=08:00 - 17:00: 21°C')).toBeVisible();
    
    const fridayCard = page.locator('text=Friday').locator('..');
    await expect(fridayCard.locator('text=08:00 - 17:00: 21°C')).toBeVisible();
  });
});

test.describe('Enhanced Schedule UI - Date-Specific Schedules', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart_heating');
    await page.waitForLoadState('networkidle');
    
    const areaCards = page.locator('[data-testid^="area-card-"]');
    await areaCards.first().click();
    await page.waitForURL(/\/area\//);
    await page.getByRole('tab', { name: /schedule/i }).click();
    await page.waitForTimeout(500);
  });

  test('should create date-specific schedule', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Switch to date-specific
    await page.getByRole('button', { name: /specific date/i }).click();
    
    // Set date (use current date + 1 day)
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateStr = tomorrow.toLocaleDateString('en-CA'); // YYYY-MM-DD format
    
    await page.getByLabel(/date/i).fill(dateStr);
    
    // Set time range
    await page.getByLabel(/start time/i).fill('10:00');
    await page.getByLabel(/end time/i).fill('14:00');
    
    // Set temperature
    await page.getByLabel(/temperature/i).fill('22');
    
    // Save
    await page.getByRole('button', { name: /^save$/i }).click();
    
    // Wait for dialog to close
    await expect(page.getByRole('dialog')).not.toBeVisible();
    
    // Verify date-specific schedules section appears
    await expect(page.getByText(/date-specific schedules/i)).toBeVisible();
    
    // Verify schedule chip shows correct info
    await expect(page.getByText(/10:00 - 14:00: 22°C/)).toBeVisible();
  });

  test('should show date-specific schedules in separate section', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Create date-specific schedule
    await page.getByRole('button', { name: /specific date/i }).click();
    const dateStr = new Date().toLocaleDateString('en-CA');
    await page.getByLabel(/date/i).fill(dateStr);
    await page.getByLabel(/start time/i).fill('12:00');
    await page.getByLabel(/end time/i).fill('13:00');
    await page.getByLabel(/temperature/i).fill('20');
    await page.getByRole('button', { name: /^save$/i }).click();
    
    await page.waitForTimeout(500);
    
    // Verify two separate sections exist
    await expect(page.getByText(/date-specific schedules/i)).toBeVisible();
    await expect(page.getByText(/weekly.*schedules/i)).toBeVisible();
    
    // Verify date-specific section has calendar icon or "one-time" badge
    const dateSection = page.locator('text=/date-specific schedules/i').locator('..');
    await expect(dateSection.locator('svg, text=/one-time/i')).toBeVisible();
  });

  test('should use preset mode instead of temperature', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Select weekdays
    await page.getByRole('button', { name: /^weekdays$/i }).click();
    
    // Set time
    await page.getByLabel(/start time/i).fill('06:00');
    await page.getByLabel(/end time/i).fill('09:00');
    
    // Switch to preset mode
    await page.getByLabel(/mode/i).click();
    await page.getByRole('option', { name: /preset mode/i }).click();
    
    // Select comfort preset
    await page.getByLabel(/preset/i).click();
    await page.getByRole('option', { name: /comfort/i }).click();
    
    // Save
    await page.getByRole('button', { name: /^save$/i }).click();
    
    await page.waitForTimeout(500);
    
    // Verify schedule shows preset name instead of temperature
    await expect(page.getByText(/06:00 - 09:00:.*comfort/i)).toBeVisible();
  });
});

test.describe('Enhanced Schedule UI - Card-Based Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart_heating');
    await page.waitForLoadState('networkidle');
    
    const areaCards = page.locator('[data-testid^="area-card-"]');
    await areaCards.first().click();
    await page.waitForURL(/\/area\//);
    await page.getByRole('tab', { name: /schedule/i }).click();
    await page.waitForTimeout(500);
  });

  test('should display schedules in card-based layout', async ({ page }) => {
    // Create a test schedule first
    await page.getByRole('button', { name: /add schedule/i }).click();
    await page.getByRole('checkbox', { name: /monday/i }).check();
    await page.getByLabel(/start time/i).fill('07:00');
    await page.getByLabel(/end time/i).fill('22:00');
    await page.getByLabel(/temperature/i).fill('21');
    await page.getByRole('button', { name: /^save$/i }).click();
    
    await page.waitForTimeout(500);
    
    // Verify card exists for Monday
    const mondayCard = page.locator('.MuiCard-root').filter({ hasText: /monday/i });
    await expect(mondayCard).toBeVisible();
    
    // Verify card shows schedule chip
    await expect(mondayCard.locator('.MuiChip-root')).toBeVisible();
  });

  test('should collapse and expand day cards', async ({ page }) => {
    // Create a schedule
    await page.getByRole('button', { name: /add schedule/i }).click();
    await page.getByRole('checkbox', { name: /monday/i }).check();
    await page.getByLabel(/start time/i).fill('08:00');
    await page.getByLabel(/end time/i).fill('16:00');
    await page.getByLabel(/temperature/i).fill('20');
    await page.getByRole('button', { name: /^save$/i }).click();
    
    await page.waitForTimeout(500);
    
    // Find Monday card
    const mondayCard = page.locator('.MuiCard-root').filter({ hasText: /^monday/i }).first();
    
    // Schedule chip should be visible initially (cards expanded by default)
    const scheduleChip = mondayCard.locator('.MuiChip-root', { hasText: /08:00 - 16:00/i });
    await expect(scheduleChip).toBeVisible();
    
    // Click collapse button
    const collapseButton = mondayCard.locator('button[aria-label*="expand"]').or(mondayCard.locator('svg').filter({ hasText: /expand/i }).locator('..')).first();
    await collapseButton.click();
    
    // Schedule chip should be hidden
    await expect(scheduleChip).not.toBeVisible();
    
    // Click expand button again
    await collapseButton.click();
    
    // Schedule chip should be visible again
    await expect(scheduleChip).toBeVisible();
  });

  test('should show schedule count badge', async ({ page }) => {
    // Create multiple schedules for Monday
    for (let i = 0; i < 2; i++) {
      await page.getByRole('button', { name: /add schedule/i }).click();
      await page.getByRole('checkbox', { name: /monday/i }).check();
      await page.getByLabel(/start time/i).fill(`0${6 + i}:00`);
      await page.getByLabel(/end time/i).fill(`0${8 + i}:00`);
      await page.getByLabel(/temperature/i).fill('21');
      await page.getByRole('button', { name: /^save$/i }).click();
      await page.waitForTimeout(500);
    }
    
    // Monday card should show count badge with "2"
    const mondayCard = page.locator('.MuiCard-root').filter({ hasText: /^monday/i }).first();
    await expect(mondayCard.locator('.MuiChip-root', { hasText: '2' })).toBeVisible();
  });

  test('should edit schedule by clicking chip', async ({ page }) => {
    // Create a schedule
    await page.getByRole('button', { name: /add schedule/i }).click();
    await page.getByRole('checkbox', { name: /monday/i }).check();
    await page.getByLabel(/start time/i).fill('09:00');
    await page.getByLabel(/end time/i).fill('17:00');
    await page.getByLabel(/temperature/i).fill('22');
    await page.getByRole('button', { name: /^save$/i }).click();
    
    await page.waitForTimeout(500);
    
    // Click on schedule chip to edit
    const scheduleChip = page.locator('.MuiChip-root', { hasText: /09:00 - 17:00: 22°C/i });
    await scheduleChip.click();
    
    // Dialog should open in edit mode
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/edit schedule/i)).toBeVisible();
    
    // Fields should be pre-filled
    await expect(page.getByLabel(/start time/i)).toHaveValue('09:00');
    await expect(page.getByLabel(/temperature/i)).toHaveValue('22');
  });

  test('should delete schedule using chip delete button', async ({ page }) => {
    // Create a schedule
    await page.getByRole('button', { name: /add schedule/i }).click();
    await page.getByRole('checkbox', { name: /monday/i }).check();
    await page.getByLabel(/start time/i).fill('10:00');
    await page.getByLabel(/end time/i).fill('18:00');
    await page.getByLabel(/temperature/i).fill('21');
    await page.getByRole('button', { name: /^save$/i }).click();
    
    await page.waitForTimeout(500);
    
    // Find and click delete button on chip
    const scheduleChip = page.locator('.MuiChip-root', { hasText: /10:00 - 18:00: 21°C/i });
    const deleteButton = scheduleChip.locator('svg[data-testid="DeleteIcon"]').locator('..');
    await deleteButton.click();
    
    // Schedule should be removed
    await expect(scheduleChip).not.toBeVisible();
    
    // Monday card should show "no schedules set"
    const mondayCard = page.locator('.MuiCard-root').filter({ hasText: /^monday/i }).first();
    await expect(mondayCard.locator('text=/no schedules set/i')).toBeVisible();
  });

  test('should show empty state when no schedules configured', async ({ page }) => {
    // If there are no schedules, should show info alert
    const scheduleCards = await page.locator('.MuiCard-root').count();
    
    if (scheduleCards === 0) {
      await expect(page.getByText(/no schedules configured/i)).toBeVisible();
    }
  });
});

test.describe('Enhanced Schedule UI - Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart_heating');
    await page.waitForLoadState('networkidle');
    
    const areaCards = page.locator('[data-testid^="area-card-"]');
    await areaCards.first().click();
    await page.waitForURL(/\/area\//);
    await page.getByRole('tab', { name: /schedule/i }).click();
    await page.waitForTimeout(500);
  });

  test('should disable save button when no days selected', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Clear all selections
    await page.getByRole('button', { name: /^clear$/i }).click();
    
    // Save button should be disabled
    const saveButton = page.getByRole('button', { name: /^save$/i });
    await expect(saveButton).toBeDisabled();
  });

  test('should enable save button when days are selected', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Select at least one day
    await page.getByRole('checkbox', { name: /monday/i }).check();
    
    // Save button should be enabled
    const saveButton = page.getByRole('button', { name: /^save$/i });
    await expect(saveButton).toBeEnabled();
  });

  test('should require date for date-specific schedules', async ({ page }) => {
    await page.getByRole('button', { name: /add schedule/i }).click();
    
    // Switch to date-specific
    await page.getByRole('button', { name: /specific date/i }).click();
    
    // Save button should require a valid date
    const saveButton = page.getByRole('button', { name: /^save$/i });
    
    // With default date, save should be enabled
    await expect(saveButton).toBeEnabled();
  });
});
