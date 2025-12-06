"""
GridTriggerEngine 单元测试

测试触发引擎的价格计算和信号检测逻辑
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.strategies.grid_strategy_config import GridStrategyConfig
from src.strategies.grid_trigger_engine import GridTriggerEngine


@pytest.fixture
def mock_trader():
    """模拟 Trader 对象"""
    trader = MagicMock()
    trader.base_price = 600.0
    trader.exchange = MagicMock()
    trader.symbol = "BNB/USDT"

    # 模拟异步方法
    trader._get_latest_price = AsyncMock(return_value=600.0)
    trader.exchange.fetch_ohlcv = AsyncMock(return_value=[
        [0, 595, 610, 590, 605, 1000],  # 24个K线数据
        [0, 598, 612, 595, 608, 1000],
        # ... 更多数据
    ] * 12)  # 24小时数据

    return trader


@pytest.fixture
def percent_config():
    """百分比模式配置"""
    return GridStrategyConfig(
        strategy_name="测试",
        symbol="BNB/USDT",
        base_currency="BNB",
        quote_currency="USDT",
        grid_type='percent',
        trigger_base_price_type='manual',
        trigger_base_price=600.0,
        rise_sell_percent=1.0,  # 1%
        fall_buy_percent=1.0
    )


@pytest.fixture
def price_config():
    """价差模式配置"""
    return GridStrategyConfig(
        strategy_name="测试",
        symbol="BNB/USDT",
        base_currency="BNB",
        quote_currency="USDT",
        grid_type='price',
        trigger_base_price_type='manual',
        trigger_base_price=600.0,
        rise_sell_percent=10.0,  # 10 USDT
        fall_buy_percent=10.0
    )


class TestBasePriceCalculation:
    """基准价计算测试"""

    @pytest.mark.asyncio
    async def test_manual_base_price(self, mock_trader, percent_config):
        """测试手动基准价"""
        engine = GridTriggerEngine(percent_config, mock_trader)

        base_price = await engine.get_base_price()

        assert base_price == 600.0

    @pytest.mark.asyncio
    async def test_current_base_price(self, mock_trader):
        """测试当前价作为基准价"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            trigger_base_price_type='current'
        )

        mock_trader._get_latest_price.return_value = 605.0
        engine = GridTriggerEngine(config, mock_trader)

        base_price = await engine.get_base_price()

        assert base_price == 605.0
        mock_trader._get_latest_price.assert_called_once()

    @pytest.mark.asyncio
    async def test_cost_base_price(self, mock_trader):
        """测试成本价作为基准价"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            trigger_base_price_type='cost'
        )

        mock_trader.base_price = 595.0
        engine = GridTriggerEngine(config, mock_trader)

        base_price = await engine.get_base_price()

        assert base_price == 595.0

    @pytest.mark.asyncio
    async def test_avg_24h_base_price(self, mock_trader):
        """测试24小时均价作为基准价"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            trigger_base_price_type='avg_24h'
        )

        # 模拟24小时K线数据
        klines = [[0, 0, 0, 0, price, 0] for price in range(595, 619)]  # 24个K线
        mock_trader.exchange.fetch_ohlcv.return_value = klines

        engine = GridTriggerEngine(config, mock_trader)
        base_price = await engine.get_base_price()

        # 预期均价 = (595 + 596 + ... + 618) / 24 = 606.5
        assert 606.0 <= base_price <= 607.0


class TestTriggerLevelCalculation:
    """触发价位计算测试"""

    @pytest.mark.asyncio
    async def test_percent_mode_trigger_levels(self, mock_trader, percent_config):
        """测试百分比模式触发价"""
        engine = GridTriggerEngine(percent_config, mock_trader)

        sell_trigger, buy_trigger = await engine.calculate_trigger_levels()

        # 600 * (1 + 0.01) = 606
        # 600 * (1 - 0.01) = 594
        assert abs(sell_trigger - 606.0) < 0.01
        assert abs(buy_trigger - 594.0) < 0.01

    @pytest.mark.asyncio
    async def test_price_mode_trigger_levels(self, mock_trader, price_config):
        """测试价差模式触发价"""
        engine = GridTriggerEngine(price_config, mock_trader)

        sell_trigger, buy_trigger = await engine.calculate_trigger_levels()

        # 600 + 10 = 610
        # 600 - 10 = 590
        assert sell_trigger == 610.0
        assert buy_trigger == 590.0


