#!/usr/bin/env python3
"""检查后端实际使用的 AI 配置，用于排查「服务暂不可用」问题。"""
import sys
from pathlib import Path

# 确保能导入 backend
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config.estimate import get_estimate_ai_config


def main() -> None:
    config = get_estimate_ai_config()
    print("=== 当前 AI 配置 ===")
    print(f"api_key 已设置: {bool(config.api_key)}")
    print(f"api_key 前几位: {config.api_key[:12]}..." if config.api_key else "无")
    print(f"model: {config.model}")
    print(f"openai_base_url: {config.openai_base_url or '(使用 Gemini)'}")
    print(f"timeout: {config.timeout_seconds}s")
    if not config.api_key:
        print("\n⚠️ 未检测到 API Key，请检查 .env 或 frontend/.env.local")
        sys.exit(1)
    print("\n配置加载正常。若仍报「服务暂不可用」，请检查：")
    print("1. API Key 是否有效、未过期")
    print("2. 千问：是否已开通百炼服务、账户有余额")
    print("3. 网络能否访问 dashscope.aliyuncs.com 或 Google API")


if __name__ == "__main__":
    main()
