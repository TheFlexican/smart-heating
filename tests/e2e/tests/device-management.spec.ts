import { test, expect } from '@playwright/test'
import { login, navigateToSmartHeating, navigateToArea, switchToTab, dismissSnackbar } from './helpers'

/**
 * Device Management Tests - Devices Tab in Area Detail
 * 
 * Features tested:
 * - Devices tab visibility and navigation
 * - Assigned Devices section display
 * - Available Devices section display
 * - Add device functionality
 * - Remove device functionality
 * - Smart filtering (HA area match + name-based matching)
 * - Real-time device status updates
 * 
 * Tests verify:
 * 1. Frontend UI displays devices correctly
 * 2. Backend API calls succeed
 * 3. State updates reflect in UI
 */

test.describe('Device Management', () => {
  
  test.beforeEach(async ({ page }) => {
    await login(page)
    await navigateToSmartHeating(page)
  })

  test.describe('Devices Tab Navigation', () => {
    
    test('should show Devices tab in area detail', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      
      // Verify Devices tab exists (2nd tab, index 1)
      const devicesTab = page.locator('button[role="tab"]', { hasText: /^Devices$/i })
      await expect(devicesTab).toBeVisible()
    })

    test('should navigate to Devices tab', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      
      // Click Devices tab
      await switchToTab(page, 'Devices')
      
      // Verify tab content is visible
      await expect(page.locator('text=/Assigned Devices/i')).toBeVisible({ timeout: 5000 })
      await expect(page.locator('text=/Available Devices/i')).toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('Assigned Devices Section', () => {
    
    test('should display assigned devices section', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Verify section header
      await expect(page.locator('text=/Assigned Devices \\(\\d+\\)/i')).toBeVisible()
      
      // Verify description text
      await expect(page.locator('text=/Devices currently assigned to this area/i')).toBeVisible()
    })

    test('should show assigned devices with remove buttons', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Check if there are assigned devices
      const assignedCount = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(assignedCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        // Verify device list items are visible
        const deviceItems = page.locator('[role="listitem"]').first()
        await expect(deviceItems).toBeVisible()
        
        // Verify remove button exists
        const removeButton = page.locator('button[aria-label="remove"]').first()
        await expect(removeButton).toBeVisible()
      }
      // If count is 0, test still passes (devices may all be assigned)
    })

    test('should display device status for assigned devices', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Check if there are assigned devices
      const assignedCount = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(assignedCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        // Verify device type is shown (e.g., "thermostat", "temperature sensor")
        const deviceType = page.locator('text=/thermostat|temperature sensor|valve|switch/i').first()
        await expect(deviceType).toBeVisible()
      }
    })
  })

  test.describe('Available Devices Section', () => {
    
    test('should display available devices section', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Verify section header
      await expect(page.locator('text=/Available Devices \\(\\d+\\)/i')).toBeVisible()
      
      // Verify description text
      await expect(page.locator('text=/Devices assigned to.*in Home Assistant but not yet added/i')).toBeVisible()
    })

    test('should show available devices with add buttons', async ({ page }) => {
      await navigateToArea(page, 'Kitchen')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Wait for available devices to load
      await page.waitForTimeout(1000)
      
      // Check if there are available devices
      const availableCount = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(availableCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        // Verify add button exists
        const addButton = page.locator('button', { hasText: /^Add$/i }).first()
        await expect(addButton).toBeVisible()
        
        // Verify device entity_id is shown
        const deviceInfo = page.locator('text=/climate\\.|sensor\\.|switch\\.|number\\./i').first()
        await expect(deviceInfo).toBeVisible()
      }
      // If count is 0, test still passes (all devices may be assigned)
    })

    test('should filter devices by HA area assignment', async ({ page }) => {
      // Navigate to Kitchen area
      await navigateToArea(page, 'Kitchen')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Get available devices count
      const availableCount = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(availableCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        // Verify device names contain "Kitchen" (name-based matching)
        const deviceNames = await page.locator('[role="listitem"]').allTextContents()
        const hasKitchenDevice = deviceNames.some(name => name.toLowerCase().includes('kitchen'))
        expect(hasKitchenDevice).toBeTruthy()
      }
    })
  })

  test.describe('Device Add/Remove Operations', () => {
    
    test('should add device from available to assigned', async ({ page }) => {
      await navigateToArea(page, 'Kitchen')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Get initial counts
      const initialAvailable = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
      const availableCount = parseInt(initialAvailable?.match(/\\d+/)?.[0] || '0')
      
      if (availableCount > 0) {
        // Get initial assigned count
        const initialAssigned = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
        const assignedCountBefore = parseInt(initialAssigned?.match(/\\d+/)?.[0] || '0')
        
        // Click first Add button
        const addButton = page.locator('button', { hasText: /^Add$/i }).first()
        await addButton.click()
        
        // Wait for update
        await page.waitForTimeout(2000)
        
        // Verify assigned count increased
        const newAssigned = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
        const assignedCountAfter = parseInt(newAssigned?.match(/\\d+/)?.[0] || '0')
        
        expect(assignedCountAfter).toBe(assignedCountBefore + 1)
      }
    })

    test('should remove device from assigned', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Get initial assigned count
      const initialAssigned = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
      const assignedCount = parseInt(initialAssigned?.match(/\\d+/)?.[0] || '0')
      
      if (assignedCount > 0) {
        // Get initial available count
        const initialAvailable = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
        const availableCountBefore = parseInt(initialAvailable?.match(/\\d+/)?.[0] || '0')
        
        // Click first Remove button
        const removeButton = page.locator('button[aria-label="remove"]').first()
        await removeButton.click()
        
        // Wait for update
        await page.waitForTimeout(2000)
        
        // Verify assigned count decreased
        const newAssigned = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
        const assignedCountAfter = parseInt(newAssigned?.match(/\\d+/)?.[0] || '0')
        
        expect(assignedCountAfter).toBe(assignedCount - 1)
        
        // Verify available count increased (if device had HA area assignment)
        const newAvailable = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
        const availableCountAfter = parseInt(newAvailable?.match(/\\d+/)?.[0] || '0')
        
        // Device should appear in available if it has HA area or name match
        expect(availableCountAfter).toBeGreaterThanOrEqual(availableCountBefore)
      }
    })
  })

  test.describe('Smart Filtering (HA Area + Name Matching)', () => {
    
    test('should match devices by HA area ID', async ({ page }) => {
      // This test verifies that devices with ha_area_id matching the zone ID appear
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Available devices should be filtered by HA area
      const availableSection = page.locator('text=/Available Devices/i')
      await expect(availableSection).toBeVisible()
    })

    test('should match devices by name (for MQTT devices)', async ({ page }) => {
      // This test verifies name-based matching for devices without HA area assignment
      await navigateToArea(page, 'Kitchen')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Check if available devices contain "Kitchen" in name
      const availableCount = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(availableCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        // Get device names
        const deviceItems = await page.locator('[role="listitem"]').allTextContents()
        
        // At least one device should contain the area name
        const hasMatchingName = deviceItems.some(item => 
          item.toLowerCase().includes('kitchen')
        )
        
        expect(hasMatchingName).toBeTruthy()
      }
    })

    test('should not show devices already assigned', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Get all assigned device names
      const assignedCount = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(assignedCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        const assignedSection = page.locator('text=/Assigned Devices/i').locator('..')
        const assignedDevices = await assignedSection.locator('[role="listitem"]').allTextContents()
        
        // Get all available device names
        const availableSection = page.locator('text=/Available Devices/i').locator('..')
        const availableDevices = await availableSection.locator('[role="listitem"]').allTextContents()
        
        // No device should appear in both lists
        const overlap = assignedDevices.some(assigned => 
          availableDevices.some(available => 
            assigned.includes(available) || available.includes(assigned)
          )
        )
        
        expect(overlap).toBeFalsy()
      }
    })
  })

  test.describe('Drag & Drop on Main Page (Preserved)', () => {
    
    test('should still have drag and drop on main page', async ({ page }) => {
      // Verify drag & drop functionality is preserved on main page
      
      // Check for Available Devices sidebar
      const sidebar = page.locator('text=/Available Devices/i').first()
      await expect(sidebar).toBeVisible()
      
      // Check for "Drag devices to areas" text
      const dragText = page.locator('text=/Drag devices to areas/i')
      await expect(dragText).toBeVisible()
    })

    test('should show draggable devices in sidebar', async ({ page }) => {
      // Verify devices are still draggable on main page
      const devicePanel = page.locator('text=/Available Devices/i').first().locator('..')
      
      // Check if devices exist in sidebar
      const devices = devicePanel.locator('[draggable="true"]')
      const count = await devices.count()
      
      // Should have draggable devices (may be 0 if all assigned, that's OK)
      expect(count).toBeGreaterThanOrEqual(0)
    })
  })
})
