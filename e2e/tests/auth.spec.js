import { test, expect } from '@playwright/test'
import { login, CREDS } from './helpers.js'

test.describe('Auth', () => {
  test('login page loads', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('#login-page')).toBeVisible()
    await expect(page.locator('#username')).toBeVisible()
    await expect(page.locator('#password')).toBeVisible()
    await expect(page.locator('#login-form button[type="submit"]')).toBeVisible()
  })

  test('wrong credentials shows error', async ({ page }) => {
    await page.goto('/')
    await page.locator('#username').fill(CREDS.username)
    await page.locator('#password').fill('wrong-password')
    await page.locator('#login-form button[type="submit"]').click()
    await expect(page.locator('#login-error')).not.toBeEmpty()
  })

  test('correct credentials shows dashboard', async ({ page }) => {
    await login(page)
    await expect(page.locator('#dashboard')).toBeVisible()
    await expect(page.locator('#login-page')).not.toBeVisible()
  })

  test('unauthenticated load shows login page', async ({ page }) => {
    await page.goto('/')
    // No token in localStorage → login page shown
    await expect(page.locator('#login-page')).toBeVisible()
    await expect(page.locator('#dashboard')).not.toBeVisible()
  })

  test('logout clears session and shows login page', async ({ page }) => {
    await login(page)
    await page.locator('#logout-link').click()
    await expect(page.locator('#login-page')).toBeVisible()
    await expect(page.locator('#dashboard')).not.toBeVisible()
    // Token cleared — reloading shows login again
    await page.reload()
    await expect(page.locator('#login-page')).toBeVisible()
  })
})