class TestBasicSellSignal:
    """基础卖出信号测试"""

    @pytest.mark.asyncio
    async def test_sell_signal_not_triggered(self, mock_trader, percent_config):
        """测试未触发卖出"""
        engine = GridTriggerEngine(percent_config, mock_trader)

        # 当前价 < 触发价
        should_sell = await engine.check_sell_signal(605.0)

        assert should_sell is False

    @pytest.mark.asyncio
    async def test_sell_signal_triggered(self, mock_trader, percent_config):
        """测试触发卖出"""
        engine = GridTriggerEngine(percent_config, mock_trader)

        # 当前价 >= 触发价 (606)
        should_sell = await engine.check_sell_signal(606.5)

        assert should_sell is True


class TestPullbackSellSignal:
    """回落卖出信号测试"""

    @pytest.mark.asyncio
    async def test_pullback_sell_monitoring(self, mock_trader):
        """测试回落卖出监测启动"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            grid_type='percent',
            trigger_base_price_type='manual',
            trigger_base_price=600.0,
            rise_sell_percent=1.0,
            enable_pullback_sell=True,
            pullback_sell_percent=0.5  # 从最高点回落0.5%
        )

        engine = GridTriggerEngine(config, mock_trader)

        # 第1次：价格达到606（触发价），开始监测
        should_sell = await engine.check_sell_signal(606.0)
        assert should_sell is False  # 未回落，不卖
        assert engine.is_monitoring_sell is True
        assert engine.highest_price == 606.0

    @pytest.mark.asyncio
    async def test_pullback_sell_highest_update(self, mock_trader):
        """测试最高价更新"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            grid_type='percent',
            trigger_base_price_type='manual',
            trigger_base_price=600.0,
            rise_sell_percent=1.0,
            enable_pullback_sell=True,
            pullback_sell_percent=0.5
        )

        engine = GridTriggerEngine(config, mock_trader)

        # 价格逐步上涨
        await engine.check_sell_signal(606.0)  # 开始监测
        await engine.check_sell_signal(608.0)  # 更新最高价
        await engine.check_sell_signal(610.0)  # 再次更新

        assert engine.highest_price == 610.0

    @pytest.mark.asyncio
    async def test_pullback_sell_triggered(self, mock_trader):
        """测试回落卖出触发"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            grid_type='percent',
            trigger_base_price_type='manual',
            trigger_base_price=600.0,
            rise_sell_percent=1.0,
            enable_pullback_sell=True,
            pullback_sell_percent=0.5  # 回落0.5%
        )

        engine = GridTriggerEngine(config, mock_trader)

        # 价格上涨到610
        await engine.check_sell_signal(610.0)
        assert engine.highest_price == 610.0

        # 价格回落到606.95（从610回落0.5%）
        # 回落触发价 = 610 * (1 - 0.005) = 606.95
        should_sell = await engine.check_sell_signal(606.9)

        assert should_sell is True
        assert engine.highest_price is None  # 已重置
        assert engine.is_monitoring_sell is False


class TestBasicBuySignal:
    """基础买入信号测试"""

    @pytest.mark.asyncio
    async def test_buy_signal_not_triggered(self, mock_trader, percent_config):
        """测试未触发买入"""
        engine = GridTriggerEngine(percent_config, mock_trader)

        # 当前价 > 触发价
        should_buy = await engine.check_buy_signal(595.0)

        assert should_buy is False

    @pytest.mark.asyncio
    async def test_buy_signal_triggered(self, mock_trader, percent_config):
        """测试触发买入"""
        engine = GridTriggerEngine(percent_config, mock_trader)

        # 当前价 <= 触发价 (594)
        should_buy = await engine.check_buy_signal(593.5)

        assert should_buy is True


class TestReboundBuySignal:
    """拐点买入信号测试"""

    @pytest.mark.asyncio
    async def test_rebound_buy_monitoring(self, mock_trader):
        """测试拐点买入监测启动"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            grid_type='percent',
            trigger_base_price_type='manual',
            trigger_base_price=600.0,
            fall_buy_percent=1.0,
            enable_rebound_buy=True,
            rebound_buy_percent=0.5  # 从最低点反弹0.5%
        )

        engine = GridTriggerEngine(config, mock_trader)

        # 价格跌到594（触发价），开始监测
        should_buy = await engine.check_buy_signal(594.0)
        assert should_buy is False  # 未反弹，不买
        assert engine.is_monitoring_buy is True
        assert engine.lowest_price == 594.0

    @pytest.mark.asyncio
    async def test_rebound_buy_lowest_update(self, mock_trader):
        """测试最低价更新"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            grid_type='percent',
            trigger_base_price_type='manual',
            trigger_base_price=600.0,
            fall_buy_percent=1.0,
            enable_rebound_buy=True,
            rebound_buy_percent=0.5
        )

        engine = GridTriggerEngine(config, mock_trader)

        # 价格逐步下跌
        await engine.check_buy_signal(594.0)  # 开始监测
        await engine.check_buy_signal(592.0)  # 更新最低价
        await engine.check_buy_signal(590.0)  # 再次更新

        assert engine.lowest_price == 590.0

    @pytest.mark.asyncio
    async def test_rebound_buy_triggered(self, mock_trader):
        """测试拐点买入触发"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            grid_type='percent',
            trigger_base_price_type='manual',
            trigger_base_price=600.0,
            fall_buy_percent=1.0,
            enable_rebound_buy=True,
            rebound_buy_percent=0.5  # 反弹0.5%
        )

        engine = GridTriggerEngine(config, mock_trader)

        # 价格跌到590
        await engine.check_buy_signal(590.0)
        assert engine.lowest_price == 590.0

        # 价格反弹到592.95（从590反弹0.5%）
        # 反弹触发价 = 590 * (1 + 0.005) = 592.95
        should_buy = await engine.check_buy_signal(593.0)

        assert should_buy is True
        assert engine.lowest_price is None  # 已重置
        assert engine.is_monitoring_buy is False


