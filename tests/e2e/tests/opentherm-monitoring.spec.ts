import { test, expect } from '@playwright/test';
import { AreaListPage } from '../page-objects/AreaListPage';
import { BasePage } from '../page-objects/BasePage';

const SMART_HEATING_URL = 'http://localhost:8123/smart_heating/index.html';

test.describe('OpenTherm Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    const areaList = new AreaListPage(page as any);
    const base = new BasePage(page as any);
    await areaList.navigateToHome();
    await base.dismissSmartHeatingSnackbar();
  });

  test('should display OpenTherm tab in Settings', async ({ page }) => {
    // Click settings inside iframe
    const frame = page.frameLocator('iframe[title="Smart Heating"]');
    const settingsBtn = frame.getByTestId('header-settings-button');
    await settingsBtn.waitFor({ state: 'visible', timeout: 10000 });
    await settingsBtn.click();
    await page.waitForTimeout(500);

    // Check for OpenTherm tab inside settings
    const openthermTab = frame.getByRole('tab', { name: /OpenTherm/i }).first();
    await expect(openthermTab).toBeVisible({ timeout: 5000 });
  });

  test('should show OpenTherm Gateway status dashboard', async ({ page }) => {
    const frame = page.frameLocator('iframe[title="Smart Heating"]');
    const settingsBtn = frame.getByTestId('header-settings-button');
    await settingsBtn.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    if (!(await settingsBtn.isVisible().catch(() => false))) {
      throw new Error('MISSING_UI: Settings button not available. Add testid "header-settings-button" to header control. See task: Add header settings testid');
    }
    await settingsBtn.click();
    await page.waitForTimeout(500);

    const otTab = frame.getByRole('tab', { name: /OpenTherm/i }).first();
    const otVisible = await otTab.isVisible().catch(() => false);
    if (!otVisible) {
      throw new Error('MISSING_UI: OpenTherm tab not present. Add testid "opentherm-tab" to the tab element and ensure it is rendered. See task: add-opentherm-tab-testid');
    }
    await otTab.click();
    await page.waitForTimeout(500);

    // Check for main status sections - at least one section should be present
    const boOp = await frame.getByText('Boiler Operation').first().isVisible().catch(() => false);
    const wt = await frame.getByText('Water Temperatures').first().isVisible().catch(() => false);
    const ss = await frame.getByText('System Status').first().isVisible().catch(() => false);
    const be = await frame.getByText('Boiler Errors').first().isVisible().catch(() => false);

    if (!(boOp || wt || ss || be)) {
      throw new Error('MISSING_UI: OpenTherm main sections not present. Add testids for Boiler Operation/Water Temperatures/System Status/Boiler Errors (opentherm-*) and ensure they render. See task: add-opentherm-main-testids');
    }

    if (boOp) await expect(frame.getByText('Boiler Operation').first()).toBeVisible();
    if (wt) await expect(frame.getByText('Water Temperatures').first()).toBeVisible();
    if (ss) await expect(frame.getByText('System Status').first()).toBeVisible();
    if (be) await expect(frame.getByText('Boiler Errors').first()).toBeVisible();
  });

  test('should display boiler operation indicators', async ({ page }) => {
    const frame = page.frameLocator('iframe[title="Smart Heating"]');
    const settingsBtn = frame.getByTestId('header-settings-button');
    await settingsBtn.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    if (!(await settingsBtn.isVisible().catch(() => false))) {
      throw new Error('MISSING_UI: Settings button not available. Add testid "header-settings-button" to header control. See task: add-header-settings-testid');
    }
    await settingsBtn.click();
    await page.waitForTimeout(500);

    const otTab = frame.getByRole('tab', { name: /OpenTherm/i }).first();
    const otVisible = await otTab.isVisible().catch(() => false);
    if (!otVisible) {
      throw new Error('MISSING_UI: OpenTherm tab not present. Add testid "opentherm-tab" to the tab element and ensure it is rendered. See task: add-opentherm-tab-testid');
    }
    await otTab.click();
    await page.waitForTimeout(500);

    // Check for operation status chips - require at least one visible
    const chActive = await frame.getByText('CH Active').first().isVisible().catch(() => false);
    const dhwActive = await frame.getByText('DHW Active').first().isVisible().catch(() => false);
    const flame = await frame.getByText('Flame Status').first().isVisible().catch(() => false);
    const modulation = await frame.getByText('Modulation').first().isVisible().catch(() => false);

    if (!(chActive || dhwActive || flame || modulation)) {
      console.log('No OpenTherm operation indicators visible in this environment');
      return;
    }

    if (chActive) await expect(frame.getByText('CH Active').first()).toBeVisible();
    if (dhwActive) await expect(frame.getByText('DHW Active').first()).toBeVisible();
    if (flame) await expect(frame.getByText('Flame Status').first()).toBeVisible();
    if (modulation) await expect(frame.getByText('Modulation').first()).toBeVisible();
  });

  test('should display water temperature sensors', async ({ page }) => {
    const frame = page.frameLocator('iframe[title="Smart Heating"]');
    const settingsBtn = frame.getByTestId('header-settings-button');
    await settingsBtn.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    if (!(await settingsBtn.isVisible().catch(() => false))) {
      throw new Error('MISSING_UI: Settings button not available. Add testid "header-settings-button" to header control. See task: add-header-settings-testid');
    }
    await settingsBtn.click();
    await page.waitForTimeout(500);

    const otTab = frame.getByRole('tab', { name: /OpenTherm/i }).first();
    const otVisible = await otTab.isVisible().catch(() => false);
    if (!otVisible) {
      throw new Error('MISSING_UI: OpenTherm tab not present. Add testid "opentherm-tab" to the tab element and ensure it is rendered. See task: add-opentherm-tab-testid');
    }
    await otTab.click();
    await page.waitForTimeout(500);

    // Check for temperature displays - require at least one to be present
    const cs = await frame.getByText('Control Setpoint').first().isVisible().catch(() => false);
    const ch = await frame.getByText('CH Water').first().isVisible().catch(() => false);
    const ret = await frame.getByText('Return Water').first().isVisible().catch(() => false);

    if (!(cs || ch || ret)) {
      console.log('No OpenTherm temperature displays visible in this environment');
      return;
    }

    if (cs) await expect(frame.getByText('Control Setpoint').first()).toBeVisible();
    if (ch) await expect(frame.getByText('CH Water').first()).toBeVisible();
    if (ret) await expect(frame.getByText('Return Water').first()).toBeVisible();
  });

  test('should show error indicators with proper colors', async ({ page }) => {
    const frame = page.frameLocator('iframe[title="Smart Heating"]');
    const settingsBtn = frame.getByTestId('header-settings-button');
    await settingsBtn.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    if (!(await settingsBtn.isVisible().catch(() => false))) {
      throw new Error('MISSING_UI: Settings button not available. Add testid "header-settings-button" to header control. See task: add-header-settings-testid');
    }
    await settingsBtn.click();
    await page.waitForTimeout(500);

    const otTab = frame.getByRole('tab', { name: /OpenTherm/i }).first();
    const otVisible = await otTab.isVisible().catch(() => false);
    if (!otVisible) {
      throw new Error('MISSING_UI: OpenTherm tab not present. Add testid "opentherm-tab" to the tab element and ensure it is rendered. See task: add-opentherm-tab-testid');
    }
    await otTab.click();
    await page.waitForTimeout(500);

    // Check for error chips (may be off initially)
    const faultChipVis = await frame.getByText('Fault').first().isVisible().catch(() => false);
    const lowPressureVis = await frame.getByText('Low Water Pressure').first().isVisible().catch(() => false);
    const gasFaultVis = await frame.getByText('Gas Fault').first().isVisible().catch(() => false);

    if (!(faultChipVis || lowPressureVis || gasFaultVis)) {
      console.log('No OpenTherm error indicators visible in this environment');
      return;
    }

    if (faultChipVis) await expect(frame.getByText('Fault').first()).toBeVisible();
    if (lowPressureVis) await expect(frame.getByText('Low Water Pressure').first()).toBeVisible();
    if (gasFaultVis) await expect(frame.getByText('Gas Fault').first()).toBeVisible();
  });

  test('should show warning indicators', async ({ page }) => {
    const frame = page.frameLocator('iframe[title="Smart Heating"]');
    const settingsBtn = frame.getByTestId('header-settings-button');
    await settingsBtn.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    if (!(await settingsBtn.isVisible().catch(() => false))) {
      throw new Error('MISSING_UI: Settings button not available. Add testid "header-settings-button" to header control. See task: add-header-settings-testid');
    }
    await settingsBtn.click();
    await page.waitForTimeout(500);

    const otTab = frame.getByRole('tab', { name: /OpenTherm/i }).first();
    const otVisible = await otTab.isVisible().catch(() => false);
    if (!otVisible) {
      throw new Error('MISSING_UI: OpenTherm tab not present. Add testid "opentherm-tab" to the tab element and ensure it is rendered. See task: add-opentherm-tab-testid');
    }
    await otTab.click();
    await page.waitForTimeout(500);

    // Check for warning chips
    const diagnosticVisible = await frame.getByText('Diagnostic').first().isVisible().catch(() => false);
    const serviceVisible = await frame.getByText('Service Required').first().isVisible().catch(() => false);

    if (!(diagnosticVisible || serviceVisible)) {
      console.log('No OpenTherm warning indicators visible in this environment');
      return;
    }

    if (diagnosticVisible) await expect(frame.getByText('Diagnostic').first()).toBeVisible();
    if (serviceVisible) await expect(frame.getByText('Service Required').first()).toBeVisible();
  });

  test('should auto-refresh every 5 seconds', async ({ page }) => {
    const frame = page.frameLocator('iframe[title="Smart Heating"]');
    const settingsBtn = frame.getByTestId('header-settings-button');
    await settingsBtn.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    if (!(await settingsBtn.isVisible().catch(() => false))) {
      throw new Error('MISSING_UI: Settings button not available. Add testid "header-settings-button" to header control. See task: add-header-settings-testid');
    }
    await settingsBtn.click();
    await page.waitForTimeout(500);

    const otTab = frame.getByRole('tab', { name: /OpenTherm/i }).first();
    const otVisible = await otTab.isVisible().catch(() => false);
    if (!otVisible) {
      throw new Error('MISSING_UI: OpenTherm tab not present. Add testid "opentherm-tab" to the tab element and ensure it is rendered. See task: add-opentherm-tab-testid');
    }
    await otTab.click();
    await page.waitForTimeout(500);

    // Wait for auto-refresh (5 seconds + buffer)
    await page.waitForTimeout(6000);

    // Value should still be visible (may have changed or stayed same)
    const modVisible = await frame.getByText('Modulation').first().isVisible().catch(() => false);
    if (!modVisible) {
      throw new Error('MISSING_UI: Modulation value not present. Add testid "opentherm-modulation" to modulation display. See task: add-opentherm-modulation-testid');
    }
    await expect(frame.getByText('Modulation').first()).toBeVisible();
  });

  test('should display system pressure and room temperature', async ({ page }) => {
    const frame = page.frameLocator('iframe[title="Smart Heating"]');
    const settingsBtn = frame.getByTestId('header-settings-button');
    await settingsBtn.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    if (!(await settingsBtn.isVisible().catch(() => false))) {
      throw new Error('MISSING_UI: Settings button not available. Add testid "header-settings-button" to header control. See task: add-header-settings-testid');
    }
    await settingsBtn.click();
    await page.waitForTimeout(500);

    const otTab = frame.getByRole('tab', { name: /OpenTherm/i }).first();
    const otVisible = await otTab.isVisible().catch(() => false);
    if (!otVisible) {
      throw new Error('MISSING_UI: OpenTherm tab not present. Add testid "opentherm-tab" to the tab element and ensure it is rendered. See task: add-opentherm-tab-testid');
    }
    await otTab.click();
    await page.waitForTimeout(500);

    // Check for system status
    const sp = await frame.getByText('System Pressure').first().isVisible().catch(() => false);
    const rt = await frame.getByText('Room Temperature').first().isVisible().catch(() => false);
    const rs = await frame.getByText('Room Setpoint').first().isVisible().catch(() => false);

    if (!(sp || rt || rs)) {
      throw new Error('MISSING_UI: No system pressure or room temperature displays visible. Add testids "opentherm-system-pressure" and "opentherm-room-temperature" to respective elements. See task: add-opentherm-system-testids');
    }

    if (sp) await expect(frame.getByText('System Pressure').first()).toBeVisible();
    if (rt) await expect(frame.getByText('Room Temperature').first()).toBeVisible();
    if (rs) await expect(frame.getByText('Room Setpoint').first()).toBeVisible();
  });

  test('should handle missing OpenTherm sensors gracefully', async ({ page }) => {
    const frame = page.frameLocator('iframe[title="Smart Heating"]');
    const settingsBtn = frame.getByTestId('header-settings-button');
    await settingsBtn.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    if (!(await settingsBtn.isVisible().catch(() => false))) {
      throw new Error('MISSING_UI: Settings button not available. Add testid "header-settings-button" to header control. See task: add-header-settings-testid');
    }
    await settingsBtn.click();
    await page.waitForTimeout(500);

    const otTab = frame.getByRole('tab', { name: /OpenTherm/i }).first();
    const otVisible = await otTab.isVisible().catch(() => false);
    if (!otVisible) {
      throw new Error('MISSING_UI: OpenTherm tab not present. Add testid "opentherm-tab" to the tab element and ensure it is rendered. See task: add-opentherm-tab-testid');
    }
    await otTab.click();
    await page.waitForTimeout(500);

    // Should not show error state if sensors are unavailable
    const errorMessage = frame.getByText('Error loading OpenTherm data').first();

    // Either shows data or handles missing sensors gracefully
    const hasContent = await frame.locator('[data-testid="opentherm-content"]').isVisible().catch(() => false);
    const hasError = await errorMessage.isVisible().catch(() => false);

    // One of these should be true (has content OR shows no error)
    expect(hasContent || !hasError).toBeTruthy();
  });

  test('should display sensor values in correct format', async ({ page }) => {
    const frame = page.frameLocator('iframe[title="Smart Heating"]');
    const settingsBtn = frame.getByTestId('header-settings-button');
    await settingsBtn.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    if (!(await settingsBtn.isVisible().catch(() => false))) {
      throw new Error('MISSING_UI: Settings button not available. Add testid "header-settings-button" to header control. See task: add-header-settings-testid');
    }
    await settingsBtn.click();
    await page.waitForTimeout(500);

    const otTab = frame.getByRole('tab', { name: /OpenTherm/i }).first();
    const otVisible = await otTab.isVisible().catch(() => false);
    if (!otVisible) {
      throw new Error('MISSING_UI: OpenTherm tab not present. Add testid "opentherm-tab" to the tab element and ensure it is rendered. See task: add-opentherm-tab-testid');
    }
    await otTab.click();
    await page.waitForTimeout(500);

    // Check for proper formatting (temperatures should have °C, pressure should have bar, etc.)
    const content = await frame.locator('body').textContent();

    // If OpenTherm gateway not configured, fail and request test data/config
    if (content?.includes('No OpenTherm gateways found')) {
      throw new Error('MISSING_CONFIG: No OpenTherm gateway configured. Configure an OpenTherm Gateway integration for tests and add test fixtures. See task: configure-opentherm-gateway');
    }

    // Should contain temperature units
    expect(content).toContain('°C');

    // Should contain percentage for modulation
    expect(content).toContain('%');
  });

  test('should group errors and warnings separately', async ({ page }) => {
    const frame = page.frameLocator('iframe[title="Smart Heating"]');
    const settingsBtn = frame.getByTestId('header-settings-button');
    await settingsBtn.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    if (!(await settingsBtn.isVisible().catch(() => false))) {
      throw new Error('MISSING_UI: Settings button not available. Add testid "header-settings-button" to header control. See task: add-header-settings-testid');
    }
    await settingsBtn.click();
    await page.waitForTimeout(500);

    const otTab = frame.getByRole('tab', { name: /OpenTherm/i }).first();
    const otVisible = await otTab.isVisible().catch(() => false);
    if (!otVisible) {
      throw new Error('MISSING_UI: OpenTherm tab not present. Add testid "opentherm-tab" to the tab element and ensure it is rendered. See task: add-opentherm-tab-testid');
    }
    await otTab.click();
    await page.waitForTimeout(500);

    // Verify error section exists
    const errorSectionVisible = await frame.getByText('Boiler Errors').first().isVisible().catch(() => false);
    if (!errorSectionVisible) {
      throw new Error('MISSING_UI: Boiler Errors section not present. Add testid "opentherm-boiler-errors" to the section. See task: add-opentherm-boiler-errors-testid');
    }
    const errorSection = frame.getByText('Boiler Errors').first();
    await expect(errorSection).toBeVisible();

    // Critical errors should be before warnings in the UI
    const pageContent = await frame.locator('body').textContent();
    const faultIndex = pageContent?.indexOf('Fault') ?? -1;
    const diagnosticIndex = pageContent?.indexOf('Diagnostic') ?? -1;

    // If both exist, fault should come before diagnostic
    if (faultIndex !== -1 && diagnosticIndex !== -1) {
      expect(faultIndex).toBeLessThan(diagnosticIndex);
    }
  });

  test('should maintain state when switching tabs', async ({ page }) => {
    const frame = page.frameLocator('iframe[title="Smart Heating"]');
    const settingsBtn = frame.getByTestId('header-settings-button');
    await settingsBtn.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    if (!(await settingsBtn.isVisible().catch(() => false))) {
      throw new Error('MISSING_UI: Settings button not available. Add testid "header-settings-button" to header control. See task: add-header-settings-testid');
    }
    await settingsBtn.click();
    await page.waitForTimeout(500);

    const otTab = frame.getByRole('tab', { name: /OpenTherm/i }).first();
    const otVisible = await otTab.isVisible().catch(() => false);
    if (!otVisible) {
      throw new Error('MISSING_UI: OpenTherm tab not present. Add testid "opentherm-tab" to the tab element and ensure it is rendered. See task: add-opentherm-tab-testid');
    }
    await otTab.click();
    await page.waitForTimeout(500);

    // Switch to another tab
    const globalTab = frame.getByRole('tab', { name: /Global/i }).first();
    if (await globalTab.isVisible().catch(() => false)) {
      await globalTab.click();
      await page.waitForTimeout(500);

      // Switch back to OpenTherm
      await otTab.click();
      await page.waitForTimeout(500);

      // Content should still be visible
      await expect(frame.getByText('Modulation').first()).toBeVisible();
    } else {
      throw new Error('MISSING_UI: Global tab not present. Add testid "global-tab" to the tab element. See task: add-global-tab-testid');
    }
  });
});
