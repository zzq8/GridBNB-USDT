"""
测试告警系统

这个脚本用于验证多渠道告警系统是否正确工作
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.services.alerting import setup_alerts, AlertLevel, get_alert_manager


async def test_alerts():
    """测试告警系统"""

    print("=" * 60)
    print("告警系统测试")
    print("=" * 60)

    # 1. 从环境变量读取配置
    pushplus_token = os.getenv("PUSHPLUS_TOKEN")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    webhook_url = os.getenv("WEBHOOK_URL")

    # 1. 初始化告警系统
    print("\n步骤 1: 初始化告警系统...")
    alert_manager = setup_alerts(
        pushplus_token=pushplus_token,
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id,
        webhook_url=webhook_url
    )

    # 显示已配置的渠道
    print(f"已配置的告警渠道: {list(alert_manager.channels.keys())}")

    if not alert_manager.channels:
        print("\n⚠️  警告: 没有配置任何告警渠道")
        print("请在 config/.env 中配置以下参数:")
        print("  - PUSHPLUS_TOKEN")
        print("  - TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID")
        print("  - WEBHOOK_URL")
        return

    # 2. 测试 WARNING 级别告警
    print("\n步骤 2: 测试 WARNING 级别告警（仅 PushPlus）...")
    await alert_manager.send_alert(
        AlertLevel.WARNING,
        "测试告警 - WARNING",
        "这是一条 WARNING 级别的测试消息\n\n测试时间：2025-10-20",
        test_key="test_value"
    )
    print("✅ WARNING 告警已发送")
    await asyncio.sleep(2)

    # 3. 测试 ERROR 级别告警
    print("\n步骤 3: 测试 ERROR 级别告警（PushPlus + Telegram）...")
    await alert_manager.send_alert(
        AlertLevel.ERROR,
        "测试告警 - ERROR",
        "这是一条 ERROR 级别的测试消息\n\n包含上下文信息：\n• 交易对: BNB/USDT\n• 错误代码: 500",
        symbol="BNB/USDT",
        error_code=500
    )
    print("✅ ERROR 告警已发送")
    await asyncio.sleep(2)

    # 4. 测试 CRITICAL 级别告警
    print("\n步骤 4: 测试 CRITICAL 级别告警（所有渠道）...")
    await alert_manager.send_alert(
        AlertLevel.CRITICAL,
        "测试告警 - CRITICAL",
        "这是一条 CRITICAL 级别的测试消息\n\n系统严重错误，需要立即处理！",
        urgency="high",
        action_required="立即检查系统状态"
    )
    print("✅ CRITICAL 告警已发送")
    await asyncio.sleep(2)

    # 5. 测试 INFO 级别（应该不发送）
    print("\n步骤 5: 测试 INFO 级别告警（不应发送）...")
    await alert_manager.send_alert(
        AlertLevel.INFO,
        "测试告警 - INFO",
        "这是一条 INFO 级别的测试消息，不应该发送到任何渠道"
    )
    print("✅ INFO 级别告警测试完成（按设计不发送）")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print("\n请检查以下渠道是否收到告警:")
    if 'pushplus' in alert_manager.channels:
        print("  - PushPlus: 应收到 WARNING、ERROR、CRITICAL 各1条")
    if 'telegram' in alert_manager.channels:
        print("  - Telegram: 应收到 ERROR、CRITICAL 各1条")
    if 'webhook' in alert_manager.channels:
        print("  - Webhook: 应收到 CRITICAL 1条")


if __name__ == "__main__":
    asyncio.run(test_alerts())
