"""
GridBNB-USDT 多币种网格交易机器人主程序

企业级路径处理：
- 支持 python -m src.main（推荐）
- 支持 python src/main.py（兼容）
"""
import asyncio
import logging
import traceback
import platform
import sys
from pathlib import Path

# 企业级路径处理：确保项目根目录在 sys.path 中
# 这样可以支持多种运行方式
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.trader import GridTrader
from src.utils.helpers import LogConfig, send_pushplus_message
from src.services.web_server import start_web_server
from src.core.exchange_client import ExchangeClient
from src.config.settings import TradingConfig, SYMBOLS_LIST, settings
from src.utils.logging_config import get_logger
from src.services.alerting import setup_alerts, get_alert_manager, AlertLevel
from src.services.config_watcher import setup_config_watcher, get_config_watcher

# 获取 structlog logger
logger = get_logger(__name__)

async def periodic_global_status_logger(interval_seconds: int = 60):
    """
    一个独立的后台任务，使用自己独立的ExchangeClient实例，
    周期性地计算并记录真正的全账户总资产。
    【最终修复版】
    """
    logging.info(f"启动全局资产监控任务，每 {interval_seconds} 秒检查一次（仅在变化>1%时记录）。")

    # 1. 为此任务创建专用的、独立的客户端实例，确保数据隔离
    report_client = None
    try:
        report_client = ExchangeClient()
        await report_client.load_markets() # 独立加载市场数据
    except Exception as e:
        logging.critical(f"全局资产监控任务的客户端初始化失败，任务无法启动: {e}")
        return # 如果客户端初始化失败，则直接退出任务

    last_logged_total_value = 0.0

    while True:
        try:
            # 2. 使用专用的客户端进行计算
            current_total_value = await report_client.calculate_total_account_value(quote_currency='USDT')

            if abs(current_total_value - last_logged_total_value) / max(last_logged_total_value, 1e-9) > 0.01:
                logging.info(
                    f"【全局资产报告】当前全账户总价值: {current_total_value:.2f} USDT "
                    f"(较上次记录变化: {current_total_value - last_logged_total_value:+.2f} USDT)"
                )
                last_logged_total_value = current_total_value

            await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            logging.info("全局资产监控任务已取消。")
            break
        except Exception as e:
            logging.error(f"全局资产监控任务发生错误: {e}", exc_info=True)
            await asyncio.sleep(interval_seconds * 2)

    # 任务结束前，安全关闭专用的客户端
    if report_client:
        await report_client.close()
        logging.info("全局资产监控任务的客户端已关闭。")

# 在Windows平台上设置SelectorEventLoop
if platform.system() == 'Windows':
    import asyncio
    # 在Windows平台上强制使用SelectorEventLoop
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logging.info("已设置Windows SelectorEventLoop策略")

async def run_trader_for_symbol(symbol: str, exchange_client: ExchangeClient):
    """为单个交易对创建并运行一个交易器实例"""
    try:
        logging.info(f"为交易对 {symbol} 创建交易实例...")
        config = TradingConfig()

        # 使用传入的共享客户端
        trader = GridTrader(exchange_client, config, symbol)

        await trader.initialize()
        await trader.main_loop()

    except Exception as e:
        error_msg = f"交易对 {symbol} 的任务失败: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        send_pushplus_message(error_msg, f"致命错误 - {symbol}")

