"""
网格订单管理引擎

本模块实现了订单数量计算和订单价格优化：
1. 数量管理：按百分比/按固定金额，对称/不对称网格
2. 价格优化：盘口价格档位选择、价格偏移

创建日期: 2025-11-07
作者: AI Assistant
版本: v1.0.0
"""

import logging
from typing import Tuple, Optional
from src.strategies.grid_strategy_config import GridStrategyConfig

logger = logging.getLogger(__name__)


class GridOrderEngine:
    """
    网格订单引擎

    负责计算订单数量和优化订单价格
    """

    def __init__(self, config: GridStrategyConfig, trader):
        """
        初始化订单引擎

        Args:
            config: 网格策略配置
            trader: GridTrader实例
        """
        self.config = config
        self.trader = trader
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{config.symbol}]")

    async def calculate_order_amount(self, side: str) -> float:
        """
        计算订单金额（USDT）

        Args:
            side: 'buy' 或 'sell'

        Returns:
            订单金额（USDT）
        """
        if self.config.amount_mode == 'percent':
            # 按百分比模式
            return await self._calculate_amount_by_percent(side)
        else:  # 'amount'
            # 按固定金额模式
            return await self._calculate_amount_by_fixed(side)

    async def _calculate_amount_by_percent(self, side: str) -> float:
        """
        按百分比计算订单金额

        Args:
            side: 'buy' 或 'sell'

        Returns:
            订单金额（USDT）
        """
        # 获取总资产价值
        total_value = await self.trader._get_pair_specific_assets_value()

        # 获取百分比
        if self.config.grid_symmetric:
            # 对称网格：使用统一比例
            percent = self.config.order_quantity / 100
        else:
            # 不对称网格：根据买卖方向使用不同比例
            if side == 'buy':
                percent = self.config.buy_quantity / 100
            else:  # sell
                percent = self.config.sell_quantity / 100

        # 计算金额
        amount = total_value * percent

        self.logger.debug(
            f"按百分比计算金额 | "
            f"总资产: {total_value:.2f} | "
            f"比例: {percent*100:.1f}% | "
            f"金额: {amount:.2f} USDT"
        )

        return amount

    async def _calculate_amount_by_fixed(self, side: str) -> float:
        """
        按固定金额计算订单金额

        Args:
            side: 'buy' 或 'sell'

        Returns:
            订单金额（USDT）
        """
        if self.config.grid_symmetric:
            # 对称网格：使用统一金额
            amount = self.config.order_quantity
        else:
            # 不对称网格：根据买卖方向使用不同金额
            if side == 'buy':
                amount = self.config.buy_quantity
            else:  # sell
                amount = self.config.sell_quantity

        self.logger.debug(
            f"按固定金额计算 | "
            f"方向: {side} | "
            f"金额: {amount:.2f} USDT"
        )

        return amount

    async def calculate_order_price(self, side: str, current_price: Optional[float] = None) -> float:
        """
        计算订单价格

        Args:
            side: 'buy' 或 'sell'
            current_price: 当前价格（可选，如果不提供则自动获取）

        Returns:
            订单价格
        """
        # 如果是市价单，直接返回当前价
        if self.config.order_type == 'market':
            if current_price is None:
                current_price = await self.trader._get_latest_price()
            return current_price

        # 限价单：根据配置计算价格
        if side == 'buy':
            price_mode = self.config.buy_price_mode
            price_offset = self.config.buy_price_offset or 0
        else:  # sell
            price_mode = self.config.sell_price_mode
            price_offset = self.config.sell_price_offset or 0

        # 获取基准价格
        if price_mode == 'trigger':
            # 使用触发价
            if current_price is None:
                current_price = await self.trader._get_latest_price()
            base_price = current_price
        else:
            # 使用盘口价格
            base_price = await self._get_orderbook_price(price_mode)

        # 应用价格偏移
        final_price = base_price + price_offset

        # 调整价格精度
        final_price = self.trader._adjust_price_precision(final_price)

        self.logger.debug(
            f"订单价格计算 | "
            f"方向: {side} | "
            f"模式: {price_mode} | "
            f"基准价: {base_price:.4f} | "
            f"偏移: {price_offset:+.4f} | "
            f"最终价: {final_price:.4f}"
        )

        return final_price

    async def _get_orderbook_price(self, mode: str) -> float:
        """
        从订单簿获取指定档位的价格

        Args:
            mode: 价格模式，如 'bid1', 'bid2', 'ask1', 'ask2' 等

        Returns:
            档位价格
        """
        try:
            # 获取订单簿数据
            orderbook = await self.trader.exchange.fetch_order_book(
                self.config.symbol,
                limit=5
            )

            if not orderbook or not orderbook.get('bids') or not orderbook.get('asks'):
                self.logger.error("订单簿数据无效，使用当前价")
                return await self.trader._get_latest_price()

            # 解析档位
            if mode.startswith('bid'):
                # 买价档位
                level = int(mode[3:])  # 'bid1' -> 1
                if level > len(orderbook['bids']):
                    self.logger.warning(f"买价档位{level}不存在，使用买1价")
                    level = 1
                return orderbook['bids'][level - 1][0]

            elif mode.startswith('ask'):
                # 卖价档位
                level = int(mode[3:])  # 'ask1' -> 1
                if level > len(orderbook['asks']):
                    self.logger.warning(f"卖价档位{level}不存在，使用卖1价")
                    level = 1
                return orderbook['asks'][level - 1][0]

            else:
                self.logger.error(f"未知的价格模式: {mode}，使用当前价")
                return await self.trader._get_latest_price()

        except Exception as e:
            self.logger.error(f"获取盘口价格失败: {e}，使用当前价")
            return await self.trader._get_latest_price()

    async def prepare_order(self, side: str) -> Tuple[float, float, float]:
        """
        准备订单：计算价格和数量

        Args:
            side: 'buy' 或 'sell'

        Returns:
            (price, amount_quote, amount_base) 订单价格、金额（USDT）、数量（BASE）
        """
        # 计算订单价格
        order_price = await self.calculate_order_price(side)

        # 计算订单金额（USDT）
        amount_quote = await self.calculate_order_amount(side)

        # 计算订单数量（BASE）
        amount_base = amount_quote / order_price

        # 调整数量精度
        amount_base = float(self.trader._adjust_amount_precision(amount_base))

        self.logger.info(
            f"订单准备完成 | "
            f"方向: {side.upper()} | "
            f"价格: {order_price:.4f} {self.config.quote_currency} | "
            f"金额: {amount_quote:.2f} {self.config.quote_currency} | "
            f"数量: {amount_base:.6f} {self.config.base_currency}"
        )

        return order_price, amount_quote, amount_base

    def get_summary(self) -> dict:
        """
        获取引擎配置摘要

        Returns:
            配置摘要字典
        """
        return {
            'amount_mode': self.config.amount_mode,
            'grid_symmetric': self.config.grid_symmetric,
            'order_quantity': self.config.order_quantity if self.config.grid_symmetric else None,
            'buy_quantity': self.config.buy_quantity if not self.config.grid_symmetric else None,
            'sell_quantity': self.config.sell_quantity if not self.config.grid_symmetric else None,
            'order_type': self.config.order_type,
            'buy_price_mode': self.config.buy_price_mode,
            'sell_price_mode': self.config.sell_price_mode,
            'buy_price_offset': self.config.buy_price_offset,
            'sell_price_offset': self.config.sell_price_offset
        }
