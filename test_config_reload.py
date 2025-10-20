"""
测试配置热重载功能

这个脚本用于验证配置文件变更时,系统能够自动重新加载配置
"""
import time
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 设置模拟的 API 密钥（避免 Pydantic 验证错误）
os.environ['BINANCE_API_KEY'] = 'test_key_' + 'x' * 64
os.environ['BINANCE_API_SECRET'] = 'test_secret_' + 'x' * 64
os.environ['SYMBOLS'] = 'BNB/USDT'

from src.services.config_watcher import setup_config_watcher, get_config_watcher
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_current_config():
    """打印当前配置"""
    print("\n" + "=" * 60)
    print("当前配置状态:")
    print("=" * 60)
    print(f"交易对列表: {os.getenv('SYMBOLS', 'BNB/USDT')}")
    print(f"初始网格大小: {os.getenv('INITIAL_GRID', '2.0')}%")
    print(f"最小交易金额: {os.getenv('MIN_TRADE_AMOUNT', '20.0')} USDT")
    print(f"最大仓位比例: {os.getenv('MAX_POSITION_RATIO', '0.9')}")
    print(f"最小仓位比例: {os.getenv('MIN_POSITION_RATIO', '0.1')}")
    print("=" * 60 + "\n")


def on_config_change():
    """配置变更回调"""
    logger.info("✅ 配置文件已变更,重新加载配置...")
    # 重新读取测试配置文件
    test_config_file = Path(__file__).resolve().parent / "config" / ".env.test"
    load_dotenv(str(test_config_file), override=True)
    print_current_config()


def test_config_watcher():
    """测试配置监听器"""

    print("\n" + "=" * 60)
    print("配置热重载测试")
    print("=" * 60)

    # 0. 创建测试用的配置文件（如果不存在）
    test_config_file = project_root / "config" / ".env.test"
    if not test_config_file.parent.exists():
        test_config_file.parent.mkdir(parents=True, exist_ok=True)

    # 写入初始配置
    test_config_content = """# 测试配置文件
BINANCE_API_KEY=test_key_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
BINANCE_API_SECRET=test_secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SYMBOLS=BNB/USDT
INITIAL_GRID=2.0
MIN_TRADE_AMOUNT=20.0
MAX_POSITION_RATIO=0.9
MIN_POSITION_RATIO=0.1
"""
    test_config_file.write_text(test_config_content, encoding='utf-8')
    logger.info(f"已创建测试配置文件: {test_config_file}")

    # 1. 打印初始配置
    logger.info("步骤 1: 打印初始配置")
    load_dotenv(str(test_config_file), override=True)
    print_current_config()

    # 2. 设置配置监听器
    logger.info("步骤 2: 启动配置监听器...")
    watcher = setup_config_watcher(
        config_file=str(test_config_file),
        callbacks={"test": on_config_change}
    )

    if watcher.is_running():
        logger.info("✅ 配置监听器已启动")
    else:
        logger.error("❌ 配置监听器启动失败")
        return

    # 3. 等待并自动修改配置文件
    print("\n" + "=" * 60)
    print("将在 3 秒后自动修改配置文件以测试热重载...")
    print("=" * 60 + "\n")

    try:
        # 等待3秒
        for i in range(3):
            logger.info(f"等待中... ({i+1}/3 秒)")
            time.sleep(1)

        # 修改配置文件
        logger.info("正在修改配置文件...")
        modified_content = """# 测试配置文件（已修改）
BINANCE_API_KEY=test_key_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
BINANCE_API_SECRET=test_secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SYMBOLS=BNB/USDT,ETH/USDT
INITIAL_GRID=3.5
MIN_TRADE_AMOUNT=30.0
MAX_POSITION_RATIO=0.85
MIN_POSITION_RATIO=0.15
"""
        test_config_file.write_text(modified_content, encoding='utf-8')
        logger.info("✅ 配置文件已修改")

        # 等待一段时间让监听器检测到变化
        logger.info("等待配置监听器检测到变化...")
        time.sleep(3)

    except KeyboardInterrupt:
        logger.info("用户中断测试")

    finally:
        # 4. 停止监听器
        logger.info("步骤 3: 停止配置监听器...")
        watcher.stop()
        logger.info("✅ 配置监听器已停止")

        # 清理测试文件
        if test_config_file.exists():
            test_config_file.unlink()
            logger.info(f"已删除测试配置文件: {test_config_file}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print("\n如果你修改了配置文件,应该能看到配置变更的日志输出。")
    print("如果没有看到,请检查:")
    print("  1. 配置文件路径是否正确 (config/.env)")
    print("  2. 文件是否真的被保存 (有些编辑器需要手动保存)")
    print("  3. 防抖时间设置为1秒,短时间内多次保存可能只触发一次回调\n")


if __name__ == "__main__":
    test_config_watcher()
