/**
 * API 基础地址，从环境变量读取。
 * 开发默认 localhost:8000，生产/测试通过 .env 覆盖。
 */
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
