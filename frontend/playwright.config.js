// Playwright configuration for the front-end E2E test.
//
// Assumes the backend (uvicorn) and the Vite dev server are already running.
// The dev server must be reachable at http://localhost:5173 so that its origin
// matches the backend CORS allow-list.
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.FRONTEND_URL || 'http://localhost:5173',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // CHROMIUM_PATH is only used in CI/sandboxes that ship their own
        // browser; on a normal machine leave it unset and Playwright uses the
        // browser installed by "npx playwright install chromium".
        launchOptions: process.env.CHROMIUM_PATH
          ? { executablePath: process.env.CHROMIUM_PATH }
          : {},
      },
    },
  ],
})
