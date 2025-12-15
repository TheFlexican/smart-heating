import { Page } from '@playwright/test';

/**
 * Dismiss any snackbars in the Smart Heating iframe (e.g., WebSocket disconnect notices)
 */
export async function dismissSmartHeatingSnackbar(page: Page): Promise<void> {
  const frame = page.frameLocator('iframe[title="Smart Heating"]');

  // Try a few times to close any snackbars
  for (let i = 0; i < 5; i++) {
    const close = frame.locator('[aria-label="Close"]').first();
    const visible = await close.isVisible({ timeout: 1000 }).catch(() => false);
    if (visible) {
      await close.click({ force: true });
      await page.waitForTimeout(300);
      continue;
    }

    // Some snackbars don't have a close button; wait for alert to disappear
    const alert = frame.locator('div[role="presentation"] .MuiAlert-message').first();
    const alertVisible = await alert.isVisible({ timeout: 500 }).catch(() => false);
    if (alertVisible) {
      // try clicking the alert to dismiss or wait
      await alert.click({ force: true }).catch(() => {});
      await page.waitForTimeout(500);
      continue;
    }

    break;
  }

  // Also dismiss any snackbar in the main page body
  for (let i = 0; i < 3; i++) {
    const closeMain = page.locator('[aria-label="Close"]').first();
    const visibleMain = await closeMain.isVisible({ timeout: 500 }).catch(() => false);
    if (visibleMain) {
      await closeMain.click().catch(() => {});
      await page.waitForTimeout(300);
    } else {
      break;
    }
  }
}
