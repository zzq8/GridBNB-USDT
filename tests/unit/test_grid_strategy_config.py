"""
GridStrategyConfig 单元测试

测试配置模型的验证、序列化和业务逻辑
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.strategies.grid_strategy_config import (
    GridStrategyConfig,
    StrategyTemplates
)


class TestGridStrategyConfigBasic:
    """基础配置测试"""

    def test_minimal_config(self):
        """测试最小配置"""
        config = GridStrategyConfig(
            strategy_name="测试策略",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT"
        )

        assert config.strategy_name == "测试策略"
        assert config.symbol == "BNB/USDT"
        assert config.grid_type == 'percent'  # 默认值
        assert config.order_type == 'limit'  # 默认值

    def test_full_config(self):
        """测试完整配置"""
        config = GridStrategyConfig(
            strategy_name="完整策略",
            symbol="ETH/USDT",
            base_currency="ETH",
            quote_currency="USDT",
            grid_type='price',
            trigger_base_price_type='manual',
            trigger_base_price=3000.0,
            rise_sell_percent=50.0,
            fall_buy_percent=50.0,
            enable_pullback_sell=True,
            pullback_sell_percent=20.0,
            order_type='limit',
            buy_price_mode='bid1',
            sell_price_mode='ask1',
            amount_mode='amount',
            grid_symmetric=False,
            buy_quantity=100.0,
            sell_quantity=150.0,
            max_position=95,
            min_position=5
        )

        assert config.grid_type == 'price'
        assert config.trigger_base_price == 3000.0
        assert config.buy_quantity == 100.0
        assert config.sell_quantity == 150.0


class TestGridStrategyConfigValidation:
    """配置验证测试"""

    def test_manual_trigger_price_required(self):
        """测试手动模式必须设置基准价"""
        with pytest.raises(ValidationError) as exc_info:
            GridStrategyConfig(
                strategy_name="测试",
                symbol="BNB/USDT",
                base_currency="BNB",
                quote_currency="USDT",
                trigger_base_price_type='manual',
                # 缺少 trigger_base_price
            )

        assert "trigger_base_price" in str(exc_info.value)

    def test_asymmetric_quantities_required(self):
        """测试不对称网格必须设置买卖数量"""
        with pytest.raises(ValidationError) as exc_info:
            GridStrategyConfig(
                strategy_name="测试",
                symbol="BNB/USDT",
                base_currency="BNB",
                quote_currency="USDT",
                grid_symmetric=False,
                # 缺少 buy_quantity 和 sell_quantity
            )

        errors = str(exc_info.value)
        assert "buy_quantity" in errors or "sell_quantity" in errors

    def test_price_range_validation(self):
        """测试价格区间验证"""
        with pytest.raises(ValidationError) as exc_info:
            GridStrategyConfig(
                strategy_name="测试",
                symbol="BNB/USDT",
                base_currency="BNB",
                quote_currency="USDT",
                price_min=100.0,
                price_max=50.0  # max < min，不合法
            )

        assert "price_max" in str(exc_info.value)

    def test_position_limits_validation(self):
        """测试仓位限制验证"""
        with pytest.raises(ValidationError) as exc_info:
            GridStrategyConfig(
                strategy_name="测试",
                symbol="BNB/USDT",
                base_currency="BNB",
                quote_currency="USDT",
                min_position=80,
                max_position=50  # max < min，不合法
            )

        assert "min_position" in str(exc_info.value)

    def test_symmetric_quantity_required(self):
        """测试对称网格必须设置数量"""
        with pytest.raises(ValidationError) as exc_info:
            GridStrategyConfig(
                strategy_name="测试",
                symbol="BNB/USDT",
                base_currency="BNB",
                quote_currency="USDT",
                grid_symmetric=True,
                # 缺少 order_quantity
            )

        assert "order_quantity" in str(exc_info.value)

    def test_floor_price_required(self):
        """测试启用保底价时必须设置价格"""
        with pytest.raises(ValidationError) as exc_info:
            GridStrategyConfig(
                strategy_name="测试",
                symbol="BNB/USDT",
                base_currency="BNB",
                quote_currency="USDT",
                enable_floor_price=True,
                # 缺少 floor_price
            )

        assert "floor_price" in str(exc_info.value)

    def test_trading_hours_validation(self):
        """测试交易时段验证"""
        # 正常情况
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            enable_monitor_period=True,
            trading_hours=[(9, 17), (20, 23)]
        )
        assert len(config.trading_hours) == 2

        # 异常：时段超出范围
        with pytest.raises(ValidationError):
            GridStrategyConfig(
                strategy_name="测试",
                symbol="BNB/USDT",
                base_currency="BNB",
                quote_currency="USDT",
                trading_hours=[(9, 25)]  # 25 超出范围
            )

        # 异常：开始时间 >= 结束时间
        with pytest.raises(ValidationError):
            GridStrategyConfig(
                strategy_name="测试",
                symbol="BNB/USDT",
                base_currency="BNB",
                quote_currency="USDT",
                trading_hours=[(17, 9)]  # 开始 > 结束
            )

    def test_trading_days_validation(self):
        """测试交易日期验证"""
        # 正常情况：工作日
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            trading_days=[1, 2, 3, 4, 5]
        )
        assert config.trading_days == [1, 2, 3, 4, 5]

        # 异常：日期超出范围
        with pytest.raises(ValidationError):
            GridStrategyConfig(
                strategy_name="测试",
                symbol="BNB/USDT",
                base_currency="BNB",
                quote_currency="USDT",
                trading_days=[1, 2, 8]  # 8 超出范围 (1-7)
            )


class TestGridStrategyConfigHelpers:
    """辅助方法测试"""

    def test_is_expired_not_set(self):
        """测试永久有效策略"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            expiry_days=-1  # 永久
        )

        assert config.is_expired() is False

    def test_is_expired_not_yet(self):
        """测试未过期策略"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            expiry_days=30
        )
        config.created_at = datetime.now()

        assert config.is_expired() is False

    def test_is_expired_yes(self):
        """测试已过期策略"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            expiry_days=30
        )
        config.created_at = datetime.now() - timedelta(days=31)

        assert config.is_expired() is True

    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        original = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            grid_type='percent',
            rise_sell_percent=1.5
        )

        # 转为字典
        data = original.to_dict()
        assert isinstance(data, dict)
        assert data['strategy_name'] == "测试"

        # 从字典恢复
        restored = GridStrategyConfig.from_dict(data)
        assert restored.strategy_name == original.strategy_name
        assert restored.symbol == original.symbol
        assert restored.grid_type == original.grid_type


