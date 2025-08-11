"""
精细化风控机制测试
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from risk_manager import AdvancedRiskManager, RiskState
from config import TradingConfig


@pytest.fixture
def mock_trader():
    """创建模拟的交易器实例"""
    trader = MagicMock()
    trader.config = TradingConfig()
    trader.logger = MagicMock()
    return trader


@pytest.fixture
def risk_manager(mock_trader):
    """创建风控管理器实例"""
    rm = AdvancedRiskManager(mock_trader)
    rm.logger = MagicMock()  # 模拟logger
    return rm


class TestRiskState:
    """测试风险状态枚举"""
    
    def test_risk_state_values(self):
        """测试风险状态枚举值"""
        assert RiskState.ALLOW_ALL.value == 0
        assert RiskState.ALLOW_SELL_ONLY.value == 1
        assert RiskState.ALLOW_BUY_ONLY.value == 2
    
    def test_risk_state_names(self):
        """测试风险状态名称"""
        assert RiskState.ALLOW_ALL.name == "ALLOW_ALL"
        assert RiskState.ALLOW_SELL_ONLY.name == "ALLOW_SELL_ONLY"
        assert RiskState.ALLOW_BUY_ONLY.name == "ALLOW_BUY_ONLY"


class TestAdvancedRiskManager:
    """测试高级风控管理器"""
    
    @pytest.mark.asyncio
    async def test_check_position_limits_normal_range(self, risk_manager):
        """测试正常仓位范围的风控检查"""
        # 模拟正常仓位比例 (50%)
        risk_manager._get_position_ratio = AsyncMock(return_value=0.5)
        
        # 模拟账户快照
        mock_spot_balance = {'free': {'BNB': 1.0, 'USDT': 1000.0}}
        mock_funding_balance = {'BNB': 0.0, 'USDT': 0.0}

        result = await risk_manager.check_position_limits(mock_spot_balance, mock_funding_balance)
        assert result == RiskState.ALLOW_ALL
    
    @pytest.mark.asyncio
    async def test_check_position_limits_high_position(self, risk_manager):
        """测试高仓位的风控检查"""
        # 模拟高仓位比例 (95%)
        risk_manager._get_position_ratio = AsyncMock(return_value=0.95)

        # 模拟账户快照
        mock_spot_balance = {'free': {'BNB': 1.0, 'USDT': 1000.0}}
        mock_funding_balance = {'BNB': 0.0, 'USDT': 0.0}

        result = await risk_manager.check_position_limits(mock_spot_balance, mock_funding_balance)
        assert result == RiskState.ALLOW_SELL_ONLY
    
    @pytest.mark.asyncio
    async def test_check_position_limits_low_position(self, risk_manager):
        """测试低仓位的风控检查"""
        # 模拟低仓位比例 (5%)
        risk_manager._get_position_ratio = AsyncMock(return_value=0.05)

        # 模拟账户快照
        mock_spot_balance = {'free': {'BNB': 1.0, 'USDT': 1000.0}}
        mock_funding_balance = {'BNB': 0.0, 'USDT': 0.0}

        result = await risk_manager.check_position_limits(mock_spot_balance, mock_funding_balance)
        assert result == RiskState.ALLOW_BUY_ONLY
    
    @pytest.mark.asyncio
    async def test_check_position_limits_boundary_values(self, risk_manager):
        """测试边界值的风控检查"""
        # 模拟账户快照
        mock_spot_balance = {'free': {'BNB': 1.0, 'USDT': 1000.0}}
        mock_funding_balance = {'BNB': 0.0, 'USDT': 0.0}

        # 测试刚好等于最大仓位比例
        risk_manager._get_position_ratio = AsyncMock(return_value=0.9)
        result = await risk_manager.check_position_limits(mock_spot_balance, mock_funding_balance)
        assert result == RiskState.ALLOW_ALL

        # 测试刚好超过最大仓位比例
        risk_manager._get_position_ratio = AsyncMock(return_value=0.901)
        result = await risk_manager.check_position_limits(mock_spot_balance, mock_funding_balance)
        assert result == RiskState.ALLOW_SELL_ONLY

        # 测试刚好等于最小仓位比例
        risk_manager._get_position_ratio = AsyncMock(return_value=0.1)
        result = await risk_manager.check_position_limits(mock_spot_balance, mock_funding_balance)
        assert result == RiskState.ALLOW_ALL

        # 测试刚好低于最小仓位比例
        risk_manager._get_position_ratio = AsyncMock(return_value=0.099)
        result = await risk_manager.check_position_limits(mock_spot_balance, mock_funding_balance)
        assert result == RiskState.ALLOW_BUY_ONLY
    
    @pytest.mark.asyncio
    async def test_check_position_limits_exception_handling(self, risk_manager):
        """测试异常处理"""
        # 模拟获取仓位比例时抛出异常
        risk_manager._get_position_ratio = AsyncMock(side_effect=Exception("Test error"))

        # 模拟账户快照
        mock_spot_balance = {'free': {'BNB': 1.0, 'USDT': 1000.0}}
        mock_funding_balance = {'BNB': 0.0, 'USDT': 0.0}

        result = await risk_manager.check_position_limits(mock_spot_balance, mock_funding_balance)
        # 异常时应该返回ALLOW_ALL以避免卡死
        assert result == RiskState.ALLOW_ALL
    
    @pytest.mark.asyncio
    async def test_multi_layer_check_backward_compatibility(self, risk_manager):
        """测试向后兼容的multi_layer_check方法"""
        # 模拟exchange的异步方法
        risk_manager.trader.exchange.fetch_balance = AsyncMock(return_value={'free': {'BNB': 1.0, 'USDT': 1000.0}})
        risk_manager.trader.exchange.fetch_funding_balance = AsyncMock(return_value={'BNB': 0.0, 'USDT': 0.0})

        # 测试正常范围
        risk_manager._get_position_ratio = AsyncMock(return_value=0.5)
        result = await risk_manager.multi_layer_check()
        assert result == False  # ALLOW_ALL -> False

        # 测试高仓位
        risk_manager._get_position_ratio = AsyncMock(return_value=0.95)
        result = await risk_manager.multi_layer_check()
        assert result == True  # ALLOW_SELL_ONLY -> True

        # 测试低仓位
        risk_manager._get_position_ratio = AsyncMock(return_value=0.05)
        result = await risk_manager.multi_layer_check()
        assert result == True  # ALLOW_BUY_ONLY -> True
    
    @pytest.mark.asyncio
    async def test_position_ratio_logging(self, risk_manager):
        """测试仓位比例变化时的日志记录"""
        # 模拟账户快照
        mock_spot_balance = {'free': {'BNB': 1.0, 'USDT': 1000.0}}
        mock_funding_balance = {'BNB': 0.0, 'USDT': 0.0}

        # 首次调用
        risk_manager._get_position_ratio = AsyncMock(return_value=0.5)
        await risk_manager.check_position_limits(mock_spot_balance, mock_funding_balance)

        # 仓位比例变化不大，不应该记录日志
        risk_manager._get_position_ratio = AsyncMock(return_value=0.5005)
        await risk_manager.check_position_limits(mock_spot_balance, mock_funding_balance)

        # 仓位比例变化较大，应该记录日志
        risk_manager._get_position_ratio = AsyncMock(return_value=0.52)
        await risk_manager.check_position_limits(mock_spot_balance, mock_funding_balance)
        
        # 验证日志调用（使用risk_manager自己的logger）
        assert risk_manager.logger.info.called


class TestRiskStateIntegration:
    """测试风控状态的集成场景"""
    
    @pytest.mark.asyncio
    async def test_risk_state_priority(self, risk_manager):
        """测试风控状态的优先级"""
        # 当仓位既超过上限又低于下限时（理论上不可能，但测试边界情况）
        # 应该优先检查上限
        with patch.object(risk_manager, '_get_position_ratio') as mock_ratio:
            # 模拟一个不可能的情况用于测试优先级
            mock_ratio.return_value = 1.5  # 150%仓位（不可能但用于测试）

            # 模拟账户快照
            mock_spot_balance = {'free': {'BNB': 1.0, 'USDT': 1000.0}}
            mock_funding_balance = {'BNB': 0.0, 'USDT': 0.0}

            result = await risk_manager.check_position_limits(mock_spot_balance, mock_funding_balance)
            # 应该返回ALLOW_SELL_ONLY，因为优先检查上限
            assert result == RiskState.ALLOW_SELL_ONLY
    
    def test_risk_state_string_representation(self):
        """测试风控状态的字符串表示"""
        assert str(RiskState.ALLOW_ALL) == "RiskState.ALLOW_ALL"
        assert str(RiskState.ALLOW_SELL_ONLY) == "RiskState.ALLOW_SELL_ONLY"
        assert str(RiskState.ALLOW_BUY_ONLY) == "RiskState.ALLOW_BUY_ONLY"


if __name__ == '__main__':
    pytest.main([__file__])
