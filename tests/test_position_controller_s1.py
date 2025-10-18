"""
PositionControllerS1 单元测试

测试S1仓位控制策略的核心功能,包括:
- 初始化和配置
- 52日高低点计算
- 仓位检查和调整逻辑
- 订单执行
- 资金转移
"""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from risk_manager import RiskState
from position_controller_s1 import PositionControllerS1


class TestPositionControllerS1Init:
    """测试 PositionControllerS1 初始化"""

    @pytest.fixture
    def mock_trader(self):
        """创建 mock 的 trader 实例"""
        trader = MagicMock()
        trader.config = MagicMock()
        trader.symbol = 'BNB/USDT'
        trader.base_asset = 'BNB'
        trader.quote_asset = 'USDT'
        trader.exchange = AsyncMock()
        trader.current_price = 683.0
        return trader

    def test_init_basic(self, mock_trader):
        """测试基础初始化"""
        controller = PositionControllerS1(mock_trader)

        assert controller.trader == mock_trader
        assert controller.s1_lookback == 52
        assert controller.s1_sell_target_pct == 0.50
        assert controller.s1_buy_target_pct == 0.70
        assert controller.s1_daily_high is None
        assert controller.s1_daily_low is None


class TestS1LevelsCalculation:
    """测试52日高低点计算"""

    @pytest.fixture
    def mock_trader(self):
        """创建 mock 的 trader 实例"""
        trader = MagicMock()
        trader.config = MagicMock()
        trader.symbol = 'BNB/USDT'
        trader.base_asset = 'BNB'
        trader.quote_asset = 'USDT'
        trader.exchange = AsyncMock()
        trader.current_price = 683.0
        return trader

    @pytest.fixture
    def controller(self, mock_trader):
        """创建 PositionControllerS1 实例"""
        return PositionControllerS1(mock_trader)

    @pytest.mark.asyncio
    async def test_fetch_and_calculate_s1_levels_success(self, controller, mock_trader):
        """测试成功计算52日高低点"""
        # 生成54根K线数据 (52 + 2 buffer)
        mock_klines = []
        for i in range(54):
            # 格式: [timestamp, open, high, low, close, volume]
            mock_klines.append([
                1634000000000 + i * 86400000,  # timestamp
                680.0,  # open
                700.0 - i,  # high (递减)
                650.0 + i * 0.5,  # low (递增)
                683.0,  # close
                1000.0  # volume
            ])

        mock_trader.exchange.fetch_ohlcv = AsyncMock(return_value=mock_klines)

        result = await controller._fetch_and_calculate_s1_levels()

        assert result is True
        # 验证高点是最高的 high 值
        expected_high = max(k[2] for k in mock_klines[-53:-1])  # 倒数第2根往前52根
        assert controller.s1_daily_high == expected_high

        # 验证低点是最低的 low 值
        expected_low = min(k[3] for k in mock_klines[-53:-1])
        assert controller.s1_daily_low == expected_low

    @pytest.mark.asyncio
    async def test_fetch_and_calculate_insufficient_data(self, controller, mock_trader):
        """测试K线数据不足的情况"""
        # 只返回10根K线
        mock_klines = [[1634000000000 + i * 86400000, 680, 690, 670, 683, 1000]
                       for i in range(10)]

        mock_trader.exchange.fetch_ohlcv = AsyncMock(return_value=mock_klines)

        result = await controller._fetch_and_calculate_s1_levels()

        assert result is False
        assert controller.s1_daily_high is None
        assert controller.s1_daily_low is None

    @pytest.mark.asyncio
    async def test_update_daily_s1_levels(self, controller, mock_trader):
        """测试每日更新触发"""
        # 模拟超过更新间隔
        controller.s1_last_data_update_ts = time.time() - (24 * 60 * 60)  # 24小时前

        mock_klines = [[1634000000000 + i * 86400000, 680, 690, 670, 683, 1000]
                       for i in range(54)]
        mock_trader.exchange.fetch_ohlcv = AsyncMock(return_value=mock_klines)

        await controller.update_daily_s1_levels()

        # 应该触发更新
        assert controller.s1_daily_high is not None
        assert controller.s1_daily_low is not None


