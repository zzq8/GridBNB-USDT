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
from src.strategies.risk_manager import RiskState
from src.strategies.position_controller_s1 import PositionControllerS1


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
        # 关键修复: exchange 应该是 AsyncMock,它的方法也应该是 AsyncMock
        trader.exchange = AsyncMock()
        trader.current_price = 683.0
        trader.symbol_info = {
            'limits': {
                'cost': {'min': 10.0},
                'amount': {'min': 0.001}
            }
        }
        # 确保余额充足,避免触发资金转移逻辑
        # 买入1.5个BNB约需 1.5 * 683 = 1024.5 USDT
        trader.get_available_balance = AsyncMock(side_effect=lambda asset:
            2000.0 if asset == 'USDT' else 10.0  # 提高USDT余额到2000
        )
        trader._adjust_amount_precision = MagicMock(side_effect=lambda x: round(x, 3))
        # 添加 _pre_transfer_funds 的 AsyncMock (以防万一)
        trader._pre_transfer_funds = AsyncMock()
        # 添加 _transfer_excess_funds 的 AsyncMock
        trader._transfer_excess_funds = AsyncMock()
        # 添加 order_tracker
        trader.order_tracker = MagicMock()
        trader.order_tracker.add_trade = MagicMock()
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

        # 显式设置 create_market_order 的返回值
        mock_trader.exchange.create_market_order.return_value = mock_order

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
        trader.config = MagicMock()
        trader.config.MAX_SINGLE_TRANSFER = 5000.0  # 模拟配置
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


class TestS1EdgeCases:
    """测试S1策略的边界情况"""

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
        trader.risk_manager = AsyncMock()
        return trader

    @pytest.fixture
    def controller(self, mock_trader):
        """创建 controller"""
        return PositionControllerS1(mock_trader)

    @pytest.mark.asyncio
    async def test_price_exactly_at_high_level(self, controller, mock_trader):
        """测试价格正好在高点时不触发"""
        controller.s1_daily_high = 683.0
        controller.s1_daily_low = 650.0
        mock_trader.current_price = 683.0

        mock_spot_balance = {'total': {'USDT': 1000.0, 'BNB': 10.0}}
        mock_funding_balance = {}

        mock_trader.exchange.fetch_balance = AsyncMock(return_value=mock_spot_balance)
        mock_trader.exchange.fetch_funding_balance = AsyncMock(return_value=mock_funding_balance)
        mock_trader.risk_manager._get_position_ratio = AsyncMock(return_value=0.60)
        mock_trader.risk_manager._get_position_value = AsyncMock(return_value=6000.0)
        mock_trader._get_pair_specific_assets_value = AsyncMock(return_value=10000.0)

        controller._execute_s1_adjustment = AsyncMock()

        await controller.check_and_execute(RiskState.ALLOW_ALL)

        # 价格正好在高点时不应触发
        controller._execute_s1_adjustment.assert_not_called()

    @pytest.mark.asyncio
    async def test_price_exactly_at_low_level(self, controller, mock_trader):
        """测试价格正好在低点时不触发"""
        controller.s1_daily_high = 700.0
        controller.s1_daily_low = 650.0
        mock_trader.current_price = 650.0

        mock_spot_balance = {'total': {'USDT': 5000.0, 'BNB': 5.0}}
        mock_funding_balance = {}

        mock_trader.exchange.fetch_balance = AsyncMock(return_value=mock_spot_balance)
        mock_trader.exchange.fetch_funding_balance = AsyncMock(return_value=mock_funding_balance)
        mock_trader.risk_manager._get_position_ratio = AsyncMock(return_value=0.30)
        mock_trader.risk_manager._get_position_value = AsyncMock(return_value=3000.0)
        mock_trader._get_pair_specific_assets_value = AsyncMock(return_value=10000.0)

        controller._execute_s1_adjustment = AsyncMock()

        await controller.check_and_execute(RiskState.ALLOW_ALL)

        # 价格正好在低点时不应触发
        controller._execute_s1_adjustment.assert_not_called()

    @pytest.mark.asyncio
    async def test_position_at_target_no_adjustment(self, controller, mock_trader):
        """测试仓位已经在目标比例时不调整"""
        controller.s1_daily_high = 700.0
        controller.s1_daily_low = 650.0
        mock_trader.current_price = 710.0  # 突破高点

        mock_spot_balance = {'total': {'USDT': 1000.0, 'BNB': 10.0}}
        mock_funding_balance = {}

        mock_trader.exchange.fetch_balance = AsyncMock(return_value=mock_spot_balance)
        mock_trader.exchange.fetch_funding_balance = AsyncMock(return_value=mock_funding_balance)
        mock_trader.risk_manager._get_position_ratio = AsyncMock(return_value=0.50)  # 正好50%
        mock_trader.risk_manager._get_position_value = AsyncMock(return_value=5000.0)
        mock_trader._get_pair_specific_assets_value = AsyncMock(return_value=10000.0)

        controller._execute_s1_adjustment = AsyncMock()

        await controller.check_and_execute(RiskState.ALLOW_ALL)

        # 仓位已经在目标比例，不应调整
        controller._execute_s1_adjustment.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_price_skips_check(self, controller, mock_trader):
        """测试无效价格时跳过检查"""
        controller.s1_daily_high = 700.0
        controller.s1_daily_low = 650.0
        mock_trader.current_price = 0.0  # 无效价格

        controller._execute_s1_adjustment = AsyncMock()

        await controller.check_and_execute(RiskState.ALLOW_ALL)

        # 无效价格应跳过检查
        controller._execute_s1_adjustment.assert_not_called()

    @pytest.mark.asyncio
    async def test_zero_total_assets_skips_check(self, controller, mock_trader):
        """测试总资产为零时跳过检查"""
        controller.s1_daily_high = 700.0
        controller.s1_daily_low = 650.0
        mock_trader.current_price = 710.0

        mock_spot_balance = {'total': {'USDT': 0.0, 'BNB': 0.0}}
        mock_funding_balance = {}

        mock_trader.exchange.fetch_balance = AsyncMock(return_value=mock_spot_balance)
        mock_trader.exchange.fetch_funding_balance = AsyncMock(return_value=mock_funding_balance)
        mock_trader.risk_manager._get_position_ratio = AsyncMock(return_value=0.0)
        mock_trader.risk_manager._get_position_value = AsyncMock(return_value=0.0)
        mock_trader._get_pair_specific_assets_value = AsyncMock(return_value=0.0)

        controller._execute_s1_adjustment = AsyncMock()

        await controller.check_and_execute(RiskState.ALLOW_ALL)

        # 总资产为零应跳过检查
        controller._execute_s1_adjustment.assert_not_called()


