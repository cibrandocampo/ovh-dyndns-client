import { test, expect } from '@playwright/test'
import { openDashboard } from './helpers.js'

test.describe('Status', () => {
  test.beforeEach(async ({ page }) => {
    await openDashboard(page)
    // Status section is shown by default after login
    await page.locator('#status-section').waitFor({ state: 'visible' })
  })

  test('status section is shown after login', async ({ page }) => {
    await expect(page.locator('#status-section')).toBeVisible()
    await expect(page.locator('.nav-link[data-section="status"]')).toHaveClass(/active/)
  })

  test('current IP card renders', async ({ page }) => {
    await expect(page.locator('#current-ip')).toBeVisible()
  })

  test('last check card renders', async ({ page }) => {
    await expect(page.locator('#last-check')).toBeVisible()
  })

  test('next scheduled check card renders', async ({ page }) => {
    await expect(page.locator('#next-check')).toBeVisible()
  })

  test('host status table has expected columns', async ({ page }) => {
    const headers = page.locator('#host-status-table thead th')
    await expect(headers).toHaveCount(5)
    await expect(headers.nth(0)).toHaveText('Hostname')
    await expect(headers.nth(1)).toHaveText('Last Update')
    await expect(headers.nth(2)).toHaveText('Status')
    await expect(headers.nth(3)).toHaveText('Error')
    await expect(headers.nth(4)).toHaveText('Actions')
  })

  test('trigger update button is visible', async ({ page }) => {
    await expect(page.locator('#trigger-update')).toBeVisible()
    await expect(page.locator('#trigger-update')).toBeEnabled()
  })

  test('trigger update button sends request and shows message', async ({ page }) => {
    // A real trigger calls OVH for every pending host, which takes from seconds
    // to minutes. The delay keeps the request in flight long enough to see the
    // disabled state.
    let triggered = false
    await page.route('**/api/status/trigger', async route => {
      triggered = true
      await new Promise(resolve => setTimeout(resolve, 500))
      await route.fulfill({ json: { success: true, message: 'DNS update triggered' } })
    })

    await page.locator('#trigger-update').click()
    // Button disables while updating
    await expect(page.locator('#trigger-update')).toBeDisabled()
    await expect(page.locator('#status-message')).toHaveText('DNS update triggered')
    // Button re-enables after completion
    await expect(page.locator('#trigger-update')).toBeEnabled()
    expect(triggered).toBe(true)
  })
})
