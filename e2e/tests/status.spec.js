import { test, expect } from '@playwright/test'
import { login } from './helpers.js'

test.describe('Status', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
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
    await page.locator('#trigger-update').click()
    // Button disables while updating
    await expect(page.locator('#trigger-update')).toBeDisabled()
    // Status message appears (success or error depending on hosts configured)
    await expect(page.locator('#status-message')).toBeVisible({ timeout: 10_000 })
    // Button re-enables after completion
    await expect(page.locator('#trigger-update')).toBeEnabled({ timeout: 10_000 })
  })
})