class TestS1PositionCheck:
    """测试S1仓位检查逻辑"""

    @pytest.fixture
    def mock_trader(self):
        """创建完整配置的 mock trader"""
        trader = MagicMock()
        trader.config = MagicMock()
        trader.symbol = 'BNB/USDT'
        trader.base_asset = 'BNB'
        trader.quote_asset = 'USDT'
        trader.exchange = AsyncMock()
        trader.current_price = 683.0
        trader.risk_manager = AsyncMock()
        trader.get_available_balance = AsyncMock(return_value=1000.0)
        trader._get_pair_specific_assets_value = AsyncMock(return_value=10000.0)
        return trader

    @pytest.fixture
    def controller(self, mock_trader):
        """创建已初始化的 controller"""
        controller = PositionControllerS1(mock_trader)
        controller.s1_daily_high = 700.0
        controller.s1_daily_low = 650.0
        return controller

    @pytest.mark.asyncio
    async def test_check_no_levels_available(self, controller, mock_trader):
        """测试没有高低点数据时的行为"""
        controller.s1_daily_high = None
        controller.s1_daily_low = None

        await controller.check_and_execute(RiskState.ALLOW_ALL)

        # 不应该执行任何操作
        mock_trader.exchange.create_market_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_sell_condition_triggered(self, controller, mock_trader):
        """测试卖出条件触发"""
        # 设置价格突破高点
        mock_trader.current_price = 710.0  # > 700.0 (s1_daily_high)

        # 设置仓位比例高于卖出目标
        mock_spot_balance = {'total': {'USDT': 1000.0, 'BNB': 10.0}}
        mock_funding_balance = {}

        mock_trader.exchange.fetch_balance = AsyncMock(return_value=mock_spot_balance)
        mock_trader.exchange.fetch_funding_balance = AsyncMock(return_value=mock_funding_balance)

        # 设置仓位比例为60% (高于50%的卖出目标)
        mock_trader.risk_manager._get_position_ratio = AsyncMock(return_value=0.60)
        mock_trader.risk_manager._get_position_value = AsyncMock(return_value=6000.0)
        mock_trader._get_pair_specific_assets_value = AsyncMock(return_value=10000.0)

        # Mock check_s1_balance_and_transfer
        controller.check_s1_balance_and_transfer = AsyncMock(return_value=10.0)

        # Mock _execute_s1_adjustment
        controller._execute_s1_adjustment = AsyncMock(return_value=True)

        await controller.check_and_execute(RiskState.ALLOW_ALL)

        # 验证执行了卖出调整
        controller._execute_s1_adjustment.assert_called_once()
        call_args = controller._execute_s1_adjustment.call_args[0]
        assert call_args[0] == 'SELL'

    @pytest.mark.asyncio
    async def test_check_buy_condition_triggered(self, controller, mock_trader):
        """测试买入条件触发"""
        # 设置价格跌破低点
        mock_trader.current_price = 640.0  # < 650.0 (s1_daily_low)

        # 设置仓位比例低于买入目标
        mock_spot_balance = {'total': {'USDT': 5000.0, 'BNB': 5.0}}
        mock_funding_balance = {}

        mock_trader.exchange.fetch_balance = AsyncMock(return_value=mock_spot_balance)
        mock_trader.exchange.fetch_funding_balance = AsyncMock(return_value=mock_funding_balance)

        # 设置仓位比例为30% (低于70%的买入目标)
        mock_trader.risk_manager._get_position_ratio = AsyncMock(return_value=0.30)
        mock_trader.risk_manager._get_position_value = AsyncMock(return_value=3000.0)
        mock_trader._get_pair_specific_assets_value = AsyncMock(return_value=10000.0)

        # Mock _execute_s1_adjustment
        controller._execute_s1_adjustment = AsyncMock(return_value=True)

        await controller.check_and_execute(RiskState.ALLOW_ALL)

        # 验证执行了买入调整
        controller._execute_s1_adjustment.assert_called_once()
        call_args = controller._execute_s1_adjustment.call_args[0]
        assert call_args[0] == 'BUY'

    @pytest.mark.asyncio
    async def test_check_risk_state_blocks_sell(self, controller, mock_trader):
        """测试风控状态阻止卖出"""
        # 设置卖出条件
        mock_trader.current_price = 710.0

        mock_spot_balance = {'total': {'USDT': 1000.0, 'BNB': 10.0}}
        mock_funding_balance = {}

        mock_trader.exchange.fetch_balance = AsyncMock(return_value=mock_spot_balance)
        mock_trader.exchange.fetch_funding_balance = AsyncMock(return_value=mock_funding_balance)
        mock_trader.risk_manager._get_position_ratio = AsyncMock(return_value=0.60)
        mock_trader.risk_manager._get_position_value = AsyncMock(return_value=6000.0)
        mock_trader._get_pair_specific_assets_value = AsyncMock(return_value=10000.0)

        controller.check_s1_balance_and_transfer = AsyncMock(return_value=10.0)
        controller._execute_s1_adjustment = AsyncMock(return_value=True)

        # 使用 ALLOW_BUY_ONLY 风控状态
        await controller.check_and_execute(RiskState.ALLOW_BUY_ONLY)

        # 卖出应该被阻止
        controller._execute_s1_adjustment.assert_not_called()


