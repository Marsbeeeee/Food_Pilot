import { test, expect } from '@playwright/test';

const TEST_EMAIL = `e2e-${Date.now()}@foodpilot.test`;
const TEST_PASSWORD = 'TestPass123!';
const TEST_DISPLAY_NAME = 'E2E Tester';
const HAS_DASHSCOPE_API_KEY = Boolean(process.env.DASHSCOPE_API_KEY);

test.describe('关键流程回归', () => {
  test.skip(!HAS_DASHSCOPE_API_KEY, 'Requires DASHSCOPE_API_KEY for live AI response.');

  test('登录 -> 聊天 -> 保存 Food Log -> 进入 Insights', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Welcome back|Create your account/ })).toBeVisible({ timeout: 10_000 });

    await page.getByRole('banner').getByRole('button', { name: 'Create account' }).click();

    await page.getByPlaceholder('you@example.com').fill(TEST_EMAIL);
    await page.getByPlaceholder(/At least 8|password/).fill(TEST_PASSWORD);
    await page.getByPlaceholder('How the Assistant should address you').fill(TEST_DISPLAY_NAME);
    await page.locator('form').getByRole('button', { name: 'Create account' }).click();

    await expect(page.getByRole('button', { name: 'Start New Chat' })).toBeVisible({ timeout: 15_000 });

    await page.getByRole('button', { name: /估算这餐|一份牛油果吐司|Estimate this meal|avocado toast/i }).first().click();

    const saveButton = page
      .getByRole('button', { name: /保存到 Food Log|Save to Food Log/i })
      .last();
    await expect(saveButton).toBeVisible({ timeout: 60_000 });

    await saveButton.click();
    await expect(page.getByText(/已保存|Saved/i)).toBeVisible({ timeout: 10_000 });

    await page.getByRole('button', { name: 'Insights' }).click();
    await expect(page.getByRole('heading', { name: 'Insights' })).toBeVisible({ timeout: 10_000 });

    await page.getByRole('navigation').getByRole('button', { name: 'Food Log' }).click();
    await expect(page.getByRole('heading', { name: 'Saved Entries', level: 1 })).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText(/牛油果|avocado|toast/i).first()).toBeVisible({ timeout: 5_000 });
  });
});
