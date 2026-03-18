import { defineConfig, devices } from '@playwright/test';

/**
 * E2E 测试配置
 * 覆盖：登录、聊天、保存 Food Log、进入 Insights 分析
 * @see docs/PRODUCT_SPEC.md 6.1 P0
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  timeout: 90_000,
  expect: {
    timeout: 15_000,
  },
});
