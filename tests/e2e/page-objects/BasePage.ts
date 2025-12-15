import { Page, Response } from '@playwright/test';

/**
 * Base page object class with common functionality for all pages
 */
export class BasePage {
  constructor(public page: Page) { }

  /**
   * Dismiss any visible snackbar notifications
   */
  async dismissSnackbar(): Promise<void> {
    const closeButton = this.page.locator('[aria-label="Close"]').first();
    const isVisible = await closeButton.isVisible({ timeout: 1000 }).catch(() => false);

    if (isVisible) {
      await closeButton.click();
      // Wait for snackbar to disappear
      await this.page.waitForTimeout(300);
    }
  }

  /**
   * Dismiss any snackbars inside the Smart Heating iframe (e.g., WebSocket disconnect)
   */
  async dismissSmartHeatingSnackbar(): Promise<void> {
    const frame = this.getSmartHeatingFrame();
    for (let i = 0; i < 3; i++) {
      const closeButton = frame.locator('[aria-label="Close"]').first();
      if (await closeButton.isVisible({ timeout: 1000 }).catch(() => false)) {
        await closeButton.click({ force: true });
        await this.page.waitForTimeout(300);
      } else {
        break;
      }
    }
  }

  /**
   * Wait for an API response matching the given URL pattern
   */
  async waitForApiResponse(urlPattern: string | RegExp): Promise<Response> {
    return await this.page.waitForResponse(urlPattern);
  }

  /**
   * Navigate to the Smart Heating home page
   */
  async navigateToHome(): Promise<void> {
    // Navigate to Home Assistant - will likely show login page
    await this.page.goto('/', { timeout: 30000 });


    // CRITICAL: Wait for Home Assistant's automatic page refresh after JS files load
    // This can take 5-10 seconds in a fresh Chrome instance without cache
    console.log('[BasePage] Waiting 10s for HA automatic refresh (JS files loading)...');
    await this.page.waitForTimeout(6000)

    // Check if login form is present
    const hasLoginForm = await this.page.locator('input[name="username"]').isVisible({ timeout: 3000 }).catch(() => false);



    if (hasLoginForm) {
      console.log('[BasePage] Login form detected, logging in...');
      // Fill in credentials
      await this.page.getByRole('textbox', { name: 'Username*' }).click();
      await this.page.getByRole('textbox', { name: 'Username*' }).fill('test');
      await this.page.getByRole('textbox', { name: 'Password*' }).click();
      await this.page.getByRole('textbox', { name: 'Password*' }).fill('test');
      await this.page.getByRole('button', { name: 'Log in' }).click();

      // Wait for sidebar to appear (indicates successful login)
      await this.page.waitForSelector('text=Smart Heating', { state: 'visible', timeout: 100000 });
      console.log('[BasePage] Login completed');
    } else {
      console.log('[BasePage] Already logged in');
    }

    // Verify we're on a proper HA page (not auth page)
    const currentUrl = this.page.url();
    console.log('[BasePage] Current URL before clicking Smart Heating:', currentUrl);

    // Click Smart Heating in sidebar instead of using goto() to preserve session
    console.log('[BasePage] Clicking Smart Heating in sidebar...');
    await this.page.locator('text=Smart Heating').first().click();
    await this.page.waitForTimeout(3000);
    console.log('[BasePage] Now at:', this.page.url());

    // Wait for iframe to be present
    console.log('[BasePage] Waiting for iframe...');
    await this.page.waitForSelector('iframe[title="Smart Heating"]', { state: 'attached', timeout: 15000 });
    await this.page.waitForTimeout(1000);
    console.log('[BasePage] Iframe found!');

    // Dismiss any snackbars that might block interactions (e.g., WebSocket disconnect)
    try {
      await this.dismissSmartHeatingSnackbar();
    } catch (e) {
      console.log('[BasePage] Warning: dismissSmartHeatingSnackbar failed', e);
    }
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get the Smart Heating iframe frame locator
   */
  protected getSmartHeatingFrame() {
    return this.page.frameLocator('iframe[title="Smart Heating"]');
  }

  /**
   * Check if an element is visible
   */
  async isVisible(selector: string, timeout = 5000): Promise<boolean> {
    return await this.page.locator(selector).isVisible({ timeout }).catch(() => false);
  }

  /**
   * Get text content of an element
   */
  async getText(selector: string): Promise<string> {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    return (await element.textContent()) || '';
  }
}
