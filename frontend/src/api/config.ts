/**
 * API 根地址，从环境变量读取，未配置时回退到本地开发默认值。
 * 修改后需重启 Vite 开发服务器。
 */
export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ||
  'http://localhost:8000';
