"""
测试 structlog 日志系统

这个脚本用于验证 structlog 是否正确安装和配置
"""
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging_config import setup_structlog, get_logger

def test_structlog():
    """测试 structlog 功能"""

    # 1. 测试控制台输出（开发模式）
    print("=" * 50)
    print("测试1: 控制台输出（开发模式）")
    print("=" * 50)

    logger = setup_structlog(log_level="INFO", log_file=None)

    logger.info("test_console_output", message="这是控制台输出测试")
    logger.info(
        "order_executed",
        symbol="BNB/USDT",
        side="buy",
        price=680.5,
        amount=0.1234,
        total=84.0
    )
    logger.warning("test_warning", message="这是警告消息", level="warning")
    logger.error("test_error", message="这是错误消息", error_code=500)

    print("\n" + "=" * 50)
    print("测试2: JSON 文件输出（生产模式）")
    print("=" * 50)

    # 2. 测试 JSON 文件输出
    log_file = "logs/test_structlog.log"
    logger2 = setup_structlog(log_level="INFO", log_file=log_file)

    logger2.info("test_file_output", message="这是文件输出测试")
    logger2.info(
        "trading_system_started",
        symbols=["BNB/USDT", "ETH/USDT"],
        count=2
    )
    logger2.info(
        "order_executed",
        symbol="ETH/USDT",
        side="sell",
        price=3500.0,
        amount=0.05,
        total=175.0
    )

    print(f"\n✅ JSON 日志已写入: {log_file}")
    print("可以使用以下命令查看:")
    print(f"  cat {log_file}")
    print(f"  cat {log_file} | python -m json.tool  # 格式化查看")

    # 读取并显示文件内容
    print("\n" + "=" * 50)
    print("文件内容预览:")
    print("=" * 50)
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    except Exception as e:
        print(f"读取日志文件失败: {e}")

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    test_structlog()