class TestS1Integration:
    """测试S1策略的集成场景"""

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
        trader.symbol_info = {
            'limits': {
                'cost': {'min': 10.0},
                'amount': {'min': 0.001}
            }
        }
        trader._adjust_amount_precision = MagicMock(side_effect=lambda x: round(x, 3))
        trader.get_available_balance = AsyncMock(return_value=2000.0)
        trader._pre_transfer_funds = AsyncMock()
        trader._transfer_excess_funds = AsyncMock()
        trader.order_tracker = MagicMock()
        trader.order_tracker.add_trade = MagicMock()
        return trader

    @pytest.fixture
    def controller(self, mock_trader):
        """创建 controller"""
        return PositionControllerS1(mock_trader)

    @pytest.mark.asyncio
    async def test_complete_s1_buy_flow(self, controller, mock_trader):
        """测试完整的S1买入流程"""
        # 1. 首次更新S1水平
        mock_klines = [[1634000000000 + i * 86400000, 680, 690, 670, 683, 1000]
                       for i in range(54)]
        mock_trader.exchange.fetch_ohlcv = AsyncMock(return_value=mock_klines)

        await controller.update_daily_s1_levels()
        assert controller.s1_daily_high is not None
        assert controller.s1_daily_low is not None

        # 2. 设置买入条件
        controller.s1_daily_low = 650.0
        mock_trader.current_price = 640.0

        # 3. 设置仓位信息
        mock_spot_balance = {'total': {'USDT': 5000.0, 'BNB': 5.0}}
        mock_funding_balance = {}
        mock_trader.exchange.fetch_balance = AsyncMock(return_value=mock_spot_balance)
        mock_trader.exchange.fetch_funding_balance = AsyncMock(return_value=mock_funding_balance)
        mock_trader.risk_manager = AsyncMock()
        mock_trader.risk_manager._get_position_ratio = AsyncMock(return_value=0.30)
        mock_trader.risk_manager._get_position_value = AsyncMock(return_value=3000.0)
        mock_trader._get_pair_specific_assets_value = AsyncMock(return_value=10000.0)

        # 确保 get_available_balance 返回足够的余额
        mock_trader.get_available_balance = AsyncMock(return_value=5000.0)

        # 4. Mock 订单执行
        mock_order = {
            'id': '12345',
            'side': 'buy',
            'filled': 1.0,
            'average': 640.0
        }
        mock_trader.exchange.create_market_order = AsyncMock(return_value=mock_order)

        # 5. 执行检查
        await controller.check_and_execute(RiskState.ALLOW_ALL)

        # 6. 验证买入被执行
        mock_trader.exchange.create_market_order.assert_called_once()

        # 7. 验证交易被记录
        assert mock_trader.order_tracker.add_trade.called

    @pytest.mark.asyncio
    async def test_update_daily_s1_levels_time_check(self, controller, mock_trader):
        """测试每日更新时间检查逻辑"""
        # 第一次更新
        mock_klines = [[1634000000000 + i * 86400000, 680, 690, 670, 683, 1000]
                       for i in range(54)]
        mock_trader.exchange.fetch_ohlcv = AsyncMock(return_value=mock_klines)

        await controller.update_daily_s1_levels()
        assert mock_trader.exchange.fetch_ohlcv.call_count == 1

        # 立即再次调用，不应触发更新
        await controller.update_daily_s1_levels()
        assert mock_trader.exchange.fetch_ohlcv.call_count == 1  # 仍然是1次

        # 模拟时间过去
        controller.s1_last_data_update_ts = time.time() - (24 * 60 * 60)  # 24小时前

        await controller.update_daily_s1_levels()
        assert mock_trader.exchange.fetch_ohlcv.call_count == 2  # 应该增加到2次

    @pytest.mark.asyncio
    async def test_execute_s1_adjustment_logs_to_order_tracker(self, controller, mock_trader):
        """测试S1订单被正确记录到OrderTracker"""
        mock_order = {
            'id': 'test_order_123',
            'side': 'buy',
            'filled': 1.5,
            'average': 683.0
        }
        mock_trader.exchange.create_market_order = AsyncMock(return_value=mock_order)

        result = await controller._execute_s1_adjustment('BUY', 1.5)

        assert result is True
        # 验证add_trade被调用
        assert mock_trader.order_tracker.add_trade.called
        call_args = mock_trader.order_tracker.add_trade.call_args[0][0]
        assert call_args['strategy'] == 'S1'
        assert call_args['side'] == 'BUY'
        assert call_args['order_id'] == 'test_order_123'


