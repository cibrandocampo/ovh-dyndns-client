export const CREDS = {
  username: process.env.E2E_USERNAME ?? 'admin',
  password: process.env.E2E_PASSWORD ?? 'admin123',
}

/**
 * Logs in and waits for the dashboard to be visible.
 * Handles the must_change_password flow transparently on first login.
 */
export async function login(page) {
  await page.goto('/')
  await page.locator('#username').fill(CREDS.username)
  await page.locator('#password').fill(CREDS.password)
  await page.locator('#login-form button[type="submit"]').click()

  const dashboard = page.locator('#dashboard')
  const changePasswordPage = page.locator('#change-password-page')

  // Wait for either the dashboard or the change-password page
  await Promise.race([
    dashboard.waitFor({ state: 'visible' }),
    changePasswordPage.waitFor({ state: 'visible' }),
  ])

  if (await changePasswordPage.isVisible()) {
    // Complete the mandatory password change (reuse same password for e2e simplicity)
    await page.locator('#current-password').fill(CREDS.password)
    await page.locator('#new-password').fill(CREDS.password)
    await page.locator('#confirm-password').fill(CREDS.password)
    await page.locator('#change-password-form button[type="submit"]').click()
    await dashboard.waitFor({ state: 'visible' })
  }
}

/**
 * Navigates to a section of the dashboard by clicking its nav link.
 */
export async function goToSection(page, section) {
  await page.locator(`.nav-link[data-section="${section}"]`).click()
  await page.locator(`#${section}-section`).waitFor({ state: 'visible' })
}