class TestStrategyTemplates:
    """策略模板测试"""

    def test_conservative_grid_template(self):
        """测试保守型模板"""
        config = StrategyTemplates.conservative_grid("BNB/USDT")

        assert config.strategy_name == "BNB保守型网格"
        assert config.symbol == "BNB/USDT"
        assert config.grid_type == 'percent'
        assert config.grid_symmetric is True
        assert config.order_quantity == 10.0
        assert config.enable_volatility_adjustment is True

    def test_aggressive_grid_template(self):
        """测试激进型模板"""
        config = StrategyTemplates.aggressive_grid("ETH/USDT")

        assert config.strategy_name == "ETH激进型不对称网格"
        assert config.symbol == "ETH/USDT"
        assert config.grid_type == 'price'
        assert config.grid_symmetric is False
        assert config.buy_quantity == 100.0
        assert config.sell_quantity == 150.0
        assert config.enable_pullback_sell is True


class TestGridTypeCalculations:
    """网格类型计算测试"""

    def test_percent_mode(self):
        """测试百分比模式"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            grid_type='percent',
            trigger_base_price_type='manual',
            trigger_base_price=600.0,
            rise_sell_percent=1.0,
            fall_buy_percent=1.0
        )

        # 预期：
        # 卖出触发价 = 600 * (1 + 1/100) = 606
        # 买入触发价 = 600 * (1 - 1/100) = 594

        assert config.grid_type == 'percent'
        assert config.trigger_base_price == 600.0
        assert config.rise_sell_percent == 1.0
        assert config.fall_buy_percent == 1.0

    def test_price_mode(self):
        """测试价差模式"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            grid_type='price',
            trigger_base_price_type='manual',
            trigger_base_price=600.0,
            rise_sell_percent=10.0,  # 价差 10 USDT
            fall_buy_percent=10.0
        )

        # 预期：
        # 卖出触发价 = 600 + 10 = 610
        # 买入触发价 = 600 - 10 = 590

        assert config.grid_type == 'price'
        assert config.rise_sell_percent == 10.0
        assert config.fall_buy_percent == 10.0


class TestAmountModeCalculations:
    """金额模式计算测试"""

    def test_symmetric_percent_mode(self):
        """测试对称网格+百分比模式"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            amount_mode='percent',
            grid_symmetric=True,
            order_quantity=10.0  # 10%
        )

        assert config.amount_mode == 'percent'
        assert config.grid_symmetric is True
        assert config.order_quantity == 10.0

    def test_symmetric_amount_mode(self):
        """测试对称网格+固定金额模式"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            amount_mode='amount',
            grid_symmetric=True,
            order_quantity=100.0  # 100 USDT
        )

        assert config.amount_mode == 'amount'
        assert config.order_quantity == 100.0

    def test_asymmetric_quantities(self):
        """测试不对称网格数量"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            grid_symmetric=False,
            buy_quantity=100.0,
            sell_quantity=150.0
        )

        assert config.grid_symmetric is False
        assert config.buy_quantity == 100.0
        assert config.sell_quantity == 150.0


class TestOrderPriceMode:
    """订单价格模式测试"""

    def test_orderbook_price_modes(self):
        """测试盘口价格模式"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            order_type='limit',
            buy_price_mode='bid1',
            sell_price_mode='ask1'
        )

        assert config.buy_price_mode == 'bid1'
        assert config.sell_price_mode == 'ask1'

    def test_price_offset(self):
        """测试价格偏移"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            buy_price_mode='bid1',
            sell_price_mode='ask1',
            buy_price_offset=-0.01,  # 向下偏移
            sell_price_offset=0.01   # 向上偏移
        )

        assert config.buy_price_offset == -0.01
        assert config.sell_price_offset == 0.01

    def test_market_order_type(self):
        """测试市价单"""
        config = GridStrategyConfig(
            strategy_name="测试",
            symbol="BNB/USDT",
            base_currency="BNB",
            quote_currency="USDT",
            order_type='market'
        )

        assert config.order_type == 'market'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
