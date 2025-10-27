"""
AI辅助交易策略模块

基于技术指标、市场情绪和持仓信息,调用AI进行综合分析并给出交易建议。

核心流程:
1. 收集并计算技术指标
2. 获取第三方市场情绪数据
3. 封装当前持仓和交易历史
4. 发送给AI模型进行分析
5. 解析AI响应并执行交易决策

支持的AI提供商:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- 本地模型 (可扩展)
"""

import logging
import json
import time
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

# AI SDK导入 (优雅降级)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None
    logging.warning("OpenAI SDK未安装,无法使用OpenAI模型")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("Anthropic SDK未安装,无法使用Claude模型")

from src.strategies.technical_indicators import TechnicalIndicators
from src.strategies.market_sentiment import get_market_sentiment
from src.strategies.multi_timeframe import MultiTimeframeAnalyzer
from src.config.settings import settings


class AIProvider(Enum):
    """AI提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class TriggerReason(Enum):
    """AI触发原因"""
    TECHNICAL_SIGNAL = "technical_signal"  # 技术指标重大变化
    TIME_INTERVAL = "time_interval"  # 时间周期到达
    POSITION_CHANGE = "position_change"  # 仓位变化
    MARKET_VOLATILITY = "market_volatility"  # 市场异常波动
    MANUAL = "manual"  # 手动触发


class AITradingStrategy:
    """AI辅助交易策略"""

    def __init__(self, trader_instance):
        """
        初始化AI策略

        Args:
            trader_instance: 主GridTrader实例
        """
        self.trader = trader_instance
        self.logger = logging.getLogger(self.__class__.__name__)

        # 技术指标计算器
        self.indicators_calculator = TechnicalIndicators()

        # 🆕 多时间周期分析器
        self.multi_timeframe_analyzer = MultiTimeframeAnalyzer()

        # 市场情绪数据获取器
        self.sentiment_data = get_market_sentiment()

        # AI配置 (从环境变量读取)
        self.ai_enabled = getattr(settings, 'AI_ENABLED', False)
        self.ai_provider = AIProvider(getattr(settings, 'AI_PROVIDER', 'openai'))
        self.ai_model = getattr(settings, 'AI_MODEL', 'gpt-4-turbo')
        self.ai_api_key = getattr(settings, 'AI_API_KEY', None)
        self.ai_openai_base_url = getattr(settings, 'AI_OPENAI_BASE_URL', None)
        self.confidence_threshold = getattr(settings, 'AI_CONFIDENCE_THRESHOLD', 70)
        self.trigger_interval = getattr(settings, 'AI_TRIGGER_INTERVAL', 900)  # 15分钟
        self.max_calls_per_day = getattr(settings, 'AI_MAX_CALLS_PER_DAY', 100)
        self.fallback_to_grid = getattr(settings, 'AI_FALLBACK_TO_GRID', True)

        # 状态跟踪
        self.last_trigger_time = 0
        self.last_indicators = None
        self.ai_call_count_today = 0
        self.last_reset_date = datetime.now().date()
        self.consecutive_failures = 0
        self.ai_suggestions_history = []  # 保存历史建议用于学习

        # 初始化AI客户端
        self._initialize_ai_client()

        self.logger.info(
            f"AI策略初始化完成 | "
            f"启用: {self.ai_enabled} | "
            f"提供商: {self.ai_provider.value} | "
            f"模型: {self.ai_model} | "
            f"置信度阈值: {self.confidence_threshold}%"
        )

    def _initialize_ai_client(self):
        """初始化AI客户端"""
        if not self.ai_enabled:
            self.ai_client = None
            return

        if self.ai_provider == AIProvider.OPENAI:
            if not OPENAI_AVAILABLE:
                self.logger.error("OpenAI SDK未安装,无法使用OpenAI")
                self.ai_client = None
                return

            if not self.ai_api_key:
                self.logger.error("未配置OPENAI_API_KEY")
                self.ai_client = None
                return

            client_kwargs = {"api_key": self.ai_api_key}
            if self.ai_openai_base_url:
                client_kwargs["base_url"] = self.ai_openai_base_url

            if hasattr(openai, "OpenAI"):
                self.ai_client = openai.OpenAI(**client_kwargs)
            else:
                openai.api_key = self.ai_api_key
                if self.ai_openai_base_url:
                    setattr(openai, "base_url", self.ai_openai_base_url)
                    setattr(openai, "api_base", self.ai_openai_base_url)
                self.ai_client = openai

            base_info = self.ai_openai_base_url or "默认"
            self.logger.info(f"OpenAI客户端初始化成功 | Base URL: {base_info}")

        elif self.ai_provider == AIProvider.ANTHROPIC:
            if not ANTHROPIC_AVAILABLE:
                self.logger.error("Anthropic SDK未安装,无法使用Claude")
                self.ai_client = None
                return

            if not self.ai_api_key:
                self.logger.error("未配置ANTHROPIC_API_KEY")
                self.ai_client = None
                return

            self.ai_client = anthropic.Anthropic(api_key=self.ai_api_key)
            self.logger.info("Anthropic客户端初始化成功")

        else:
            self.logger.warning("不支持的AI提供商,AI功能禁用")
            self.ai_client = None

    async def should_trigger(self, current_price: float) -> Tuple[bool, Optional[TriggerReason]]:
        """
        判断是否应该触发AI分析

        Args:
            current_price: 当前价格

        Returns:
            (是否触发, 触发原因)
        """
        if not self.ai_enabled or self.ai_client is None:
            return False, None

        # 检查每日调用限制
        self._check_daily_limit()
        if self.ai_call_count_today >= self.max_calls_per_day:
            self.logger.warning(f"今日AI调用已达上限: {self.max_calls_per_day}")
            return False, None

        now = time.time()

        # 触发条件1: 时间周期触发
        if now - self.last_trigger_time >= self.trigger_interval:
            self.logger.info(f"时间周期触发: 距上次{(now - self.last_trigger_time)/60:.1f}分钟")
            return True, TriggerReason.TIME_INTERVAL

        # 获取当前技术指标 (用于后续判断)
        try:
            prices, volumes = await self._fetch_recent_klines()
            current_indicators = self.indicators_calculator.calculate_all_indicators(
                prices, volumes
            )
        except Exception as e:
            self.logger.error(f"获取技术指标失败: {e}")
            return False, None

        # 触发条件2: 技术指标重大变化
        if self.last_indicators is not None:
            if self._has_significant_indicator_change(current_indicators):
                self.logger.info("技术指标重大变化触发")
                return True, TriggerReason.TECHNICAL_SIGNAL

        # 触发条件3: 市场异常波动 (1小时涨跌超过5%)
        if len(prices) >= 12:  # 至少12根5分钟K线
            hour_ago_price = prices[-12]
            price_change_pct = abs((current_price - hour_ago_price) / hour_ago_price)
            if price_change_pct > 0.05:  # 5%
                self.logger.warning(
                    f"市场异常波动触发: 1小时变化{price_change_pct*100:.2f}%"
                )
                return True, TriggerReason.MARKET_VOLATILITY

        # 保存当前指标用于下次对比
        self.last_indicators = current_indicators

        return False, None

    def _has_significant_indicator_change(self, current: Dict) -> bool:
        """
        检测技术指标是否有重大变化

        Args:
            current: 当前指标

        Returns:
            是否有重大变化
        """
        prev = self.last_indicators

        # MACD金叉/死叉
        if current['macd']['crossover'] in ['golden_cross', 'death_cross']:
            self.logger.info(f"MACD {current['macd']['crossover']}")
            return True

        # RSI跨越超买超卖阈值
        prev_rsi = prev['rsi']['value']
        curr_rsi = current['rsi']['value']
        if (prev_rsi < 30 and curr_rsi >= 30) or (prev_rsi > 70 and curr_rsi <= 70):
            self.logger.info(f"RSI跨越阈值: {prev_rsi:.1f} -> {curr_rsi:.1f}")
            return True

        # 布林带突破
        prev_bb_pos = prev['bollinger_bands']['position']
        curr_bb_pos = current['bollinger_bands']['position']
        if prev_bb_pos != curr_bb_pos and curr_bb_pos in ['above', 'below']:
            self.logger.info(f"布林带突破: {curr_bb_pos}")
            return True

        return False

    async def _fetch_recent_klines(self, limit: int = 100) -> Tuple[List[float], List[float]]:
        """
        获取最近的K线数据

        Args:
            limit: 数量

        Returns:
            (价格列表, 成交量列表)
        """
        try:
            # 使用5分钟K线
            klines = await self.trader.exchange.fetch_ohlcv(
                self.trader.symbol,
                timeframe='5m',
                limit=limit
            )

            if not klines or len(klines) < 50:
                raise ValueError(f"K线数据不足: {len(klines) if klines else 0}")

            # 提取收盘价和成交量
            prices = [float(k[4]) for k in klines]  # close price
            volumes = [float(k[5]) for k in klines]  # volume

            return prices, volumes

        except Exception as e:
            self.logger.error(f"获取K线数据失败: {e}")
            raise

    def _check_daily_limit(self):
        """检查并重置每日调用计数"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.logger.info(
                f"新的一天开始,重置AI调用计数 | "
                f"昨日调用: {self.ai_call_count_today}次"
            )
            self.ai_call_count_today = 0
            self.last_reset_date = today

    async def analyze_and_suggest(self, trigger_reason: TriggerReason) -> Optional[Dict]:
        """
        执行AI分析并返回交易建议

        Args:
            trigger_reason: 触发原因

        Returns:
            AI建议字典或None
        """
        from src.strategies.ai_prompt import AIPromptBuilder

        self.logger.info(f"开始AI分析 | 触发原因: {trigger_reason.value}")

        try:
            # 收集数据
            analysis_data = await self._collect_analysis_data()

            # 构建提示词
            prompt = AIPromptBuilder.build_prompt(analysis_data)

            # 调用AI
            ai_response = await self._call_ai_model(prompt)

            if not ai_response:
                self.logger.error("AI调用失败")
                self.consecutive_failures += 1
                return None

            # 解析响应
            suggestion = AIPromptBuilder.parse_ai_response(ai_response)

            if not suggestion:
                self.logger.error("AI响应解析失败")
                self.consecutive_failures += 1
                return None

            # 验证建议
            is_valid, error_msg = AIPromptBuilder.validate_suggestion(
                suggestion,
                analysis_data['market_data']['current_price'],
                analysis_data['risk_metrics']['max_position_ratio']
            )

            if not is_valid:
                self.logger.warning(f"AI建议验证失败: {error_msg}")
                return None

            # 记录成功
            self.consecutive_failures = 0
            self.ai_call_count_today += 1
            self.last_trigger_time = time.time()

            # 保存到历史
            suggestion['timestamp'] = datetime.now().isoformat()
            suggestion['trigger_reason'] = trigger_reason.value
            self.ai_suggestions_history.append(suggestion)
            if len(self.ai_suggestions_history) > 100:
                self.ai_suggestions_history.pop(0)

            self.logger.info(
                f"AI分析完成 | "
                f"建议: {suggestion['action']} | "
                f"置信度: {suggestion['confidence']}% | "
                f"金额: {suggestion['suggested_amount_pct']}%"
            )

            return suggestion

        except Exception as e:
            self.logger.error(f"AI分析异常: {e}", exc_info=True)
            self.consecutive_failures += 1
            return None

    async def _collect_analysis_data(self) -> Dict:
        """收集AI分析所需的所有数据"""
        from src.strategies.ai_prompt import AIPromptBuilder

        # 获取K线数据 (当前使用5分钟作为基准)
        prices, volumes = await self._fetch_recent_klines()

        # 计算技术指标 (基于5分钟)
        indicators = self.indicators_calculator.calculate_all_indicators(prices, volumes)

        # 🆕 多时间周期分析
        self.logger.info("开始多时间周期分析...")
        multi_timeframe_data = await self.multi_timeframe_analyzer.analyze_multi_timeframe(
            self.trader.exchange,
            self.trader.symbol,
            self.indicators_calculator
        )
        self.logger.info("多时间周期分析完成")

        # 获取市场情绪
        sentiment = await self.sentiment_data.get_comprehensive_sentiment()

        # 市场数据
        current_price = await self.trader._get_latest_price()
        ticker = await self.trader.exchange.fetch_ticker(self.trader.symbol)

        market_data = {
            'current_price': current_price,
            '24h_change': ticker.get('percentage', 0),
            '24h_volume': ticker.get('quoteVolume', 0),
            '24h_high': ticker.get('high', 0),
            '24h_low': ticker.get('low', 0)
        }

        # 持仓状态
        total_value = await self.trader._get_pair_specific_assets_value()
        balance = await self.trader.exchange.fetch_balance()
        funding_balance = await self.trader.exchange.fetch_funding_balance()

        base_amount = (
            float(balance.get('free', {}).get(self.trader.base_asset, 0)) +
            float(funding_balance.get(self.trader.base_asset, 0))
        )
        base_value = base_amount * current_price
        quote_value = (
            float(balance.get('free', {}).get(self.trader.quote_asset, 0)) +
            float(funding_balance.get(self.trader.quote_asset, 0))
        )

        position_ratio = base_value / total_value if total_value > 0 else 0

        # 计算盈亏
        initial_principal = getattr(settings, 'INITIAL_PRINCIPAL', 0)
        unrealized_pnl = total_value - initial_principal if initial_principal > 0 else 0
        pnl_pct = (unrealized_pnl / initial_principal * 100) if initial_principal > 0 else 0

        portfolio = {
            'total_value_usdt': total_value,
            'base_asset_value': base_value,
            'quote_asset_value': quote_value,
            'position_ratio': position_ratio,
            'unrealized_pnl': unrealized_pnl,
            'pnl_percentage': pnl_pct
        }

        # 网格状态
        grid_status = {
            'base_price': self.trader.base_price,
            'grid_size': self.trader.grid_size,
            'upper_band': self.trader._get_upper_band(),
            'lower_band': self.trader._get_lower_band(),
            'current_volatility': getattr(self.trader, 'last_volatility', 0),
            'next_buy_price': self.trader._get_lower_band(),
            'next_sell_price': self.trader._get_upper_band()
        }

        # 风险指标
        risk_metrics = {
            'max_position_ratio': settings.MAX_POSITION_RATIO,
            'min_position_ratio': settings.MIN_POSITION_RATIO,
            'current_risk_state': getattr(self.trader, 'current_risk_state', 'ALLOW_ALL'),
            'consecutive_losses': getattr(self.trader, 'consecutive_failures', 0),
            'max_drawdown': 'N/A'  # TODO: 实现最大回撤计算
        }

        # 最近交易
        recent_trades = []
        if hasattr(self.trader, 'order_tracker'):
            trades = self.trader.order_tracker.get_trade_history()
            recent_trades = [
                {
                    'time': datetime.fromtimestamp(t['timestamp']).strftime('%Y-%m-%d %H:%M'),
                    'side': t.get('side', 'N/A'),
                    'price': t.get('price', 0),
                    'amount': t.get('amount', 0),
                    'pnl': f"{t.get('profit', 0):.2f} USDT" if 'profit' in t else 'N/A'
                }
                for t in trades[-10:]
            ]

        return AIPromptBuilder.build_analysis_data(
            symbol=self.trader.symbol,
            market_data=market_data,
            technical_indicators=indicators,
            sentiment_data=sentiment,
            portfolio=portfolio,
            recent_trades=recent_trades,
            grid_status=grid_status,
            risk_metrics=risk_metrics,
            multi_timeframe=multi_timeframe_data  # 🆕 多时间周期数据
        )

    async def _call_ai_model(self, prompt: str) -> Optional[str]:
        """
        调用AI模型

        Args:
            prompt: 提示词

        Returns:
            AI返回的文本
        """
        if self.ai_provider == AIProvider.OPENAI:
            return await self._call_openai(prompt)
        elif self.ai_provider == AIProvider.ANTHROPIC:
            return await self._call_anthropic(prompt)
        else:
            self.logger.error("不支持的AI提供商")
            return None

    async def _call_openai(self, prompt: str) -> Optional[str]:
        """调用OpenAI API"""
        try:
            response = await asyncio.to_thread(
                self.ai_client.chat.completions.create,
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": "You are a professional cryptocurrency trading analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"OpenAI API调用失败: {e}")
            return None

    async def _call_anthropic(self, prompt: str) -> Optional[str]:
        """调用Anthropic API"""
        try:
            response = await asyncio.to_thread(
                self.ai_client.messages.create,
                model=self.ai_model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Anthropic API调用失败: {e}")
            return None
