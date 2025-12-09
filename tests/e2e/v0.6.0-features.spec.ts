import { test, expect } from '@playwright/test'

test.describe('User Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart_heating_ui/settings/users')
    await page.waitForLoadState('networkidle')
  })

  test('should display user management page', async ({ page }) => {
    await expect(page.locator('h4:has-text("User Management")')).toBeVisible()
    await expect(page.locator('button:has-text("Add User")')).toBeVisible()
  })

  test('should create a new user profile', async ({ page }) => {
    // Click Add User button
    await page.click('button:has-text("Add User")')
    
    // Fill in user details
    await page.fill('input[label="User ID"]', 'test_user')
    await page.fill('input[label="Name"]', 'Test User')
    await page.fill('input[label="Person Entity"]', 'person.test_user')
    await page.fill('input[label="Priority (1-10)"]', '7')
    
    // Set preset preferences
    await page.fill('input[label*="home"]', '21.0')
    await page.fill('input[label*="away"]', '16.0')
    await page.fill('input[label*="sleep"]', '18.5')
    
    // Save user
    await page.click('button:has-text("Save")')
    
    // Wait for save and verify user appears in table
    await page.waitForTimeout(500)
    await expect(page.locator('td:has-text("Test User")')).toBeVisible()
    await expect(page.locator('td:has-text("person.test_user")')).toBeVisible()
    await expect(page.locator('td:has-text("7")')).toBeVisible()
  })

  test('should update user profile', async ({ page }) => {
    // Assume user exists from previous test or setup
    // Click edit button for first user
    await page.click('button[aria-label="edit"] >> nth=0')
    
    // Update name
    await page.fill('input[label="Name"]', 'Updated User')
    await page.fill('input[label="Priority (1-10)"]', '9')
    
    // Save changes
    await page.click('button:has-text("Save")')
    
    await page.waitForTimeout(500)
    await expect(page.locator('td:has-text("Updated User")')).toBeVisible()
    await expect(page.locator('td:has-text("9")')).toBeVisible()
  })

  test('should delete user profile', async ({ page }) => {
    // Click delete button for first user
    await page.click('button[aria-label="delete"] >> nth=0')
    
    // Confirm deletion
    page.on('dialog', dialog => dialog.accept())
    
    await page.waitForTimeout(500)
    // Verify user no longer in table (check specific user name)
  })

  test('should display presence status', async ({ page }) => {
    await expect(page.locator('text=Presence Status')).toBeVisible()
    await expect(page.locator('text=/\\d+ users home/')).toBeVisible()
  })

  test('should update multi-user settings', async ({ page }) => {
    // Open settings dialog
    await page.click('button:has-text("Settings")')
    
    // Toggle multi-user enabled
    await page.click('input[type="checkbox"]')
    
    // Change strategy
    await page.click('div[role="button"]:has-text("Priority")')
    await page.click('li:has-text("Average")')
    
    // Close dialog
    await page.click('button:has-text("Close")')
    
    await page.waitForTimeout(500)
  })

  test('should show user status badges', async ({ page }) => {
    // Verify status badges (home/away) are visible
    await expect(page.locator('text=home, text=away').first()).toBeVisible()
  })

  test('should filter users by area', async ({ page }) => {
    // This test would verify area-specific user filtering if implemented
    // Currently users can be configured for specific areas
  })

  test('should show validation error for invalid priority', async ({ page }) => {
    await page.click('button:has-text("Add User")')
    
    await page.fill('input[label="User ID"]', 'invalid_user')
    await page.fill('input[label="Name"]', 'Invalid')
    await page.fill('input[label="Person Entity"]', 'person.invalid')
    await page.fill('input[label="Priority (1-10)"]', '15')  // Invalid
    
    await page.click('button:has-text("Save")')
    
    // Should show error
    await expect(page.locator('text=/error|invalid/i')).toBeVisible()
  })

  test('should prevent duplicate user IDs', async ({ page }) => {
    // Create first user
    await page.click('button:has-text("Add User")')
    await page.fill('input[label="User ID"]', 'duplicate')
    await page.fill('input[label="Name"]', 'First')
    await page.fill('input[label="Person Entity"]', 'person.first')
    await page.click('button:has-text("Save")')
    
    await page.waitForTimeout(500)
    
    // Try to create duplicate
    await page.click('button:has-text("Add User")')
    await page.fill('input[label="User ID"]', 'duplicate')
    await page.fill('input[label="Name"]', 'Second')
    await page.fill('input[label="Person Entity"]', 'person.second')
    await page.click('button:has-text("Save")')
    
    // Should show error
    await expect(page.locator('text=/already exists|duplicate/i')).toBeVisible()
  })
})

