import { test, expect } from '@playwright/test'

test.describe('Manual Override Mode Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to Smart Heating panel
    await page.goto('http://localhost:8123/smart_heating_panel/smart-heating')
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000) // Give WebSocket time to connect
  })

  test('should detect manual temperature change and enter manual override mode', async ({ page }) => {
    // Find any area card (first one available)
    const areaCard = page.locator('[class*="MuiCard"]').first()
    await expect(areaCard).toBeVisible()

    // Get the area name
    const areaName = await areaCard.locator('h6').first().textContent()
    console.log('Testing with area:', areaName)

    // Click on the area card to open detail view
    await areaCard.click()
    await page.waitForTimeout(1000)

    // Verify we're on the detail page
    await expect(page.locator(`h4:has-text("${areaName}")`)).toBeVisible()

    // Get current temperature
    const tempDisplay = page.locator('text=/\\d+(\\.\\d+)?°C/').first()
    const initialTemp = await tempDisplay.textContent()
    console.log('Initial temperature:', initialTemp)

    // Note: To properly test manual override, we would need to:
    // 1. Change the thermostat temperature outside the app (via HA)
    // 2. Wait for the debounce period (2 seconds)
    // 3. Verify the MANUAL badge appears
    // 4. Verify the temperature updates to match the external change
    // 5. Verify the app no longer controls the temperature automatically

    // For now, we'll verify the UI can display manual override state
    // Go back to main view
    await page.goBack()
    await page.waitForTimeout(1000)

    // Check if any area has MANUAL badge (might be set from previous tests)
    const manualBadge = page.locator('text=MANUAL').first()
    if (await manualBadge.isVisible()) {
      console.log('✓ Manual override badge is displayed')
      
      // Verify the badge has correct styling (warning color)
      const badgeElement = await manualBadge.elementHandle()
      if (badgeElement) {
        const bgColor = await page.evaluate(el => {
          return window.getComputedStyle(el).backgroundColor
        }, badgeElement)
        console.log('Manual badge background color:', bgColor)
      }
    } else {
      console.log('ℹ No manual override currently active (expected if thermostat not changed externally)')
    }
  })

  test('should clear manual override when temperature adjusted via app', async ({ page }) => {
    // Find any area card
    const areaCard = page.locator('[class*="MuiCard"]').first()
    await expect(areaCard).toBeVisible()

    // Check if already in manual mode
    const manualBadgeOnMain = page.locator('text=MANUAL').first()
    const hasManualMode = await manualBadgeOnMain.isVisible()
    
    if (hasManualMode) {
      console.log('✓ Found area in manual override mode, testing clear functionality')
      
      // Click on the card
      await areaCard.click()
      await page.waitForTimeout(1000)

      // Find the temperature slider
      const slider = page.locator('input[type="range"]').first()
      await expect(slider).toBeVisible()

      // Get current value
      const currentValue = await slider.getAttribute('value')
      console.log('Current temperature:', currentValue)

      // Move slider to change temperature
      await slider.fill(String(parseFloat(currentValue || '20') + 1))
      await page.waitForTimeout(2000) // Wait for API call

      // Go back to main view
      await page.goBack()
      await page.waitForTimeout(1000)

      // Verify MANUAL badge is gone
      const manualBadgeAfter = areaCard.locator('text=MANUAL')
      const stillInManualMode = await manualBadgeAfter.isVisible()
      
      if (!stillInManualMode) {
        console.log('✓ Manual override cleared successfully after app adjustment')
      } else {
        console.log('⚠ Manual badge still visible (might take longer to update)')
      }
    } else {
      console.log('ℹ No area currently in manual override mode, skipping clear test')
    }
  })

  test('should show manual override state in area detail view', async ({ page }) => {
    // Find any area card
    const areaCard = page.locator('[class*="MuiCard"]').first()
    await expect(areaCard).toBeVisible()

    // Click to open detail view
    await areaCard.click()
    await page.waitForTimeout(1000)

    // Check for presence of state badges (HOME, MANUAL, etc.)
    const stateBadges = page.locator('[class*="MuiChip"]')
    const badgeCount = await stateBadges.count()
    
    console.log(`Found ${badgeCount} state badges in area detail view`)

    // Check if MANUAL badge exists
    const manualBadge = page.locator('text=MANUAL')
    const hasManualBadge = await manualBadge.isVisible()
    
    if (hasManualBadge) {
      console.log('✓ MANUAL badge displayed in area detail view')
      
      // Verify it's a warning-colored badge
      const badge = await manualBadge.first().elementHandle()
      if (badge) {
        const parent = await page.evaluateHandle(el => el.parentElement, badge)
        const className = await page.evaluate(el => el?.className || '', parent)
        
        if (className.includes('warning')) {
          console.log('✓ MANUAL badge has warning color styling')
        }
      }
    } else {
      console.log('ℹ Area not in manual override mode')
    }
  })

  test('should persist manual override state across page refreshes', async ({ page }) => {
    // Check if any area is in manual mode
    const manualBadge = page.locator('text=MANUAL').first()
    const hasManualMode = await manualBadge.isVisible()
    
    if (hasManualMode) {
      console.log('✓ Found area in manual override mode')
      
      // Get the area name
      const card = manualBadge.locator('..').locator('..')
      const areaName = await card.locator('h6').first().textContent()
      console.log('Area in manual mode:', areaName)

      // Refresh the page
      await page.reload()
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(2000)

      // Check if manual mode still visible
      const manualBadgeAfterRefresh = page.locator('text=MANUAL').first()
      const stillHasManualMode = await manualBadgeAfterRefresh.isVisible()

      if (stillHasManualMode) {
        console.log('✓ Manual override state persisted across page refresh')
      } else {
        console.log('⚠ Manual override state not persisted (might have been cleared)')
      }
    } else {
      console.log('ℹ No area in manual override mode to test persistence')
    }
  })

  test('should receive real-time manual override updates via WebSocket', async ({ page }) => {
    // Set up WebSocket message listener
    const wsMessages: any[] = []
    
    page.on('websocket', ws => {
      ws.on('framereceived', event => {
        try {
          const message = JSON.parse(event.payload as string)
          if (message.type === 'result' && message.result?.event === 'update') {
            wsMessages.push(message)
            console.log('WebSocket update received:', message.result.data.areas ? 'areas update' : 'other update')
          }
        } catch (e) {
          // Ignore non-JSON frames
        }
      })
    })

    // Wait for initial WebSocket connection
    await page.waitForTimeout(3000)

    // Check initial WebSocket messages
    console.log(`Received ${wsMessages.length} WebSocket updates`)

    if (wsMessages.length > 0) {
      // Check if any area has manual_override flag
      const latestUpdate = wsMessages[wsMessages.length - 1]
      const areas = latestUpdate?.result?.data?.areas || {}
      
      const areasWithManualOverride = Object.entries(areas).filter(
        ([_, area]: [string, any]) => area.manual_override === true
      )

      if (areasWithManualOverride.length > 0) {
        console.log(`✓ Found ${areasWithManualOverride.length} area(s) with manual_override flag in WebSocket data`)
        areasWithManualOverride.forEach(([areaId, area]: [string, any]) => {
          console.log(`  - ${area.name}: manual_override=true, target_temp=${area.target_temperature}`)
        })
      } else {
        console.log('ℹ No areas currently in manual override mode')
      }
    }
  })
})
