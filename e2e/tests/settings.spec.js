import { test, expect } from '@playwright/test'
import { login, goToSection } from './helpers.js'

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToSection(page, 'settings')
  })

  test('settings section renders the form', async ({ page }) => {
    await expect(page.locator('#settings-section')).toBeVisible()
    await expect(page.locator('#update-interval')).toBeVisible()
    await expect(page.locator('#logger-level')).toBeVisible()
    await expect(page.locator('#settings-form button[type="submit"]')).toBeVisible()
  })

  test('update interval is pre-filled with a number', async ({ page }) => {
    // Wait for the API to populate the field (starts empty, then gets set by loadSettings())
    await expect(page.locator('#update-interval')).not.toHaveValue('', { timeout: 5_000 })
    await expect(page.locator('#update-interval')).not.toHaveValue('0')
    const value = await page.locator('#update-interval').inputValue()
    expect(Number(value)).toBeGreaterThan(0)
  })

  test('log level selector has expected options', async ({ page }) => {
    const options = page.locator('#logger-level option')
    await expect(options).toHaveCount(5)
    const values = await options.evaluateAll(els => els.map(el => el.value))
    expect(values).toEqual(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
  })

  test('save settings shows success message', async ({ page }) => {
    // Wait for settings to load from API before saving
    await expect(page.locator('#update-interval')).not.toHaveValue('', { timeout: 5_000 })
    await page.locator('#settings-form button[type="submit"]').click()
    await expect(page.locator('#settings-message')).not.toBeEmpty({ timeout: 5_000 })
    await expect(page.locator('#settings-message')).toContainText('saved')
  })

  test('can change update interval and save', async ({ page }) => {
    // Wait for settings to load from API before making changes
    await expect(page.locator('#update-interval')).not.toHaveValue('', { timeout: 5_000 })
    await page.locator('#update-interval').fill('600')
    await page.locator('#settings-form button[type="submit"]').click()
    await expect(page.locator('#settings-message')).toContainText('saved', { timeout: 5_000 })

    // Navigate away and back to verify persistence
    await goToSection(page, 'status')
    await goToSection(page, 'settings')
    // Wait for settings to reload from API
    await expect(page.locator('#update-interval')).not.toHaveValue('', { timeout: 5_000 })
    await expect(page.locator('#update-interval')).not.toHaveValue('0')
    await expect(page.locator('#update-interval')).toHaveValue('600')

    // Restore original value
    await page.locator('#update-interval').fill('300')
    await page.locator('#settings-form button[type="submit"]').click()
  })
})
