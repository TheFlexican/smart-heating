import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  const { baseURL } = config.projects[0].use;

  console.log('Setting up authentication...');

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to base URL
    await page.goto(baseURL || 'http://localhost:8123', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3000);

    // Check for login form
    const hasLoginForm = await page.locator('input[name="username"]').isVisible({ timeout: 5000 }).catch(() => false);

    if (hasLoginForm) {
      console.log('Login form detected, authenticating...');

      // Fill in credentials
      await page.fill('input[name="username"]', 'test');
      await page.fill('input[name="password"]', 'test');

      // Submit login form by pressing Enter
      await page.press('input[name="password"]', 'Enter');

      // Wait for login to complete
      await page.waitForSelector('input[name="username"]', { state: 'hidden', timeout: 15000 });
      await page.waitForLoadState('networkidle', { timeout: 15000 });

      // Wait for sidebar to appear (indicates successful login)
      await page.waitForSelector('text=Overview', { timeout: 10000 });
      await page.waitForTimeout(3000);

      // Take screenshot to verify what page we're on
      await page.screenshot({ path: 'setup-after-login.png', fullPage: true });

      // Debug: Check what we have in storage
      const cookies = await context.cookies();
      const localStorageKeys = await page.evaluate(() => Object.keys(localStorage));
      const currentURL = page.url();
      console.log('Current URL:', currentURL);
      console.log('Cookies count:', cookies.length);
      console.log('LocalStorage keys:', localStorageKeys);

      console.log('Successfully logged in!');
    } else {
      console.log('Already logged in');
    }

    // Save authentication state (includes localStorage)
    await context.storageState({ path: 'auth.json' });

    console.log('Authentication setup complete!');
  } catch (error) {
    console.error('Failed to set up authentication:', error);
    throw error;
  } finally {
    await context.close();
    await browser.close();
  }
}

export default globalSetup;
