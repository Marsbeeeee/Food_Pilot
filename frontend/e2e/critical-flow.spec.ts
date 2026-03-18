import { test, expect } from '@playwright/test';

/**
 * 前端关键流程 E2E 测试
 * 覆盖：登录、聊天、保存 Food Log、进入 Insights 分析
 * 验收：发布前可一键执行并稳定回归
 */
const TEST_EMAIL = `e2e-${Date.now()}@foodpilot.test`;
const TEST_PASSWORD = 'TestPass123!';
const TEST_DISPLAY_NAME = 'E2E Tester';

test.describe('关键流程回归', () => {
  test('登录 -> 聊天 -> 保存 Food Log -> 进入 Insights', async ({ page }) => {
    // 1. 登录：注册新账号
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Welcome back|Create your account/ })).toBeVisible({ timeout: 10_000 });

    // 切换到注册模式（Header 中的 tab）
    await page.getByRole('banner').getByRole('button', { name: 'Create account' }).click();

    await page.getByPlaceholder('you@example.com').fill(TEST_EMAIL);
    await page.getByPlaceholder(/At least 8|password/).fill(TEST_PASSWORD);
    await page.getByPlaceholder('How the Assistant should address you').fill(TEST_DISPLAY_NAME);
    // 表单提交按钮
    await page.locator('form').getByRole('button', { name: 'Create account' }).click();

    // 等待进入主界面（Chat 或 Workspace）
    await expect(page.getByRole('button', { name: 'Start New Chat' })).toBeVisible({ timeout: 15_000 });

    // 2. 聊天：发送估算问题
    await page.getByRole('button', { name: /估算这餐|一份牛油果吐司/ }).first().click();

    // 等待 AI 返回 meal_estimate 结果（含「保存到 Food Log」按钮）
    const saveButton = page.getByRole('button', { name: '保存到 Food Log' });
    await expect(saveButton).toBeVisible({ timeout: 60_000 });

    // 3. 保存 Food Log
    await saveButton.click();
    await expect(page.getByText('已保存')).toBeVisible({ timeout: 10_000 });

    // 4. 进入 Insights
    await page.getByRole('button', { name: 'Insights' }).click();
    await expect(page.getByRole('heading', { name: 'Insights' })).toBeVisible({ timeout: 10_000 });

    // 5. 进入 Food Log 验证条目存在（导航栏按钮，非「返回 Food Log」）
    await page.getByRole('navigation').getByRole('button', { name: 'Food Log' }).click();
    await expect(page.getByRole('heading', { name: 'Saved Entries', level: 1 })).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText(/牛油果|吐司|avocado|toast/i).first()).toBeVisible({ timeout: 5_000 });
  });
});