class TestS1ErrorHandling:
    """测试S1策略的错误处理"""

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
        return trader

    @pytest.fixture
    def controller(self, mock_trader):
        """创建 controller"""
        return PositionControllerS1(mock_trader)

    @pytest.mark.asyncio
    async def test_fetch_ohlcv_error_handling(self, controller, mock_trader):
        """测试K线数据获取失败时的错误处理"""
        mock_trader.exchange.fetch_ohlcv = AsyncMock(side_effect=Exception("API error"))

        result = await controller._fetch_and_calculate_s1_levels()

        assert result is False
        assert controller.s1_daily_high is None
        assert controller.s1_daily_low is None

    @pytest.mark.asyncio
    async def test_check_and_execute_exchange_error(self, controller, mock_trader):
        """测试检查执行时交易所API错误"""
        controller.s1_daily_high = 700.0
        controller.s1_daily_low = 650.0
        mock_trader.current_price = 710.0

        mock_trader.exchange.fetch_balance = AsyncMock(side_effect=Exception("Network error"))

        # 应该捕获异常，不抛出
        await controller.check_and_execute(RiskState.ALLOW_ALL)
        # 如果没有抛出异常，测试通过

    @pytest.mark.asyncio
    async def test_execute_order_exception(self, controller, mock_trader):
        """测试订单执行异常处理"""
        mock_trader.exchange.create_market_order = AsyncMock(side_effect=Exception("Order failed"))
        mock_trader.symbol_info = {
            'limits': {
                'cost': {'min': 10.0},
                'amount': {'min': 0.001}
            }
        }
        mock_trader._adjust_amount_precision = MagicMock(side_effect=lambda x: round(x, 3))
        mock_trader.get_available_balance = AsyncMock(return_value=2000.0)

        result = await controller._execute_s1_adjustment('BUY', 1.0)

        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
