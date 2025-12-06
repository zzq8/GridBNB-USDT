"""
完整集成示例 - 如何在 GridTrader 中使用新的网格策略引擎

本文件展示了如何将新的配置驱动��网格策略引擎集成到现有的 GridTrader 中。

使用方式：
1. 基础集成：在 trader.py 中添加可选的配置驱动模式
2. API 驱动：通过 API 创建和管理策略配置
3. 向后兼容：不影响现有的硬编码策略逻辑

创建日期: 2025-11-07
作者: AI Assistant
"""

import asyncio
import logging
from typing import Optional

from src.strategies.grid_strategy_config import GridStrategyConfig, StrategyTemplates
from src.strategies.grid_trigger_engine import GridTriggerEngine
from src.strategies.grid_order_engine import GridOrderEngine
from src.strategies.advanced_risk_controller import AdvancedRiskController


# ============================================================================
# 示例 1: 修改 GridTrader 以支持配置驱动模式
# ============================================================================

class GridTraderEnhanced:
    """
    增强版 GridTrader

    支持两种模式：
    1. 原有模式：使用硬编码配置（向后兼容）
    2. 配置模式：使用 GridStrategyConfig（新功能）
    """

    def __init__(self, exchange, config, symbol: str, global_allocator=None,
                 grid_strategy_config: Optional[GridStrategyConfig] = None):
        """
        初始化交易器

        Args:
            exchange: 交易所实例
            config: 原有配置对象
            symbol: 交易对
            global_allocator: 全局资金分配器
            grid_strategy_config: 可选的网格策略配置（启用新引擎）
        """
        # ... 原有初始化代码 ...

        # 新增：网格策略引擎
        self.grid_strategy_config = grid_strategy_config
        self.trigger_engine: Optional[GridTriggerEngine] = None
        self.order_engine: Optional[GridOrderEngine] = None
        self.risk_controller: Optional[AdvancedRiskController] = None

        if grid_strategy_config:
            self._initialize_strategy_engines()

    def _initialize_strategy_engines(self):
        """初始化策略引擎"""
        self.trigger_engine = GridTriggerEngine(self.grid_strategy_config, self)
        self.order_engine = GridOrderEngine(self.grid_strategy_config, self)
        self.risk_controller = AdvancedRiskController(self.grid_strategy_config, self)

        self.logger.info(
            f"✅ 网格策略引擎已启用 | "
            f"策略: {self.grid_strategy_config.strategy_name} | "
            f"配置ID: {self.grid_strategy_config.strategy_id}"
        )

    async def _check_sell_signal_enhanced(self):
        """
        增强版卖出信号检测

        优先使用新引擎，回退到原有逻辑
        """
        if self.trigger_engine:
            # 使用新引擎
            current_price = await self._get_latest_price()

            # 检查价格区间
            if not self.trigger_engine.check_price_range(current_price):
                self.logger.warning("价格超出允许区间，跳过卖出检测")
                return False

            return await self.trigger_engine.check_sell_signal(current_price)

        else:
            # 使用原有逻辑（向后兼容）
            return await self._check_sell_signal()

    async def _check_buy_signal_enhanced(self):
        """
        增强版买入信号检测

        优先使用新引擎，回退到原有逻辑
        """
        if self.trigger_engine:
            # 使用新引擎
            current_price = await self._get_latest_price()

            # 检查价格区间
            if not self.trigger_engine.check_price_range(current_price):
                self.logger.warning("价格超出允许区间，跳过买入检测")
                return False

            return await self.trigger_engine.check_buy_signal(current_price)

        else:
            # 使用原有逻辑
            return await self._check_buy_signal()

    async def execute_order_enhanced(self, side):
        """
        增强版订单执行

        使用新引擎准备订单，保留原有执行逻辑
        """
        max_retries = 10
        retry_count = 0

        while retry_count < max_retries:
            try:
                if self.order_engine:
                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    # 使用新引擎准备订单
                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    order_price, amount_quote, amount_base = \
                        await self.order_engine.prepare_order(side)

                    # 调整精度（保留原有逻辑）
                    amount_base = float(self._adjust_amount_precision(amount_base))
                    order_price = self._adjust_price_precision(order_price)

                    # 获取订单类型
                    order_type = self.grid_strategy_config.order_type

                else:
                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    # 使用原有逻辑（向后兼容）
                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    order_book = await self.exchange.fetch_order_book(self.symbol, limit=5)

                    if side == 'buy':
                        order_price = order_book['asks'][0][0]
                    else:
                        order_price = order_book['bids'][0][0]

                    amount_quote = await self._calculate_order_amount(side)
                    amount_base = self._adjust_amount_precision(amount_quote / order_price)
                    order_price = self._adjust_price_precision(order_price)
                    order_type = 'limit'

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # 余额检查（保留原有逻辑）
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                spot_balance = await self.exchange.fetch_balance({'type': 'spot'})
                funding_balance = await self.exchange.fetch_funding_balance()

                if not await self._ensure_balance_for_trade(side, spot_balance, funding_balance):
                    self.logger.warning(f"{side}余额不足，第 {retry_count + 1} 次尝试中止")
                    return False

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # 创建订单
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                self.logger.info(
                    f"创建订单 | "
                    f"方向: {side.upper()} | "
                    f"类型: {order_type} | "
                    f"价格: {order_price} | "
                    f"数量: {amount_base:.6f}"
                )

                order = await self.exchange.create_order(
                    self.symbol,
                    order_type,
                    side,
                    amount_base,
                    order_price if order_type == 'limit' else None
                )

                # ... 后续处理逻辑（等待成交、记录、通知等）...
                # 这部分保持原有代码

                return True

            except Exception as e:
                self.logger.error(f"执行{side}单失败: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(2)

        return False

    async def main_loop_enhanced(self):
        """
        增强版主循环

        添加高级风控检查
        """
        while True:
            try:
                if not self.initialized:
                    await self.initialize()

                current_price = await self._get_latest_price()
                if not current_price:
                    await asyncio.sleep(5)
                    continue

                self.current_price = current_price

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # 🆕 阶段零：高级风控检查（P1功能）
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                if self.risk_controller:
                    # 检查保底价
                    floor_triggered, floor_reason = await self.risk_controller.check_floor_price(current_price)

                    if floor_triggered and self.grid_strategy_config.floor_price_action == 'stop':
                        self.logger.critical("保底价触发，停止交易")
                        break  # 退出主循环

                    # 检查自动清仓条件
                    auto_close_triggered, auto_close_reason = \
                        await self.risk_controller.check_auto_close_conditions()

                    if auto_close_triggered:
                        self.logger.critical("自动清仓条件满足，执行清仓")
                        await self.risk_controller.execute_auto_close(auto_close_reason)
                        break  # 退出主循环

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # 原有主循环逻辑（使用增强版信号检测）
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                # 检查卖出信号
                if await self._check_sell_signal_enhanced():
                    await self.execute_order_enhanced('sell')

                # 检查买入信号
                elif await self._check_buy_signal_enhanced():
                    await self.execute_order_enhanced('buy')

                await asyncio.sleep(5)

            except Exception as e:
                self.logger.error(f"主循环错误: {e}", exc_info=True)
                await asyncio.sleep(30)


# ============================================================================
# 示例 2: 通过 API 创建和启动策略
# ============================================================================

async def example_api_driven_strategy():
    """
    示例：通过 API 创建和管理策略

    演示如何：
    1. 调用 API 创建策略配置
    2. 加载配置并启动 Trader
    """
    import httpx

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 步骤1: 通过 API 创建策略
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async with httpx.AsyncClient() as client:
        # 使用保守型模板创建策略
        response = await client.post(
            "http://localhost:8000/api/grid-strategies/templates/conservative_grid",
            params={"symbol": "BNB/USDT"}
        )

        result = response.json()
        strategy_id = result['id']
        print(f"✅ 策略已创建 | ID: {strategy_id}")

        # 获取策略配置
        response = await client.get(
            f"http://localhost:8000/api/grid-strategies/{strategy_id}"
        )

        config_data = response.json()

    # ━━━━���━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 步骤2: 从配置创建 GridStrategyConfig 实例
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    grid_config = GridStrategyConfig(**config_data)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 步骤3: 启动 Trader（使用配置）
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    from src.core.exchange_client import ExchangeClient
    from src.config.settings import TradingConfig

    exchange = ExchangeClient()
    config = TradingConfig()

    trader = GridTraderEnhanced(
        exchange=exchange,
        config=config,
        symbol="BNB/USDT",
        grid_strategy_config=grid_config  # 🔑 传入网格配置
    )

    # 启动交易
    await trader.main_loop_enhanced()


# ============================================================================
# 示例 3: 编程方式创建策略
# ============================================================================

async def example_programmatic_strategy():
    """
    示例：编程方式创建和使用策略

    演示如何：
    1. 直接创建 GridStrategyConfig
    2. 自定义配置参数
    3. 启动 Trader
    """

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 创建自定义策略配置
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    grid_config = GridStrategyConfig(
        strategy_name="BNB激进型网格",
        symbol="BNB/USDT",
        base_currency="BNB",
        quote_currency="USDT",

        # 触发条件：价差模式
        grid_type='price',
        trigger_base_price_type='manual',
        trigger_base_price=600.0,
        rise_sell_percent=15.0,  # 上涨15 USDT卖出
        fall_buy_percent=15.0,   # 下跌15 USDT买入

        # 启用高级触发
        enable_pullback_sell=True,
        pullback_sell_percent=1.0,  # 回落1%触发

        # 订单设置：限价单 + 盘口优化
        order_type='limit',
        buy_price_mode='ask1',   # 使用卖1价买入（快速成交）
        sell_price_mode='bid1',  # 使用买1价卖出（快速成交）
        buy_price_offset=-0.01,  # 买入价向下偏移0.01
        sell_price_offset=0.01,  # 卖出价向上偏移0.01

        # 数量管理：不对称网格
        amount_mode='amount',
        grid_symmetric=False,
        buy_quantity=100.0,   # 每次买入100 USDT
        sell_quantity=120.0,  # 每次卖出120 USDT

        # 仓位控制
        max_position=90,
        min_position=10,

        # P1功能：保底价和自动清仓
        enable_floor_price=True,
        floor_price=550.0,
        floor_price_action='alert',  # 触及时���警告

        enable_auto_close=True,
        auto_close_conditions={
            'profit_target': 500.0,      # 盈利500 USDT时清仓
            'loss_limit': 200.0,         # 亏损200 USDT时止损
            'price_drop_percent': 10.0,  # 价格暴跌10%时清仓
        }
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 启动 Trader
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    from src.core.exchange_client import ExchangeClient
    from src.config.settings import TradingConfig

    exchange = ExchangeClient()
    config = TradingConfig()

    trader = GridTraderEnhanced(
        exchange=exchange,
        config=config,
        symbol="BNB/USDT",
        grid_strategy_config=grid_config
    )

    await trader.main_loop_enhanced()


# ============================================================================
# 示例 4: 使用预设模板
# ============================================================================

async def example_template_strategy():
    """
    示例：使用预设模板快速启动策略
    """

    # 使用保守型模板
    grid_config = StrategyTemplates.conservative_grid("BNB/USDT")

    # 可选：调整部分参数
    grid_config.order_quantity = 15.0  # 修改为15%
    grid_config.enable_floor_price = True
    grid_config.floor_price = 500.0

    # 启动 Trader
    from src.core.exchange_client import ExchangeClient
    from src.config.settings import TradingConfig

    exchange = ExchangeClient()
    config = TradingConfig()

    trader = GridTraderEnhanced(
        exchange=exchange,
        config=config,
        symbol="BNB/USDT",
        grid_strategy_config=grid_config
    )

    await trader.main_loop_enhanced()


# ============================================================================
# 主程序入口示例
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== 网格策略引擎集成示例 ===\n")
    print("请选择运行模式：")
    print("1. API 驱动模式（需要先启动 FastAPI 服务）")
    print("2. 编程方式创建策略")
    print("3. 使用预设模板")

    choice = input("\n请输入选项 (1-3): ")

    if choice == '1':
        asyncio.run(example_api_driven_strategy())
    elif choice == '2':
        asyncio.run(example_programmatic_strategy())
    elif choice == '3':
        asyncio.run(example_template_strategy())
    else:
        print("无效选项")
