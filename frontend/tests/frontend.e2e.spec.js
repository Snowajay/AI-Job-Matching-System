// Front-end end-to-end test for the AI Job Matching System.
//
// Integration Lead: Terrance Montgomery
//
// This test drives the REAL React UI in a browser (not the API directly).
// It proves the AI semantic matcher works all the way through the front end:
// it types ABBREVIATED skills ("JS, Postgres, ML") into the profile form,
// saves the profile, clicks "Find Matches", and asserts the UI renders the
// JavaScript/PostgreSQL/Machine-Learning job at a 100% score. The old exact
// string matcher would have scored that candidate 0%, so a green run here is
// direct evidence of the AI component working end to end.
//
// PREREQUISITES (two terminals, both servers running):
//   1. Backend with the AI matcher:   uvicorn app.main:app --reload
//   2. Frontend dev server:           cd frontend ; npm run dev
//      -> must be reachable at http://localhost:5173
//
// FIRST-TIME SETUP (from the frontend/ folder):
//   npm install -D @playwright/test
//   npx playwright install chromium
//
// RUN:
//   npx playwright test
//   npx playwright test --headed      (watch it click through the UI)
//
// The test seeds its own job through the API so it does not depend on what is
// already in the database.

import { test, expect, request } from '@playwright/test'

const FRONTEND = process.env.FRONTEND_URL || 'http://localhost:5173'
const API = process.env.API_URL || 'http://127.0.0.1:8000'

// The front end posts matches for the hardcoded candidate id "test-candidate".
const CANDIDATE_ID = 'test-candidate'

test.beforeAll(async () => {
  // Seed the job the UI will match against, so the test is self-contained.
  const ctx = await request.newContext()
  const res = await ctx.post(`${API}/api/v1/jobs/`, {
    data: {
      job_id: 'JS-DEV-01',
      title: 'Frontend Engineer',
      company: 'Bright Labs',
      required_skills: ['JavaScript', 'PostgreSQL', 'Machine Learning'],
      posting_date: '2026-09-01',
    },
  })
  expect(res.ok(), 'seeding JS-DEV-01 job should succeed (is the backend running?)').toBeTruthy()
  await ctx.dispose()
})

test('AI matcher works through the React UI: abbreviated skills match at 100%', async ({ page }) => {
  // No uncaught console errors during the flow.
  const consoleErrors = []
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()) })

  await page.goto(FRONTEND)
  await expect(page.getByRole('heading', { name: 'Find jobs that match your skills' })).toBeVisible()

  // --- Fill the candidate profile with ABBREVIATIONS ---------------------
  await page.getByRole('button', { name: 'Manage Profile' }).click()
  const inputs = page.locator('.card input')
  await inputs.nth(0).fill('JS, Postgres, ML')        // Skills (abbreviations the AI must recognize)
  await inputs.nth(1).fill('Software Developer')       // Job Title
  await inputs.nth(2).fill('Acme')                    // Company
  await inputs.nth(3).fill('2022-01-01')              // Start Date
  await inputs.nth(4).fill('B.S. Computer Science')   // Qualification
  await inputs.nth(5).fill('UMGC')                    // Institution

  await page.getByRole('button', { name: 'Save Profile' }).click()
  await expect(page.getByText('Profile saved successfully.')).toBeVisible()

  // --- View jobs (exercises the listing UI) ------------------------------
  await page.getByRole('button', { name: 'View Jobs' }).click()
  await expect(page.getByRole('heading', { name: 'Frontend Engineer' })).toBeVisible()

  // --- Find matches and assert the UI shows 100% -------------------------
  await page.getByRole('button', { name: 'Find Matches' }).click()

  // Find JS-DEV-01 at WHATEVER rank it lands. The database is shared and may
  // already hold other 100% jobs from earlier runs, so we do not assume
  // JS-DEV-01 is #1 -- only that it is present and scored 100%.
  const jsMatch = page.getByRole('heading', { name: /#\d+ - JS-DEV-01/ })
  await expect(jsMatch).toBeVisible()

  // The match card is the div containing that heading.
  const card = page.locator('.card div', { has: jsMatch })
  await expect(card).toContainText('100%')
  // The reasons must VISIBLY show the AI recognized the abbreviations, not just
  // list the skills -- this is the user-facing proof of AI in the UI.
  await expect(card).toContainText("AI recognized your 'JS' as JavaScript")
  await expect(card).toContainText("AI recognized your 'Postgres' as PostgreSQL")
  await expect(card).toContainText("AI recognized your 'ML' as Machine Learning")

  expect(consoleErrors, `console errors: ${consoleErrors.join('; ')}`).toHaveLength(0)
})