class TestPriceRangeCheck:
    """价格区间检查测试"""

    def test_price_below_min(self, mock_trader):
        """测试价格低于最低限制"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            price_min=500.0,
            price_max=700.0
        )

        engine = GridTriggerEngine(config, mock_trader)

        assert engine.check_price_range(450.0) is False
        assert engine.check_price_range(550.0) is True

    def test_price_above_max(self, mock_trader):
        """测试价格高于最高限制"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            price_min=500.0,
            price_max=700.0
        )

        engine = GridTriggerEngine(config, mock_trader)

        assert engine.check_price_range(750.0) is False
        assert engine.check_price_range(650.0) is True

    def test_price_no_limits(self, mock_trader, percent_config):
        """测试无价格限制"""
        engine = GridTriggerEngine(percent_config, mock_trader)

        assert engine.check_price_range(100.0) is True
        assert engine.check_price_range(10000.0) is True


class TestStateManagement:
    """状态管理测试"""

    def test_reset_monitoring_state(self, mock_trader, percent_config):
        """测试重置监测状态"""
        engine = GridTriggerEngine(percent_config, mock_trader)

        # 设置一些状态
        engine.highest_price = 610.0
        engine.lowest_price = 590.0
        engine.is_monitoring_sell = True
        engine.is_monitoring_buy = True

        # 重置
        engine.reset_monitoring_state()

        assert engine.highest_price is None
        assert engine.lowest_price is None
        assert engine.is_monitoring_sell is False
        assert engine.is_monitoring_buy is False

    def test_get_status(self, mock_trader, percent_config):
        """测试获取状态"""
        engine = GridTriggerEngine(percent_config, mock_trader)

        engine.base_price = 600.0
        engine.sell_trigger_price = 606.0
        engine.buy_trigger_price = 594.0
        engine.highest_price = 610.0

        status = engine.get_status()

        assert status['base_price'] == 600.0
        assert status['sell_trigger'] == 606.0
        assert status['buy_trigger'] == 594.0
        assert status['highest_price'] == 610.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
