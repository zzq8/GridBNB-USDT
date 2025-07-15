import asyncio
import logging
import traceback
import platform
import sys
from trader import GridTrader
from helpers import LogConfig, send_pushplus_message
from web_server import start_web_server
from exchange_client import ExchangeClient
from config import TradingConfig, SYMBOLS_LIST

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
    try:
        LogConfig.setup_logger()
        logging.info("="*50)
        logging.info("多币种网格交易系统启动")
        logging.info(f"待运行交易对: {SYMBOLS_LIST}")
        logging.info("="*50)

        if not SYMBOLS_LIST:
            logging.warning("没有配置任何交易对，程序即将退出。")
            return

        # 在主函数中创建唯一、共享的ExchangeClient实例
        shared_exchange_client = ExchangeClient()

        # 【新增】启动周期性时间同步任务
        await shared_exchange_client.start_periodic_time_sync()

        # 加载一次市场数据供所有实例使用
        await shared_exchange_client.load_markets()
        logging.info("市场数据加载完成，开始创建交易器实例...")

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

        # 如果有trader实例，启动Web服务器监控所有交易对
        if traders:
            logging.info(f"启动Web服务器监控 {len(traders)} 个交易对...")
            web_server_task = asyncio.create_task(start_web_server(traders))
            tasks.append(web_server_task)

        # 并发运行所有任务
        logging.info(f"开始并发运行 {len(SYMBOLS_LIST)} 个交易对...")
        await asyncio.gather(*tasks)

    except Exception as e:
        logging.critical(f"主程序发生未知严重错误: {e}\n{traceback.format_exc()}")

    finally:
        # 统一在此处关闭共享的客户端
        if shared_exchange_client:
            try:
                # 【新增】在关闭连接前，先停止时间同步任务
                await shared_exchange_client.stop_periodic_time_sync()
                await shared_exchange_client.close()
                logging.info("共享的交易所连接已安全关闭")
            except Exception as e:
                logging.error(f"关闭共享连接时发生错误: {str(e)}")

        logging.info("所有交易任务已结束。程序即将退出。")

if __name__ == "__main__":
    asyncio.run(main()) 