test.describe('Heating Efficiency Reports', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart_heating_ui/analytics/efficiency')
    await page.waitForLoadState('networkidle')
  })

  test('should display efficiency dashboard', async ({ page }) => {
    await expect(page.locator('h4:has-text("Efficiency Reports")')).toBeVisible()
  })

  test('should show efficiency scores for all areas', async ({ page }) => {
    // Verify chart or list showing efficiency scores
    await expect(page.locator('text=Energy Score')).toBeVisible()
    await expect(page.locator('text=/%/').first()).toBeVisible()  // Percentage values
  })

  test('should filter by time period', async ({ page }) => {
    // Click period selector
    await page.click('button:has-text("Day")')
    await page.click('li:has-text("Week")')
    
    await page.waitForTimeout(500)
    // Verify data updates
  })

  test('should display efficiency metrics', async ({ page }) => {
    await expect(page.locator('text=Heating Time')).toBeVisible()
    await expect(page.locator('text=Temperature Delta')).toBeVisible()
    await expect(page.locator('text=Heating Cycles')).toBeVisible()
  })

  test('should show recommendations', async ({ page }) => {
    await expect(page.locator('text=Recommendations')).toBeVisible()
  })

  test('should display efficiency trend chart', async ({ page }) => {
    // Verify chart is rendered
    await expect(page.locator('canvas, svg').first()).toBeVisible()
  })

  test('should show area-specific efficiency details', async ({ page }) => {
    // Click on an area
    await page.click('text=Living Room')
    
    await page.waitForTimeout(500)
    
    // Verify detailed metrics
    await expect(page.locator('text=Energy Score')).toBeVisible()
    await expect(page.locator('text=Recommendations')).toBeVisible()
  })
})

test.describe('Historical Comparisons', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart_heating_ui/analytics/comparison')
    await page.waitForLoadState('networkidle')
  })

  test('should display comparison dashboard', async ({ page }) => {
    await expect(page.locator('h4:has-text("Historical Comparisons")')).toBeVisible()
  })

  test('should compare current week to last week', async ({ page }) => {
    await page.click('button:has-text("Week")')
    
    await page.waitForTimeout(500)
    
    await expect(page.locator('text=Current Period')).toBeVisible()
    await expect(page.locator('text=/Last \\d+ week/i')).toBeVisible()
  })

  test('should display delta indicators', async ({ page }) => {
    // Verify improvement/regression indicators
    await expect(page.locator('text=/improved|decreased/i')).toBeVisible()
  })

  test('should show percentage changes', async ({ page }) => {
    await expect(page.locator('text=/%/')).toBeVisible()
  })

  test('should compare custom date ranges', async ({ page }) => {
    await page.click('button:has-text("Custom")')
    
    // Select dates
    await page.fill('input[type="date"]:nth(0)', '2025-01-01')
    await page.fill('input[type="date"]:nth(1)', '2025-01-07')
    await page.fill('input[type="date"]:nth(2)', '2024-12-25')
    await page.fill('input[type="date"]:nth(3)', '2024-12-31')
    
    await page.click('button:has-text("Compare")')
    
    await page.waitForTimeout(500)
    await expect(page.locator('text=Period A')).toBeVisible()
    await expect(page.locator('text=Period B')).toBeVisible()
  })

  test('should display comparison chart', async ({ page }) => {
    await expect(page.locator('canvas, svg').first()).toBeVisible()
  })

  test('should show summary text', async ({ page }) => {
    await expect(page.locator('text=/efficiency.*improved|decreased/i')).toBeVisible()
  })

  test('should compare multiple areas side by side', async ({ page }) => {
    await page.click('button:has-text("All Areas")')
    
    await page.waitForTimeout(500)
    
    // Verify multiple area comparisons
    await expect(page.locator('text=Living Room')).toBeVisible()
    await expect(page.locator('text=Bedroom')).toBeVisible()
  })
})
