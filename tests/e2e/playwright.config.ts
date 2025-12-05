import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false, // Run tests sequentially for better debugging
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 0 : 0,
  workers: 3, // Single worker for sequential execution
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:8123',
    trace: 'on-first-retry',
    screenshot: 'on', // Always take screenshots
    video: 'retain-on-failure',
    headless: true, // Use headless mode for speed
  },

  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Use headed mode for better debugging
      },
    },
  ],

  webServer: {
    command: 'echo "Assuming Home Assistant is running on http://localhost:8123"',
    url: 'http://localhost:8123',
    reuseExistingServer: true,
    timeout: 5000,
  },
});