async def main():
    shared_exchange_client = None  # 在try块外部定义
    config_watcher = None  # 配置监听器
    try:
        LogConfig.setup_logger()
        logger.info("trading_system_started")
        logger.info("=" * 50)
        logger.info("trading_pairs_loaded", symbols=SYMBOLS_LIST, count=len(SYMBOLS_LIST))
        logger.info("=" * 50)

        if not SYMBOLS_LIST:
            logger.warning("no_symbols_configured", message="没有配置任何交易对，程序即将退出")
            return

        if len({s.split('/')[1] for s in SYMBOLS_LIST}) > 1:
            logger.warning("inconsistent_quote_currency", message="计价货币不一致，程序即将退出")
            return

        # 【阶段3新增】设置告警系统
        alert_manager = setup_alerts(
            pushplus_token=settings.PUSHPLUS_TOKEN,
            telegram_bot_token=settings.TELEGRAM_BOT_TOKEN,
            telegram_chat_id=settings.TELEGRAM_CHAT_ID,
            webhook_url=settings.WEBHOOK_URL
        )
        logger.info("alert_system_initialized", message="告警系统已初始化")

        # 在主函数中创建唯一、共享的ExchangeClient实例
        shared_exchange_client = ExchangeClient()

        # 【新增】启动周期性时间同步任务
        await shared_exchange_client.start_periodic_time_sync()

        # 加载一次市场数据供所有实例使用
        await shared_exchange_client.load_markets()
        logger.info("markets_loaded", message="市场数据加载完成，开始创建交易器实例")

        traders = {}  # 用于存储所有trader实例，供Web服务器使用
        tasks = []

        # 为每个交易对创建trader实例和任务
        for symbol in SYMBOLS_LIST:
            config = TradingConfig()
            trader_instance = GridTrader(shared_exchange_client, config, symbol)
            traders[symbol] = trader_instance

            # 初始化trader
            await trader_instance.initialize()

            # 创建运行任务
            tasks.append(trader_instance.main_loop())

        # 【阶段4新增】设置配置热重载
        def on_config_change():
            """配置文件变更时的回调函数"""
            logger.info("config_file_changed", message="检测到配置文件变更，开始更新所有交易器配置")
            for symbol, trader in traders.items():
                try:
                    trader.update_config()
                    logger.info("trader_config_updated", symbol=symbol)
                except Exception as e:
                    logger.error("trader_config_update_failed", symbol=symbol, error=str(e))

        config_watcher = setup_config_watcher(
            config_file="config/.env",
            callbacks={"traders": on_config_change}
        )
        logger.info("config_watcher_started", message="配置热重载已启动")

        # 如果有trader实例，启动Web服务器监控所有交易对
        if traders:
            logger.info("starting_web_server", trader_count=len(traders))
            web_server_task = asyncio.create_task(start_web_server(traders))
            tasks.append(web_server_task)

        # 【新增】启动独立的全局资产监控任务
        global_status_task = asyncio.create_task(
            periodic_global_status_logger(interval_seconds=60)
        )
        tasks.append(global_status_task)

        # 并发运行所有任务
        logger.info("starting_concurrent_tasks", symbol_count=len(SYMBOLS_LIST), total_tasks=len(tasks))

        # 【阶段3新增】发送系统启动通知
        await alert_manager.send_alert(
            AlertLevel.WARNING,
            "交易系统启动",
            f"GridBNB 交易系统已成功启动\n交易对: {', '.join(SYMBOLS_LIST)}\n实例数量: {len(traders)}"
        )

        await asyncio.gather(*tasks)

    except Exception as e:
        logger.critical("main_program_error", error=str(e), traceback=traceback.format_exc())

        # 【阶段3新增】发送严重错误告警
        alert_manager = get_alert_manager()
        await alert_manager.send_alert(
            AlertLevel.CRITICAL,
            "主程序严重错误",
            f"交易系统发生未知严重错误\n错误信息: {str(e)}",
            error=str(e),
            traceback=traceback.format_exc()[:500]  # 限制长度
        )

    finally:
        # 【阶段4新增】停止配置监听器
        if config_watcher and config_watcher.is_running():
            try:
                config_watcher.stop()
                logger.info("config_watcher_stopped", message="配置监听器已停止")
            except Exception as e:
                logger.error("config_watcher_stop_error", error=str(e))

        # 统一在此处关闭共享的客户端
        if shared_exchange_client:
            try:
                # 【新增】在关闭连接前，先停止时间同步任务
                await shared_exchange_client.stop_periodic_time_sync()
                await shared_exchange_client.close()
                logger.info("shared_client_closed", message="共享的交易所连接已安全关闭")
            except Exception as e:
                logger.error("client_close_error", error=str(e))

        logger.info("program_exiting", message="所有交易任务已结束，程序即将退出")

if __name__ == "__main__":
    asyncio.run(main()) 