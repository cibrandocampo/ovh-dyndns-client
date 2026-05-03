import { test, expect } from '@playwright/test'
import { login, goToSection } from './helpers.js'

test.describe('Hosts', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToSection(page, 'hosts')
  })

  test('hosts section shows table with expected columns', async ({ page }) => {
    const headers = page.locator('#hosts-table thead th')
    await expect(headers).toHaveCount(5)
    await expect(headers.nth(0)).toHaveText('ID')
    await expect(headers.nth(1)).toHaveText('Hostname')
    await expect(headers.nth(2)).toHaveText('Username')
    await expect(headers.nth(3)).toHaveText('Created At')
    await expect(headers.nth(4)).toHaveText('Actions')
  })

  test('add host button opens modal', async ({ page }) => {
    await page.locator('#add-host-btn').click()
    await expect(page.locator('#host-modal')).toBeVisible()
    await expect(page.locator('#modal-title')).toHaveText('Add Host')
    await expect(page.locator('#host-hostname')).toBeVisible()
    await expect(page.locator('#host-username')).toBeVisible()
    await expect(page.locator('#host-password')).toBeVisible()
  })

  test('close modal hides it', async ({ page }) => {
    await page.locator('#add-host-btn').click()
    await expect(page.locator('#host-modal')).toBeVisible()
    await page.locator('#host-modal .close-modal').click()
    await expect(page.locator('#host-modal')).not.toBeVisible()
  })

  test('add host creates a new row in the table', async ({ page }) => {
    // Wait for the hosts API to finish loading before counting rows
    await page.waitForLoadState('networkidle')
    const initialRows = await page.locator('#hosts-table tbody tr').count()
    const hostname = `e2e-add-${Date.now()}.example.com`

    await page.locator('#add-host-btn').click()
    await page.locator('#host-hostname').fill(hostname)
    await page.locator('#host-username').fill('e2e-user')
    await page.locator('#host-password').fill('e2e-password')
    await page.locator('#host-form button[type="submit"]').click()

    await expect(page.locator('#host-modal')).not.toBeVisible()
    await expect(page.locator('#hosts-table tbody tr')).toHaveCount(initialRows + 1)
    await expect(page.locator('#hosts-table tbody')).toContainText(hostname)
  })

  test('delete host shows confirmation modal and removes row', async ({ page }) => {
    // Ensure the test host exists first
    const hostname = `e2e-del-${Date.now()}.example.com`
    await page.locator('#add-host-btn').click()
    await page.locator('#host-hostname').fill(hostname)
    await page.locator('#host-username').fill('e2e-user')
    await page.locator('#host-password').fill('e2e-password')
    await page.locator('#host-form button[type="submit"]').click()
    await expect(page.locator('#host-modal')).not.toBeVisible()

    const rowsBefore = await page.locator('#hosts-table tbody tr').count()

    // Click delete on the last row
    await page.locator('#hosts-table tbody tr').last().locator('[aria-label="Delete host"]').click()
    await expect(page.locator('#delete-modal')).toBeVisible()
    await expect(page.locator('#delete-hostname')).toHaveText(hostname)

    await page.locator('#confirm-delete').click()
    await expect(page.locator('#delete-modal')).not.toBeVisible()
    await expect(page.locator('#hosts-table tbody tr')).toHaveCount(rowsBefore - 1)
  })

  test('cancel delete keeps the row', async ({ page }) => {
    // Always add a fresh host to avoid duplicate hostname conflicts
    const hostname = `e2e-cancel-${Date.now()}.example.com`
    await page.locator('#add-host-btn').click()
    await page.locator('#host-hostname').fill(hostname)
    await page.locator('#host-username').fill('e2e-user')
    await page.locator('#host-password').fill('e2e-password')
    await page.locator('#host-form button[type="submit"]').click()
    await expect(page.locator('#host-modal')).not.toBeVisible()

    const rowsBefore = await page.locator('#hosts-table tbody tr').count()
    await page.locator('#hosts-table tbody tr').last().locator('[aria-label="Delete host"]').click()
    await expect(page.locator('#delete-modal')).toBeVisible()
    await page.locator('#cancel-delete').click()
    await expect(page.locator('#delete-modal')).not.toBeVisible()
    await expect(page.locator('#hosts-table tbody tr')).toHaveCount(rowsBefore)
  })
})
