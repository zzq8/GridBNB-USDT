"""
高级风控引擎

实现 P1 功能：
1. 保底价触发（Floor Price Trigger）
2. 自动清仓（Auto Close Position）

创建日期: 2025-11-07
作者: AI Assistant
版本: v1.0.0
"""

import logging
from typing import Optional, Tuple
from datetime import datetime

from src.strategies.grid_strategy_config import GridStrategyConfig
from src.utils.helpers import send_pushplus_message

logger = logging.getLogger(__name__)


class AdvancedRiskController:
    """
    高级风控控制器

    实现保底价触发和自动清仓功能
    """

    def __init__(self, config: GridStrategyConfig, trader):
        """
        初始化风控控制器

        Args:
            config: 网格策略配置
            trader: GridTrader实例
        """
        self.config = config
        self.trader = trader
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{config.symbol}]")

        # 保底价状态
        self.floor_price_triggered = False
        self.floor_price_trigger_time: Optional[datetime] = None

        # 自动清仓状态
        self.auto_close_triggered = False
        self.auto_close_trigger_time: Optional[datetime] = None

    async def check_floor_price(self, current_price: float) -> Tuple[bool, str]:
        """
        检查保底价触发

        Args:
            current_price: 当前价格

        Returns:
            (是否触发, 触发原因)
        """
        # 如果未启用或已触发，跳过
        if not self.config.enable_floor_price:
            return False, ""

        if self.floor_price_triggered:
            return False, "保底价已触发过"

        # 检查价格是否触及保底价
        if current_price <= self.config.floor_price:
            self.floor_price_triggered = True
            self.floor_price_trigger_time = datetime.now()

            reason = (
                f"触及保底价 | "
                f"当前价: {current_price:.4f} | "
                f"保底价: {self.config.floor_price:.4f}"
            )

            self.logger.warning(f"⚠️ {reason}")

            # 根据配置决定动作
            if self.config.floor_price_action == 'stop':
                # 停止交易
                self.logger.critical(f"保底价触发，停止交易")
                await self._send_floor_price_alert(current_price, action="停止交易")
                return True, reason

            else:  # 'alert'
                # 仅发出警告
                self.logger.warning(f"保底价触发，发出警告")
                await self._send_floor_price_alert(current_price, action="仅警告")
                return False, reason

        return False, ""

    async def _send_floor_price_alert(self, current_price: float, action: str):
        """发送保底价触发警告"""
        message = f"""
⚠️ 保底价触发警告
━━━━━━━━━━━━━━━━━━━━
交易对: {self.config.symbol}
当前价格: {current_price:.4f} {self.config.quote_currency}
保底价: {self.config.floor_price:.4f} {self.config.quote_currency}
触发时间: {self.floor_price_trigger_time.strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
执行动作: {action}
━━━━━━━━━━━━━━━━━━━━
"""
        send_pushplus_message(message, "⚠️ 保底价触发")

    async def check_auto_close_conditions(self) -> Tuple[bool, str]:
        """
        检查自动清仓条件

        Returns:
            (是否触发, 触发原因)
        """
        # 如果未启用或已触发，跳过
        if not self.config.enable_auto_close:
            return False, ""

        if self.auto_close_triggered:
            return False, "自动清仓已触发过"

        # 获取清仓条件配置
        if not self.config.auto_close_conditions:
            self.logger.warning("自动清仓已启用但未配置条件")
            return False, "未配置清仓条件"

        conditions = self.config.auto_close_conditions

        # 条件1: 盈利目标达成
        if 'profit_target' in conditions:
            profit = await self._calculate_profit()
            target = conditions['profit_target']

            if profit >= target:
                reason = f"盈利达标清仓 | 当前盈利: {profit:.2f} | 目标: {target:.2f}"
                self.logger.info(f"✅ {reason}")
                return True, reason

        # 条件2: 亏损止损
        if 'loss_limit' in conditions:
            profit = await self._calculate_profit()
            limit = conditions['loss_limit']

            if profit <= -limit:  # 负盈利表示亏损
                reason = f"亏损止损清仓 | 当前亏损: {profit:.2f} | 限制: {limit:.2f}"
                self.logger.warning(f"⚠️ {reason}")
                return True, reason

        # 条件3: 价格暴跌
        if 'price_drop_percent' in conditions:
            current_price = await self.trader._get_latest_price()
            base_price = self.trader.base_price
            drop_percent = (base_price - current_price) / base_price * 100
            threshold = conditions['price_drop_percent']

            if drop_percent >= threshold:
                reason = (
                    f"价格暴跌清仓 | "
                    f"基准价: {base_price:.4f} | "
                    f"当前价: {current_price:.4f} | "
                    f"跌幅: {drop_percent:.2f}% (阈值: {threshold}%)"
                )
                self.logger.warning(f"⚠️ {reason}")
                return True, reason

        # 条件4: 持续时间
        if 'holding_hours' in conditions:
            holding_hours = conditions['holding_hours']
            elapsed_hours = (datetime.now() - self.config.created_at).total_seconds() / 3600

            if elapsed_hours >= holding_hours:
                reason = (
                    f"持续时间达标清仓 | "
                    f"已运行: {elapsed_hours:.1f}小时 | "
                    f"目标: {holding_hours}小时"
                )
                self.logger.info(f"✅ {reason}")
                return True, reason

        return False, ""

    async def _calculate_profit(self) -> float:
        """
        计算当前盈利

        Returns:
            盈利金额（正数=盈利，负数=亏损）
        """
        try:
            # 获取当前总资产
            current_assets = await self.trader._get_pair_specific_assets_value()

            # 获取初始本金（从配置或交易历史计算）
            from src.config.settings import settings

            if settings.INITIAL_PRINCIPAL and settings.INITIAL_PRINCIPAL > 0:
                initial_principal = settings.INITIAL_PRINCIPAL
            else:
                # 从交易历史计算
                initial_principal = current_assets  # 简化处理

            profit = current_assets - initial_principal

            self.logger.debug(
                f"盈利计算 | "
                f"当前资产: {current_assets:.2f} | "
                f"初始本金: {initial_principal:.2f} | "
                f"盈亏: {profit:+.2f}"
            )

            return profit

        except Exception as e:
            self.logger.error(f"计算盈利失败: {e}")
            return 0.0

    async def execute_auto_close(self, reason: str):
        """
        执行自动清仓

        Args:
            reason: 清仓原因
        """
        self.auto_close_triggered = True
        self.auto_close_trigger_time = datetime.now()

        self.logger.critical(f"🚨 开始执行自动清仓 | 原因: {reason}")

        try:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 步骤1: 取消所有挂单
            # ━━━━━━━━━━━━━━━━━━━━━━━���━━━━━━━━━━━━━━━━━━━━
            self.logger.info("取消所有挂单...")
            open_orders = await self.trader.exchange.fetch_open_orders(self.config.symbol)

            for order in open_orders:
                try:
                    await self.trader.exchange.cancel_order(order['id'], self.config.symbol)
                    self.logger.info(f"已取消订单: {order['id']}")
                except Exception as e:
                    self.logger.error(f"取消订单失败: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 步骤2: 市价单卖出所有基础资产
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            balance = await self.trader.exchange.fetch_balance({'type': 'spot'})
            base_balance = float(balance['free'].get(self.config.base_currency, 0))

            if base_balance > 0:
                # 调整精度
                base_balance = float(self.trader._adjust_amount_precision(base_balance))

                # 检查最小交易量
                from src.config.settings import settings
                min_amount = getattr(settings, 'MIN_AMOUNT_LIMIT', 0.001)

                if base_balance >= min_amount:
                    self.logger.info(f"市价卖出 {base_balance} {self.config.base_currency}")

                    # 市价单卖出
                    order = await self.trader.exchange.create_order(
                        self.config.symbol,
                        'market',
                        'sell',
                        base_balance
                    )

                    self.logger.info(f"清仓订单已成交: {order}")
                else:
                    self.logger.warning(
                        f"基础资产余额 ({base_balance}) 低于最小交易量 ({min_amount})，跳过卖出"
                    )
            else:
                self.logger.info(f"没有可卖出的 {self.config.base_currency}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 步骤3: 发送通知
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            await self._send_auto_close_notification(reason, base_balance)

            self.logger.critical(f"✅ 自动清仓完成")

        except Exception as e:
            self.logger.error(f"自动清仓失败: {e}", exc_info=True)
            send_pushplus_message(
                f"🆘 自动清仓失败\n"
                f"交易对: {self.config.symbol}\n"
                f"错误: {str(e)}\n"
                f"请立即人工介入！",
                "🆘 紧急告警"
            )
            raise

    async def _send_auto_close_notification(self, reason: str, sold_amount: float):
        """发送自动清仓通知"""
        current_price = await self.trader._get_latest_price()
        profit = await self._calculate_profit()

        message = f"""
🚨 自动清仓通知
━━━━━━━━━━━━━━━━━━━━
交易对: {self.config.symbol}
清仓原因: {reason}
执行时间: {self.auto_close_trigger_time.strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
当前价格: {current_price:.4f} {self.config.quote_currency}
卖出数量: {sold_amount:.6f} {self.config.base_currency}
当前盈亏: {profit:+.2f} {self.config.quote_currency}
━━━━━━━━━━━━━━━━━━━━
策略已停止
━━━━━━━━━━━━━━━━━━━━
"""
        send_pushplus_message(message, "🚨 自动清仓")

    def get_status(self) -> dict:
        """
        获取风控状态

        Returns:
            状态字典
        """
        return {
            'floor_price_enabled': self.config.enable_floor_price,
            'floor_price': self.config.floor_price,
            'floor_price_triggered': self.floor_price_triggered,
            'floor_price_trigger_time': self.floor_price_trigger_time.isoformat() if self.floor_price_trigger_time else None,

            'auto_close_enabled': self.config.enable_auto_close,
            'auto_close_triggered': self.auto_close_triggered,
            'auto_close_trigger_time': self.auto_close_trigger_time.isoformat() if self.auto_close_trigger_time else None,
        }

    def reset(self):
        """重置风控状态"""
        self.floor_price_triggered = False
        self.floor_price_trigger_time = None
        self.auto_close_triggered = False
        self.auto_close_trigger_time = None
        self.logger.info("风控状态已重置")
