import { test, expect } from '@playwright/test'
import { login, goToSection } from './helpers.js'

test.describe('History', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToSection(page, 'history')
  })

  test('history section renders', async ({ page }) => {
    await expect(page.locator('#history-section')).toBeVisible()
  })

  test('history table has expected columns', async ({ page }) => {
    const headers = page.locator('#history-table thead th')
    await expect(headers).toHaveCount(5)
    await expect(headers.nth(0)).toHaveText('Timestamp')
    await expect(headers.nth(1)).toHaveText('Action')
    await expect(headers.nth(2)).toHaveText('Hostname')
    await expect(headers.nth(3)).toHaveText('IP')
    await expect(headers.nth(4)).toHaveText('Details')
  })

  test('pagination controls render', async ({ page }) => {
    await expect(page.locator('#prev-page')).toBeVisible()
    await expect(page.locator('#next-page')).toBeVisible()
    await expect(page.locator('#page-info')).toContainText('Page 1')
  })

  test('previous page button is disabled on first page', async ({ page }) => {
    await expect(page.locator('#prev-page')).toBeDisabled()
  })
})
