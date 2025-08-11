# position_controller_s1.py
import time
import asyncio
import logging
import math # 需要 math 来处理精度
from risk_manager import RiskState

class PositionControllerS1:
    """
    独立的仓位控制策略 (S1)。
    基于每日更新的52日高低点，高频检查仓位并执行调整。
    独立于主网格策略运行，不修改网格的 base_price。
    """
    def __init__(self, trader_instance):
        """
        初始化S1仓位控制器。

        Args:
            trader_instance: 主 GridTrader 类的实例，用于访问交易所客户端、
                             获取账户信息、执行订单和日志记录。
        """
        self.trader = trader_instance  # 保存对主 trader 实例的引用
        self.config = trader_instance.config # 访问配置
        self.logger = logging.getLogger(self.__class__.__name__) # 创建独立的 logger

        # S1 策略参数 (从配置或直接赋值)
        # 现在直接使用默认值，因为这些参数不在 settings 中定义
        self.s1_lookback = 52
        self.s1_sell_target_pct = 0.50
        self.s1_buy_target_pct = 0.70

        # S1 状态变量
        self.s1_daily_high = None
        self.s1_daily_low = None
        self.s1_last_data_update_ts = 0
        # 每日更新时间间隔（秒），略小于24小时确保不会错过
        self.daily_update_interval = 23.9 * 60 * 60 

        self.logger.info(f"S1 Position Controller initialized. Lookback={self.s1_lookback} days, Sell Target={self.s1_sell_target_pct*100}%, Buy Target={self.s1_buy_target_pct*100}%.")

    async def _fetch_and_calculate_s1_levels(self):
        """获取日线数据并计算52日高低点"""
        try:
            # 获取比回看期稍多的日线数据 (+2 buffer)
            limit = self.s1_lookback + 2
            klines = await self.trader.exchange.fetch_ohlcv(
                self.trader.symbol, 
                timeframe='1d', 
                limit=limit
            )

            if not klines or len(klines) < self.s1_lookback + 1:
                self.logger.warning(f"S1: Insufficient daily klines received ({len(klines)}), cannot update levels.")
                return False

            # 使用倒数第2根K线往前数 s1_lookback 根来计算 (排除最新未完成K线)
            # klines[-1] 是当前未完成日线，klines[-2] 是昨天收盘的日线
            relevant_klines = klines[-(self.s1_lookback + 1) : -1]

            if len(relevant_klines) < self.s1_lookback:
                 self.logger.warning(f"S1: Not enough relevant klines ({len(relevant_klines)}) for lookback {self.s1_lookback}.")
                 return False

            # 计算高低点 (索引 2 是 high, 3 是 low)
            self.s1_daily_high = max(float(k[2]) for k in relevant_klines)
            self.s1_daily_low = min(float(k[3]) for k in relevant_klines)
            self.s1_last_data_update_ts = time.time()
            self.logger.info(f"S1 Levels Updated: High={self.s1_daily_high:.4f}, Low={self.s1_daily_low:.4f}")
            return True

        except Exception as e:
            self.logger.error(f"S1: Failed to fetch or calculate daily levels: {e}", exc_info=False)
            return False

    async def update_daily_s1_levels(self):
        """每日检查并更新一次S1所需的52日高低价"""
        now = time.time()
        if now - self.s1_last_data_update_ts >= self.daily_update_interval:
            self.logger.info("S1: Time to update daily high/low levels...")
            await self._fetch_and_calculate_s1_levels()
        # else: 不需要更新

    async def _execute_s1_adjustment(self, side, amount_base_asset):
        """
        专门执行 S1 仓位调整的下单函数。
        使用 trader 实例的 exchange 客户端直接下单。
        不更新网格的 base_price。
        """
        try:
            # 1. 精度调整 (复用 trader 中的方法，如果存在且安全)
            # 假设 trader 中有 _adjust_amount_precision 方法
            if hasattr(self.trader, '_adjust_amount_precision') and callable(self.trader._adjust_amount_precision):
                adjusted_amount = self.trader._adjust_amount_precision(amount_base_asset)
            else:
                # 如果没有，提供一个基础实现 (根据需要调整精度)
                precision = 3 
                factor = 10 ** precision
                adjusted_amount = math.floor(amount_base_asset * factor) / factor
                self.logger.warning("S1: Using basic amount precision adjustment.")

            if adjusted_amount <= 0:
                self.logger.warning(f"S1: Adjusted amount is zero or negative ({adjusted_amount}), skipping order.")
                return False

            # 2. 获取当前价格（用于后续日志和最小名义价值判断）
            current_price = self.trader.current_price # 假设主循环已更新
            if not current_price or current_price <= 0:
                 self.logger.error("S1: Invalid current price, cannot execute adjustment.")
                 return False
                 
            # 3. 检查最小订单限制 (复用 trader 中的 symbol_info, 如果存在)
            min_notional = 10 # 默认最小名义价值 (quote currency)
            min_amount_limit = 0.0001 # 默认最小数量
            if hasattr(self.trader, 'symbol_info') and self.trader.symbol_info:
                 limits = self.trader.symbol_info.get('limits', {})
                 min_notional = limits.get('cost', {}).get('min', min_notional)
                 min_amount_limit = limits.get('amount', {}).get('min', min_amount_limit)
                 
            if adjusted_amount < min_amount_limit:
                self.logger.warning(f"S1: Adjusted amount {adjusted_amount:.8f} {self.trader.base_asset} is below minimum amount limit {min_amount_limit:.8f}.")
                return False
            if adjusted_amount * current_price < min_notional:
                 self.logger.warning(f"S1: Order value {adjusted_amount * current_price:.2f} {self.trader.quote_asset} is below minimum notional value {min_notional:.2f}.")
                 return False

            # 4. 检查余额，必要时从理财账户赎回资金
            if side == 'BUY':
                # 检查quote currency余额是否足够
                quote_needed = adjusted_amount * current_price
                quote_available = await self.trader.get_available_balance(self.trader.quote_asset)
                
                if quote_available < quote_needed:
                    self.logger.info(f"S1: {self.trader.quote_asset}余额不足，需要{quote_needed:.2f}，可用{quote_available:.2f}，尝试从理财赎回")
                    
                    # 使用网格策略的资金转移方法
                    if hasattr(self.trader, '_pre_transfer_funds'):
                        try:
                            await self.trader._pre_transfer_funds(current_price)
                            # 重新检查余额
                            quote_available = await self.trader.get_available_balance(self.trader.quote_asset)
                            if quote_available < quote_needed:
                                self.logger.warning(f"S1: 即使赎回后，{self.trader.quote_asset}余额仍不足，可用{quote_available:.2f}")
                                return False
                        except Exception as e:
                            self.logger.error(f"S1: 从理财赎回资金失败: {e}")
                            return False
                    else:
                        self.logger.warning("S1: 无法从理财赎回资金，trader没有_pre_transfer_funds方法")
                        return False
                    
            elif side == 'SELL':
                # 检查base_asset余额是否足够
                if adjusted_amount > await self.trader.get_available_balance(self.trader.base_asset):
                    self.logger.warning(f"S1: {self.trader.base_asset}余额不足，无法执行卖出操作")
                    return False

            self.logger.info(f"S1: Placing {side} order for {adjusted_amount:.8f} {self.trader.base_asset} at market price (approx {current_price})...")

            # 5. 使用 trader 的 exchange 客户端直接下单 (使用市价单确保执行调整)
            # 注意：市价单可能有滑点风险，对于大额调整需谨慎
            order = await self.trader.exchange.create_market_order(
                symbol=self.trader.symbol,
                side=side.lower(), # ccxt 通常需要小写
                amount=adjusted_amount
            )

            self.logger.info(f"S1: Adjustment order placed successfully. Order ID: {order.get('id', 'N/A')}")
            
            # 6. （可选）更新交易记录器 (如果希望S1交易也记录在案)
            if hasattr(self.trader, 'order_tracker'):
                 trade_info = {
                     'timestamp': time.time(),
                     'strategy': 'S1', # 标记来源
                     'side': side,
                     'price': float(order.get('average', current_price)), # 使用成交均价或市价
                     'amount': float(order.get('filled', adjusted_amount)), # 使用实际成交量
                     'order_id': order.get('id')
                     # 可以添加更多信息，如 cost, fee (如果API返回)
                 }
                 self.trader.order_tracker.add_trade(trade_info)
                 self.logger.info("S1: Trade logged in OrderTracker.")
                 
            # 7. 买入后如有多余资金，转入理财
            if side == 'BUY' and hasattr(self.trader, '_transfer_excess_funds'):
                try:
                    await self.trader._transfer_excess_funds()
                    self.logger.info("S1: 交易完成后尝试将多余资金转入理财")
                except Exception as e:
                    self.logger.warning(f"S1: 转移多余资金到理财失败: {e}")

            return True # 表示成功执行

        except Exception as e:
            self.logger.error(f"S1: Failed to execute adjustment order ({side} {amount_base_asset:.8f}): {e}", exc_info=True)
            return False

    async def check_s1_balance_and_transfer(self, value_needed, currency='USDT'):
        """
        检查S1策略触发后可用余额, 如果不够则尝试从理财账户赎回资金。
        """
        try:
            self.logger.info(f"S1: 需要现货账户余额: {value_needed:.2f} {currency}")
            # 获取当前可用余额
            available_balance = await self.trader.get_available_balance(currency)
            if available_balance >= value_needed:
                self.logger.info(f"S1: 可用余额足够: {available_balance:.2f} {currency}, 不需要赎回。")
            else:
                # 余额不足，尝试从理财账户赎回资金
                required = value_needed - available_balance
                # 添加20%缓冲
                required_with_buffer = required * 1.2
                
                self.logger.info(f"S1: 可用余额不足: {available_balance:.2f} {currency}, 需要赎回 {required_with_buffer:.2f} {currency}。")
                # 尝试从理财账户赎回资金
                max_single_transfer = 5000  # 假设单次最大划转5000
                while required_with_buffer > 0:
                    transfer_amount = min(required_with_buffer, max_single_transfer)
                    await self.trader.exchange.transfer_to_spot(currency, transfer_amount)
                    required_with_buffer -= transfer_amount
                    self.logger.info(f"预划转完成: {transfer_amount} {currency} | 剩余需划转: {required_with_buffer:.2f} {currency}")
                    
                self.logger.info("资金预划转完成，等待10秒确保到账")
                await asyncio.sleep(10)  # 等待资金到账
                
                # 再次检查余额
                available_balance = await self.trader.get_available_balance(currency)
                self.logger.info(f"赎回后余额检查 | 可用于S1策略交易的的现货{currency}: {available_balance:.2f}")
            
            return available_balance
                
        except Exception as e:
            self.logger.error(f"S1: 检查可用余额失败: {e}")
            return 0


    async def check_and_execute(self, risk_state: RiskState = RiskState.ALLOW_ALL):
        """
        高频检查 S1 仓位控制条件并执行调仓。
        应在主交易循环中频繁调用。

        Args:
            risk_state: 当前的风控状态，决定允许执行的操作类型
        """
        # 0. 确保我们有当天的 S1 边界值
        if self.s1_daily_high is None or self.s1_daily_low is None:
            self.logger.debug("S1: Daily high/low levels not available yet.")
            return # 等待下次数据更新

        # 1. 获取当前状态 (通过 trader 实例)
        try:
            current_price = self.trader.current_price
            if not current_price or current_price <= 0:
                self.logger.warning("S1: Invalid current price from trader.")
                return

            # 获取账户快照用于仓位计算
            spot_balance = await self.trader.exchange.fetch_balance()
            funding_balance = await self.trader.exchange.fetch_funding_balance()

            # 使用风控管理器的仓位计算方法
            position_pct = await self.trader.risk_manager._get_position_ratio(spot_balance, funding_balance)
            position_value = await self.trader.risk_manager._get_position_value(spot_balance, funding_balance)
            total_assets = await self.trader._get_pair_specific_assets_value()
            base_asset_balance = await self.trader.get_available_balance(self.trader.base_asset)

            if total_assets <= 0:
                self.logger.warning("S1: Invalid total assets value.")
                return

        except Exception as e:
            self.logger.error(f"S1: Failed to get current state: {e}")
            return

        # 2. 判断 S1 条件
        s1_action = 'NONE'
        s1_trade_amount_base_asset = 0

        # 高点检查
        if current_price > self.s1_daily_high and position_pct > self.s1_sell_target_pct:
            s1_action = 'SELL'
            target_position_value = total_assets * self.s1_sell_target_pct
            sell_value_needed = position_value - target_position_value
            # 确保不会卖出负数或零 (以防万一)
            if sell_value_needed > 0:
                available_balance = await self.check_s1_balance_and_transfer(sell_value_needed / current_price, self.trader.base_asset)
                if available_balance > 0:
                    s1_trade_amount_base_asset = min(sell_value_needed / current_price, available_balance)
                    self.logger.info(f"S1: High level breached. Need to SELL {s1_trade_amount_base_asset:.8f} {self.trader.base_asset} to reach {self.s1_sell_target_pct*100:.0f}% target.")
                else:
                    self.logger.warning(f"S1: Insufficient {self.trader.base_asset} balance for sell adjustment. Available: {available_balance:.8f} {self.trader.base_asset}")
                    s1_action = 'NONE'
            else:
                s1_action = 'NONE' # 重置，因为计算结果无效

        # 低点检查 (用 elif 避免同时触发)
        elif current_price < self.s1_daily_low and position_pct < self.s1_buy_target_pct:
            s1_action = 'BUY'
            target_position_value = total_assets * self.s1_buy_target_pct
            buy_value_needed = target_position_value - position_value
            # 确保不会买入负数或零
            if buy_value_needed > 0:
                s1_trade_amount_base_asset = buy_value_needed / current_price
                self.logger.info(f"S1: Low level breached. Need to BUY {s1_trade_amount_base_asset:.8f} {self.trader.base_asset} to reach {self.s1_buy_target_pct*100:.0f}% target.")
            else:
                s1_action = 'NONE' # 重置

        # 3. 如果触发，并且风控允许，才执行 S1 调仓
        if s1_action == 'SELL' and risk_state != RiskState.ALLOW_BUY_ONLY:
            if s1_trade_amount_base_asset > 1e-9:
                self.logger.info(f"S1: Condition met for SELL adjustment.")
                await self._execute_s1_adjustment('SELL', s1_trade_amount_base_asset)
        elif s1_action == 'BUY' and risk_state != RiskState.ALLOW_SELL_ONLY:
            if s1_trade_amount_base_asset > 1e-9:
                self.logger.info(f"S1: Condition met for BUY adjustment.")
                await self._execute_s1_adjustment('BUY', s1_trade_amount_base_asset)
        elif s1_action != 'NONE' and s1_trade_amount_base_asset > 1e-9:
            # 记录被风控阻止的操作
            self.logger.info(f"S1: {s1_action} signal detected but blocked by risk control (state: {risk_state.name})")
            # 注意：这里不等待执行结果，执行函数内部处理日志和错误
            # 也不更新网格的 base_price
        # else:
            # self.logger.debug(f"S1: No adjustment needed. Price={current_price:.2f} H={self.s1_daily_high:.2f} L={self.s1_daily_low:.2f} Pos={position_pct:.2%}") 