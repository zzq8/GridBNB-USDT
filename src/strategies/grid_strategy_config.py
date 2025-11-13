"""
网格策略完整配置模型

本模块定义了网格策略的完整配置数据模型，支持前端39个配置字段的所有功能。

配置分类：
1. 基础信息：交易对、策略名称等
2. 触发条件：grid_type、基准价、涨跌幅等
3. 订单设置：订单类型、价格模式、偏移量
4. 数量设置：金额模式、对称/不对称网格
5. 仓位控制：最大/最小仓位比例
6. 波动率自适应：动态网格调整
7. 生命周期：策略有效期、交易时段
8. 高级功能：保底价、自动清仓、优化算法

创建日期: 2025-11-07
作者: AI Assistant
版本: v1.0.0
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, Dict, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GridStrategyConfig(BaseModel):
    """
    网格策略完整配置模型

    支持39个配置字段，涵盖从基础设置到高级优化的所有功能。
    配置存储方案：可存储为JSON格式，支持数据库或文件存储。
    """

    # ========================================
    # 📋 基础信息
    # ========================================
    strategy_id: Optional[int] = Field(None, description="策略ID（数据库主键）")
    strategy_name: str = Field(..., description="策略名称", min_length=1, max_length=255)
    symbol: str = Field(..., description="交易对，格式: BNB/USDT", pattern=r"^[A-Z]+/[A-Z]+$")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    # ========================================
    # 💰 交易对配置
    # ========================================
    base_currency: str = Field(..., description="基础货币（如BNB）", pattern=r"^[A-Z]+$")
    quote_currency: str = Field(..., description="计价货币（如USDT）", pattern=r"^[A-Z]+$")

    # ========================================
    # 📊 触发条件核心逻辑
    # ========================================

    # 网格类型
    grid_type: Literal['percent', 'price'] = Field(
        'percent',
        description="网格类型: percent=按百分比, price=按价差"
    )

    # 触发基准价设置
    trigger_base_price_type: Literal['current', 'cost', 'avg_24h', 'manual'] = Field(
        'current',
        description="触发基准价类型: current=当前价, cost=成本价, avg_24h=24h均价, manual=手动设置"
    )
    trigger_base_price: Optional[float] = Field(
        None,
        description="手动触发基准价（仅当trigger_base_price_type=manual时必填）",
        gt=0
    )

    # 价格区间限制
    price_min: Optional[float] = Field(None, description="最低价格限制", gt=0)
    price_max: Optional[float] = Field(None, description="最高价格限制", gt=0)

    # 基础触发条件
    rise_sell_percent: float = Field(
        1.0,
        description="上涨卖出百分比/价差（取决于grid_type）",
        gt=0
    )
    fall_buy_percent: float = Field(
        1.0,
        description="下跌买入百分比/价差（取决于grid_type）",
        gt=0
    )

    # 高级触发条件
    enable_pullback_sell: bool = Field(False, description="是否启用回落卖出")
    pullback_sell_percent: float = Field(
        0.5,
        description="回落卖出触发条件（从最高点回落的百分比）",
        ge=0,
        le=100
    )

    enable_rebound_buy: bool = Field(False, description="是否启用拐点买入")
    rebound_buy_percent: float = Field(
        0.5,
        description="拐点买入触发条件（从最低点反弹的百分比）",
        ge=0,
        le=100
    )

    # ========================================
    # 🎯 订单设置
    # ========================================

    # 订单类型
    order_type: Literal['limit', 'market'] = Field(
        'limit',
        description="订单类型: limit=限价单, market=市价单"
    )

    # 限价单价格设置（仅当order_type=limit时生效）
    buy_price_mode: str = Field(
        'bid1',
        description="买入参考价: bid1-5（买1-5价）, ask1-5（卖1-5价）, trigger（触发价）",
        pattern=r"^(bid[1-5]|ask[1-5]|trigger)$"
    )
    sell_price_mode: str = Field(
        'ask1',
        description="卖出参考价: bid1-5（买1-5价）, ask1-5（卖1-5价）, trigger（触发价）",
        pattern=r"^(bid[1-5]|ask[1-5]|trigger)$"
    )
    buy_price_offset: Optional[float] = Field(
        None,
        description="买入价格偏移量（正数向上偏移，负数向下偏移）"
    )
    sell_price_offset: Optional[float] = Field(
        None,
        description="卖出价格偏移量（正数向上偏移，负数向下偏移）"
    )

    # ========================================
    # 💵 数量/金额管理
    # ========================================

    # 金额模式
    amount_mode: Literal['percent', 'amount'] = Field(
        'percent',
        description="金额模式: percent=按总资产百分比, amount=按固定金额（USDT）"
    )

    # 对称/不对称网格
    grid_symmetric: bool = Field(
        True,
        description="是否为对称网格（买入和卖出使用相同数量）"
    )

    # 对称网格数量（grid_symmetric=True时使用）
    order_quantity: Optional[float] = Field(
        None,
        description="对称网格每笔委托数量（百分比或固定金额，取决于amount_mode）",
        gt=0
    )

    # 不对称网格数量（grid_symmetric=False时使用）
    buy_quantity: Optional[float] = Field(
        None,
        description="不对称网格买入数量（百分比或固定金额）",
        gt=0
    )
    sell_quantity: Optional[float] = Field(
        None,
        description="不对称网格卖出数量（百分比或固定金额）",
        gt=0
    )

    # ========================================
    # 📈 仓位控制
    # ========================================
    max_position: float = Field(
        100,
        description="最大仓位比例（百分比，0-100）",
        ge=0,
        le=100
    )
    min_position: Optional[float] = Field(
        None,
        description="最小仓位比例（百分比，0-100）",
        ge=0,
        le=100
    )

    # ========================================
    # 📉 波动率自适应
    # ========================================
    enable_volatility_adjustment: bool = Field(
        False,
        description="是否启用波动率自适应网格调整"
    )
    base_grid: float = Field(
        2.5,
        description="基础网格大小（百分比）",
        gt=0
    )
    center_volatility: float = Field(
        0.25,
        description="波动率中心点",
        gt=0
    )
    sensitivity_k: float = Field(
        10.0,
        description="敏感度系数",
        gt=0
    )

    enable_dynamic_interval: bool = Field(
        False,
        description="是否启用动态交易间隔"
    )
    default_interval_hours: float = Field(
        1.0,
        description="默认交易间隔（小时）",
        gt=0
    )

    enable_volume_weighting: bool = Field(
        True,
        description="是否启用成交量加权"
    )

    # ========================================
    # ⏰ 生命周期管理
    # ========================================
    expiry_days: int = Field(
        -1,
        description="策略有效期（天数），-1表示永久有效"
    )

    # ========================================
    # 🕒 交易时段控制
    # ========================================
    enable_monitor_period: bool = Field(
        False,
        description="是否启用监控时段限制"
    )
    trading_hours: Optional[List[Tuple[int, int]]] = Field(
        None,
        description="交易时段列表，如：[(9, 17), (20, 23)] 表示 9:00-17:00 和 20:00-23:00"
    )
    trading_days: Optional[List[int]] = Field(
        None,
        description="交易日期列表（星期），1-7代表周一到周日，如：[1,2,3,4,5]表示工作日"
    )
    timezone: str = Field(
        'Asia/Shanghai',
        description="时区设置"
    )

    # ========================================
    # 🔧 高级功能
    # ========================================

    # 保底价
    enable_floor_price: bool = Field(
        False,
        description="是否启用保底价触发"
    )
    floor_price: Optional[float] = Field(
        None,
        description="保底价（触及时停止交易或发出警告）",
        gt=0
    )
    floor_price_action: Literal['stop', 'alert'] = Field(
        'alert',
        description="保底价触发动作: stop=停止交易, alert=仅发出警告"
    )

    # 自动清仓
    enable_auto_close: bool = Field(
        False,
        description="是否启用自动清仓"
    )
    auto_close_conditions: Optional[Dict] = Field(
        None,
        description="自动清仓条件配置（JSON格式）"
    )

    # 高级优化算法
    enable_deviation_control: bool = Field(
        False,
        description="是否启用偏差控制"
    )
    enable_price_optimization: bool = Field(
        False,
        description="是否启用报价优化"
    )
    enable_delay_confirm: bool = Field(
        False,
        description="是否启用延迟确认"
    )

    # ========================================
    # ✅ 验证器
    # ========================================

    @field_validator('trigger_base_price')
    @classmethod
    def validate_trigger_price(cls, v, info):
        """验证手动触发基准价"""
        # 该校验对字段间依赖在部分情况下可能不生效，
        # 在 model_validator 中也会进行兜底校验。
        if info.data.get('trigger_base_price_type') == 'manual' and v is None:
            raise ValueError("当 trigger_base_price_type='manual' 时，必须设置 trigger_base_price")
        return v

    @field_validator('buy_quantity', 'sell_quantity')
    @classmethod
    def validate_asymmetric_quantities(cls, v, info):
        """验证不对称网格数量"""
        # 该校验在字段顺序或默认值影响下可能不触发，
        # 在 model_validator 中也会进行兜底校验。
        if not info.data.get('grid_symmetric') and v is None:
            raise ValueError("当 grid_symmetric=False 时，必须设置 buy_quantity 和 sell_quantity")
        return v

    @field_validator('price_max')
    @classmethod
    def validate_price_range(cls, v, info):
        """验证价格区间"""
        price_min = info.data.get('price_min')
        if price_min and v and v <= price_min:
            raise ValueError(f"price_max ({v}) 必须大于 price_min ({price_min})")
        return v

    @field_validator('min_position')
    @classmethod
    def validate_position_limits(cls, v, info):
        """验证仓位限制"""
        max_position = info.data.get('max_position')
        if v is not None and max_position is not None and v >= max_position:
            raise ValueError(f"min_position ({v}) 必须小于 max_position ({max_position})")
        return v

    @field_validator('base_currency', 'quote_currency')
    @classmethod
    def validate_currencies_from_symbol(cls, v, info):
        """自动从symbol解析货币对（如果未提供）"""
        if info.field_name == 'base_currency' and not v:
            symbol = info.data.get('symbol')
            if symbol and '/' in symbol:
                return symbol.split('/')[0]
        elif info.field_name == 'quote_currency' and not v:
            symbol = info.data.get('symbol')
            if symbol and '/' in symbol:
                return symbol.split('/')[1]
        return v

    @field_validator('order_quantity')
    @classmethod
    def validate_symmetric_quantity(cls, v, info):
        """验证对称网格数量"""
        # 该校验在字段顺序或默认值影响下可能不触发，
        # 在 model_validator 中也会进行兜底校验。
        if info.data.get('grid_symmetric') and v is None:
            raise ValueError("当 grid_symmetric=True 时，必须设置 order_quantity")
        return v

    @field_validator('floor_price')
    @classmethod
    def validate_floor_price(cls, v, info):
        """验证保底价"""
        # 该校验在字段顺序或默认值影响下可能不触发，
        # 在 model_validator 中也会进行兜底校验。
        if info.data.get('enable_floor_price') and v is None:
            raise ValueError("当 enable_floor_price=True 时，必须设置 floor_price")
        return v

    # 统一的模型级校验，确保跨字段依赖在所有场景下都能正确校验
    from pydantic import model_validator

    @model_validator(mode='after')
    def _cross_field_validation(self):
        # 1) 手动基准价必须提供值
        if self.trigger_base_price_type == 'manual' and self.trigger_base_price is None:
            raise ValueError("当 trigger_base_price_type='manual' 时，必须设置 trigger_base_price")

        # 2) 对称/不对称数量要求
        # 仅当显式传入 grid_symmetric 时才强制对应数量校验，
        # 以避免默认值导致的反序列化失败。
        provided_fields = getattr(self, 'model_fields_set', set())
        if 'grid_symmetric' in provided_fields:
            if self.grid_symmetric:
                if self.order_quantity is None:
                    raise ValueError("当 grid_symmetric=True 时，必须设置 order_quantity")
            else:
                if self.buy_quantity is None or self.sell_quantity is None:
                    raise ValueError("当 grid_symmetric=False 时，必须设置 buy_quantity 和 sell_quantity")

        # 3) 保底价启用时必须设置价格
        if getattr(self, 'enable_floor_price', False) and self.floor_price is None:
            raise ValueError("当 enable_floor_price=True 时，必须设置 floor_price")

        # 4) 价格区间与仓位范围的兜底检查
        if self.price_min is not None and self.price_max is not None:
            if self.price_max <= self.price_min:
                raise ValueError(f"price_max ({self.price_max}) 必须大于 price_min ({self.price_min})")

        if self.min_position is not None and self.max_position is not None:
            if self.min_position >= self.max_position:
                raise ValueError(f"min_position ({self.min_position}) 必须小于 max_position ({self.max_position})")

        return self

    @field_validator('trading_hours')
    @classmethod
    def validate_trading_hours(cls, v):
        """验证交易时段格式"""
        if v is not None:
            for start, end in v:
                if not (0 <= start <= 23 and 0 <= end <= 23):
                    raise ValueError(f"交易时段必须在 0-23 之间，收到: ({start}, {end})")
                if start >= end:
                    raise ValueError(f"交易时段开始时间 ({start}) 必须小于结束时间 ({end})")
        return v

    @field_validator('trading_days')
    @classmethod
    def validate_trading_days(cls, v):
        """验证交易日期格式"""
        if v is not None:
            for day in v:
                if not (1 <= day <= 7):
                    raise ValueError(f"交易日期必须在 1-7 之间（周一到周日），收到: {day}")
        return v

    # ========================================
    # 🛠️ 辅助方法
    # ========================================

    def is_expired(self) -> bool:
        """检查策略是否已过期"""
        if self.expiry_days < 0:
            return False
        elapsed = (datetime.now() - self.created_at).days
        return elapsed >= self.expiry_days

    def is_in_trading_period(self) -> bool:
        """检查当前是否在交易时段内"""
        if not self.enable_monitor_period:
            return True

        from datetime import datetime
        import pytz

        now = datetime.now(pytz.timezone(self.timezone))
        current_hour = now.hour
        current_weekday = now.isoweekday()  # 1=Monday, 7=Sunday

        # 检查交易日期
        if self.trading_days and current_weekday not in self.trading_days:
            return False

        # 检查交易时段
        if self.trading_hours:
            for start, end in self.trading_hours:
                if start <= current_hour < end:
                    return True
            return False

        return True

    def to_dict(self) -> dict:
        """转换为字典（用于JSON序列化）
        默认排除未显式设置的字段，避免下次反序列化时触发无关校验。
        """
        return self.model_dump(mode='json', exclude_unset=True)

    @classmethod
    def from_dict(cls, data: dict) -> 'GridStrategyConfig':
        """从字典创建实例"""
        return cls(**data)

    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "strategy_name": "BNB保守型网格",
                "symbol": "BNB/USDT",
                "base_currency": "BNB",
                "quote_currency": "USDT",
                "grid_type": "percent",
                "trigger_base_price_type": "current",
                "rise_sell_percent": 1.5,
                "fall_buy_percent": 1.5,
                "order_type": "limit",
                "buy_price_mode": "bid1",
                "sell_price_mode": "ask1",
                "amount_mode": "percent",
                "grid_symmetric": True,
                "order_quantity": 10.0,
                "max_position": 80,
                "min_position": 20,
                "enable_volatility_adjustment": True,
                "base_grid": 2.5,
                "center_volatility": 0.25,
                "sensitivity_k": 10.0,
                "expiry_days": -1
            }
        }


# ========================================
# 📦 预设策略模板
# ========================================

class StrategyTemplates:
    """策略模板集合"""

    @staticmethod
    def conservative_grid(symbol: str = "BNB/USDT") -> GridStrategyConfig:
        """保守型网格策略"""
        base, quote = symbol.split('/')
        return GridStrategyConfig(
            strategy_name=f"{base}保守型网格",
            symbol=symbol,
            base_currency=base,
            quote_currency=quote,
            grid_type='percent',
            trigger_base_price_type='current',
            rise_sell_percent=1.5,
            fall_buy_percent=1.5,
            order_type='limit',
            buy_price_mode='bid1',
            sell_price_mode='ask1',
            amount_mode='percent',
            grid_symmetric=True,
            order_quantity=10.0,
            max_position=80,
            min_position=20,
            enable_volatility_adjustment=True,
            base_grid=2.5,
            expiry_days=-1
        )

    @staticmethod
    def aggressive_grid(symbol: str = "ETH/USDT") -> GridStrategyConfig:
        """激进型网格策略（不对称）"""
        base, quote = symbol.split('/')
        return GridStrategyConfig(
            strategy_name=f"{base}激进型不对称网格",
            symbol=symbol,
            base_currency=base,
            quote_currency=quote,
            grid_type='price',
            trigger_base_price_type='manual',
            trigger_base_price=3000.0,
            price_min=2800.0,
            price_max=3200.0,
            rise_sell_percent=50.0,
            fall_buy_percent=50.0,
            enable_pullback_sell=True,
            pullback_sell_percent=20.0,
            order_type='limit',
            buy_price_mode='ask1',
            sell_price_mode='bid1',
            amount_mode='amount',
            grid_symmetric=False,
            buy_quantity=100.0,
            sell_quantity=150.0,
            max_position=95,
            min_position=5,
            expiry_days=30
        )
