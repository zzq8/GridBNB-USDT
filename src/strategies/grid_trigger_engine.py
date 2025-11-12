"""
网格触发条件引擎

本模块实现了网格策略的完整触发逻辑，包括：
1. 基准价计算（当前价/成本价/均价/手动）
2. 触发价位计算（百分比模式/价差模式）
3. 基础触发检测（上涨卖出/下跌买入）
4. 高级触发检测（回落卖出/拐点买入）

创建日期: 2025-11-07
作者: AI Assistant
版本: v1.0.0
"""

import logging
from typing import Optional, Tuple
from src.strategies.grid_strategy_config import GridStrategyConfig

logger = logging.getLogger(__name__)


class GridTriggerEngine:
    """
    网格触发引擎

    负责根据配置计算触发价位并检测交易信号
    """

    def __init__(self, config: GridStrategyConfig, trader):
        """
        初始化触发引擎

        Args:
            config: 网格策略配置
            trader: GridTrader实例（用于获取市场数据）
        """
        self.config = config
        self.trader = trader
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{config.symbol}]")

        # 状态变量
        self.base_price: Optional[float] = None  # 当前基准价
        self.sell_trigger_price: Optional[float] = None  # 卖出触发价
        self.buy_trigger_price: Optional[float] = None  # 买入触发价

        # 高级触发状态
        self.highest_price: Optional[float] = None  # 监测到的最高价
        self.lowest_price: Optional[float] = None  # 监测到的最低价
        self.is_monitoring_sell: bool = False  # 是否在监测卖出回落
        self.is_monitoring_buy: bool = False  # 是否在监测买入反弹

    async def get_base_price(self) -> float:
        """
        获取触发基准价

        Returns:
            基准价格
        """
        if self.config.trigger_base_price_type == 'manual':
            # 手动设置的基准价
            return self.config.trigger_base_price

        elif self.config.trigger_base_price_type == 'current':
            # 当前市场价
            return await self.trader._get_latest_price()

        elif self.config.trigger_base_price_type == 'cost':
            # 成本价（使用trader的base_price）
            return self.trader.base_price

        elif self.config.trigger_base_price_type == 'avg_24h':
            # 24小时均价
            return await self._calculate_24h_avg_price()

        else:
            self.logger.warning(f"未知的基准价类型: {self.config.trigger_base_price_type}，使用当前价")
            return await self.trader._get_latest_price()

    async def _calculate_24h_avg_price(self) -> float:
        """
        计算24小时均价

        Returns:
            24小时均价
        """
        try:
            # 获取24小时K线数据
            klines = await self.trader.exchange.fetch_ohlcv(
                self.config.symbol,
                timeframe='1h',
                limit=24
            )

            if not klines or len(klines) == 0:
                self.logger.warning("无法获取24h K线数据，使用当前价")
                return await self.trader._get_latest_price()

            # 计算平均收盘价
            closes = [float(k[4]) for k in klines]
            avg_price = sum(closes) / len(closes)

            self.logger.debug(f"24h均价: {avg_price:.4f}")
            return avg_price

        except Exception as e:
            self.logger.error(f"计算24h均价失败: {e}")
            return await self.trader._get_latest_price()

    async def calculate_trigger_levels(self) -> Tuple[float, float]:
        """
        计算买卖触发价位

        Returns:
            (sell_trigger, buy_trigger) 卖出触发价和买入触发价
        """
        # 获取基准价
        self.base_price = await self.get_base_price()

        if self.config.grid_type == 'percent':
            # 百分比模式
            sell_trigger = self.base_price * (1 + self.config.rise_sell_percent / 100)
            buy_trigger = self.base_price * (1 - self.config.fall_buy_percent / 100)

            self.logger.debug(
                f"百分比模式触发价 | "
                f"基准价: {self.base_price:.4f} | "
                f"卖出触发: {sell_trigger:.4f} (+{self.config.rise_sell_percent}%) | "
                f"买入触发: {buy_trigger:.4f} (-{self.config.fall_buy_percent}%)"
            )

        else:  # 'price' 价差模式
            sell_trigger = self.base_price + self.config.rise_sell_percent
            buy_trigger = self.base_price - self.config.fall_buy_percent

            self.logger.debug(
                f"价差模式触发价 | "
                f"基准价: {self.base_price:.4f} | "
                f"卖出触发: {sell_trigger:.4f} (+{self.config.rise_sell_percent}) | "
                f"买入触发: {buy_trigger:.4f} (-{self.config.fall_buy_percent})"
            )

        # 缓存触发价
        self.sell_trigger_price = sell_trigger
        self.buy_trigger_price = buy_trigger

        return sell_trigger, buy_trigger

    async def check_sell_signal(self, current_price: float) -> bool:
        """
        检查卖出信号

        Args:
            current_price: 当前市场价格

        Returns:
            是否应该卖出
        """
        # 计算触发价位
        sell_trigger, _ = await self.calculate_trigger_levels()

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 场景1: 启用回落卖出 (高级触发)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if self.config.enable_pullback_sell:
            return await self._check_pullback_sell_signal(current_price, sell_trigger)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 场景2: 基础卖出触发（价格达到上轨）
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if current_price >= sell_trigger:
            self.logger.info(
                f"✅ 卖出信号触发 | "
                f"当前价: {current_price:.4f} | "
                f"触发价: {sell_trigger:.4f} | "
                f"超出: {(current_price - sell_trigger):.4f}"
            )
            return True

        return False

    async def _check_pullback_sell_signal(self, current_price: float, sell_trigger: float) -> bool:
        """
        检查回落卖出信号

        逻辑：
        1. 价格突破sell_trigger后，进入监测状态
        2. 记录最高价
        3. 当价格从最高价回落超过pullback_sell_percent时，触发卖出

        Args:
            current_price: 当前价格
            sell_trigger: 卖出触发价

        Returns:
            是否触发卖出
        """
        # 价格突破上轨，进入监测
        if current_price >= sell_trigger:
            self.is_monitoring_sell = True

            # 更新最高价
            if self.highest_price is None or current_price > self.highest_price:
                old_highest = self.highest_price or 0
                self.highest_price = current_price

                if old_highest > 0:
                    self.logger.info(
                        f"📈 更新最高价 | "
                        f"{old_highest:.4f} → {self.highest_price:.4f} | "
                        f"回落触发价: {self.highest_price * (1 - self.config.pullback_sell_percent / 100):.4f}"
                    )

            # 检查是否回落到触发点
            if self.highest_price:
                pullback_trigger = self.highest_price * (1 - self.config.pullback_sell_percent / 100)

                if current_price <= pullback_trigger:
                    pullback_amount = (self.highest_price - current_price) / self.highest_price * 100
                    self.logger.info(
                        f"✅ 回落卖出触发 | "
                        f"最高价: {self.highest_price:.4f} | "
                        f"当前价: {current_price:.4f} | "
                        f"回落: {pullback_amount:.2f}% (阈值: {self.config.pullback_sell_percent}%)"
                    )

                    # 重置状态
                    self.highest_price = None
                    self.is_monitoring_sell = False

                    return True

        # 价格回落到触发价以下，重置监测状态
        elif self.is_monitoring_sell and current_price < sell_trigger:
            self.logger.info(
                f"❌ 价格回落到触发价以下，重置卖出监测 | "
                f"当前价: {current_price:.4f} | "
                f"触发价: {sell_trigger:.4f}"
            )
            self.highest_price = None
            self.is_monitoring_sell = False

        return False

    async def check_buy_signal(self, current_price: float) -> bool:
        """
        检查买入信号

        Args:
            current_price: 当前市场价格

        Returns:
            是否应该买入
        """
        # 计算触发价位
        _, buy_trigger = await self.calculate_trigger_levels()

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 场景1: 启用拐点买入 (高级触发)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if self.config.enable_rebound_buy:
            return await self._check_rebound_buy_signal(current_price, buy_trigger)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 场景2: 基础买入触发（价格达到下轨）
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if current_price <= buy_trigger:
            self.logger.info(
                f"✅ 买入信号触发 | "
                f"当前价: {current_price:.4f} | "
                f"触发价: {buy_trigger:.4f} | "
                f"低于: {(buy_trigger - current_price):.4f}"
            )
            return True

        return False

    async def _check_rebound_buy_signal(self, current_price: float, buy_trigger: float) -> bool:
        """
        检查拐点买入信号

        逻辑：
        1. 价格跌破buy_trigger后，进入监测状态
        2. 记录最低价
        3. 当价格从最低价反弹超过rebound_buy_percent时，触发买入

        Args:
            current_price: 当前价格
            buy_trigger: 买入触发价

        Returns:
            是否触发买入
        """
        # 价格跌破下轨，进入监测
        if current_price <= buy_trigger:
            self.is_monitoring_buy = True

            # 更新最低价
            if self.lowest_price is None or current_price < self.lowest_price:
                old_lowest = self.lowest_price or float('inf')
                self.lowest_price = current_price

                if old_lowest < float('inf'):
                    self.logger.info(
                        f"📉 更新最低价 | "
                        f"{old_lowest:.4f} → {self.lowest_price:.4f} | "
                        f"反弹触发价: {self.lowest_price * (1 + self.config.rebound_buy_percent / 100):.4f}"
                    )

            # 检查是否反弹到触发点
            if self.lowest_price:
                rebound_trigger = self.lowest_price * (1 + self.config.rebound_buy_percent / 100)

                if current_price >= rebound_trigger:
                    rebound_amount = (current_price - self.lowest_price) / self.lowest_price * 100
                    self.logger.info(
                        f"✅ 拐点买入触发 | "
                        f"最低价: {self.lowest_price:.4f} | "
                        f"当前价: {current_price:.4f} | "
                        f"反弹: {rebound_amount:.2f}% (阈值: {self.config.rebound_buy_percent}%)"
                    )

                    # 重置状态
                    self.lowest_price = None
                    self.is_monitoring_buy = False

                    return True

        # 价格回升到触发价以上，重置监测状态
        elif self.is_monitoring_buy and current_price > buy_trigger:
            self.logger.info(
                f"❌ 价格回升到触发价以上，重置买入监测 | "
                f"当前价: {current_price:.4f} | "
                f"触发价: {buy_trigger:.4f}"
            )
            self.lowest_price = None
            self.is_monitoring_buy = False

        return False

    def check_price_range(self, current_price: float) -> bool:
        """
        检查价格是否在允许的区间内

        Args:
            current_price: 当前价格

        Returns:
            是否在区间内
        """
        if self.config.price_min and current_price < self.config.price_min:
            self.logger.warning(
                f"⚠️ 价格低于最低限制 | "
                f"当前价: {current_price:.4f} | "
                f"最低价: {self.config.price_min:.4f}"
            )
            return False

        if self.config.price_max and current_price > self.config.price_max:
            self.logger.warning(
                f"⚠️ 价格高于最高限制 | "
                f"当前价: {current_price:.4f} | "
                f"最高价: {self.config.price_max:.4f}"
            )
            return False

        return True

    def reset_monitoring_state(self):
        """重置监测状态"""
        self.highest_price = None
        self.lowest_price = None
        self.is_monitoring_sell = False
        self.is_monitoring_buy = False
        self.logger.debug("已重置监测状态")

    def get_status(self) -> dict:
        """
        获取引擎当前状态

        Returns:
            状态字典
        """
        return {
            'base_price': self.base_price,
            'sell_trigger': self.sell_trigger_price,
            'buy_trigger': self.buy_trigger_price,
            'highest_price': self.highest_price,
            'lowest_price': self.lowest_price,
            'is_monitoring_sell': self.is_monitoring_sell,
            'is_monitoring_buy': self.is_monitoring_buy
        }
