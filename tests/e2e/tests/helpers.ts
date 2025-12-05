import { Page } from '@playwright/test';

/**
 * Common helper functions for Smart Heating E2E tests
 */

export async function login(page: Page) {
  await page.goto('/');
  
  // Check if we need to login
  const loginForm = page.locator('input[name="username"]');
  if (await loginForm.isVisible({ timeout: 2000 }).catch(() => false)) {
    await page.fill('input[name="username"]', 'test');
    await page.fill('input[name="password"]', 'test');
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
  }
}

export async function navigateToSmartHeating(page: Page) {
  await login(page);
  // Navigate directly to Smart Heating UI
  await page.goto('/smart_heating_ui');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000); // Give React time to load
}

export async function navigateToArea(page: Page, areaName: string) {
  await navigateToSmartHeating(page);
  // Wait for areas to load
  await page.waitForTimeout(1000);
  // Click on the area card
  const areaCard = page.locator(`text=${areaName}`).first();
  await areaCard.waitFor({ state: 'visible', timeout: 10000 });
  await areaCard.click();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
}

export async function switchToTab(page: Page, tabName: string) {
  await page.getByRole('tab', { name: tabName }).click();
  await page.waitForTimeout(500); // Wait for tab content to render
}

export async function dismissSnackbar(page: Page) {
  // Dismiss any visible snackbar notifications
  const closeButton = page.locator('[aria-label="Close"]').first();
  if (await closeButton.isVisible({ timeout: 1000 }).catch(() => false)) {
    await closeButton.click();
    await page.waitForTimeout(300);
  }
}

export async function expandSettingsCard(page: Page, cardTitle: string) {
  // Find the card by its title and click to expand (accordion pattern)
  await page.getByText(cardTitle).click();
  await page.waitForTimeout(800); // Wait for Collapse animation
}