class TestS1OrderExecution:
    """测试S1订单执行"""

    @pytest.fixture
    def mock_trader(self):
        """创建 mock trader"""
        trader = MagicMock()
        trader.config = MagicMock()
        trader.symbol = 'BNB/USDT'
        trader.base_asset = 'BNB'
        trader.quote_asset = 'USDT'
        trader.exchange = AsyncMock()
        trader.current_price = 683.0
        trader.symbol_info = {
            'limits': {
                'cost': {'min': 10.0},
                'amount': {'min': 0.001}
            }
        }
        trader.get_available_balance = AsyncMock(side_effect=lambda asset:
            1000.0 if asset == 'USDT' else 10.0
        )
        trader._adjust_amount_precision = MagicMock(side_effect=lambda x: round(x, 3))
        return trader

    @pytest.fixture
    def controller(self, mock_trader):
        """创建 controller"""
        return PositionControllerS1(mock_trader)

    @pytest.mark.asyncio
    async def test_execute_s1_buy_order_success(self, controller, mock_trader):
        """测试成功执行买入订单"""
        mock_order = {
            'id': '12345',
            'symbol': 'BNB/USDT',
            'side': 'buy',
            'amount': 1.0,
            'filled': 1.0,
            'average': 683.0
        }

        mock_trader.exchange.create_market_order = AsyncMock(return_value=mock_order)

        result = await controller._execute_s1_adjustment('BUY', 1.5)

        assert result is True
        mock_trader.exchange.create_market_order.assert_called_once()
        call_kwargs = mock_trader.exchange.create_market_order.call_args[1]
        assert call_kwargs['side'] == 'buy'

    @pytest.mark.asyncio
    async def test_execute_s1_sell_insufficient_balance(self, controller, mock_trader):
        """测试余额不足时无法执行卖出"""
        mock_trader.get_available_balance = AsyncMock(return_value=0.5)  # 余额不足

        result = await controller._execute_s1_adjustment('SELL', 1.0)

        assert result is False
        mock_trader.exchange.create_market_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_s1_buy_with_funding_transfer(self, controller, mock_trader):
        """测试买入时从理财转移资金"""
        # 初始余额不足
        balance_calls = [500.0, 1500.0]  # 第一次不足,转账后足够
        mock_trader.get_available_balance = AsyncMock(side_effect=balance_calls)

        mock_trader._pre_transfer_funds = AsyncMock()

        mock_order = {
            'id': '12345',
            'side': 'buy',
            'filled': 1.0,
            'average': 683.0
        }
        mock_trader.exchange.create_market_order = AsyncMock(return_value=mock_order)

        result = await controller._execute_s1_adjustment('BUY', 1.0)

        assert result is True
        mock_trader._pre_transfer_funds.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_s1_amount_below_minimum(self, controller, mock_trader):
        """测试数量低于最小限制"""
        result = await controller._execute_s1_adjustment('BUY', 0.0001)

        assert result is False
        mock_trader.exchange.create_market_order.assert_not_called()


class TestS1BalanceTransfer:
    """测试S1资金转移功能"""

    @pytest.fixture
    def mock_trader(self):
        """创建 mock trader"""
        trader = MagicMock()
        trader.exchange = AsyncMock()
        trader.get_available_balance = AsyncMock()
        return trader

    @pytest.fixture
    def controller(self, mock_trader):
        """创建 controller"""
        return PositionControllerS1(mock_trader)

    @pytest.mark.asyncio
    async def test_check_balance_sufficient(self, controller, mock_trader):
        """测试余额充足时不需要转移"""
        mock_trader.get_available_balance = AsyncMock(return_value=2000.0)

        balance = await controller.check_s1_balance_and_transfer(1500.0, 'USDT')

        assert balance >= 1500.0
        mock_trader.exchange.transfer_to_spot.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_balance_transfer_needed(self, controller, mock_trader):
        """测试余额不足时转移资金"""
        # 初始余额不足,转账后充足
        balance_calls = [500.0, 1800.0]
        mock_trader.get_available_balance = AsyncMock(side_effect=balance_calls)

        mock_trader.exchange.transfer_to_spot = AsyncMock()

        balance = await controller.check_s1_balance_and_transfer(1500.0, 'USDT')

        assert balance >= 1500.0
        # 验证调用了转账
        # 需要 1500 - 500 = 1000, 加20%缓冲 = 1200
        mock_trader.exchange.transfer_to_spot.assert_called()

    @pytest.mark.asyncio
    async def test_check_balance_large_amount_multiple_transfers(self, controller, mock_trader):
        """测试大额转账分批执行"""
        mock_trader.get_available_balance = AsyncMock(side_effect=[100.0, 12000.0])
        mock_trader.exchange.transfer_to_spot = AsyncMock()

        balance = await controller.check_s1_balance_and_transfer(10000.0, 'USDT')

        # 需要 10000 - 100 = 9900, 加20%缓冲 = 11880
        # 应该分成 5000 + 5000 + 1880 三次转账
        assert mock_trader.exchange.transfer_to_spot.call_count == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
