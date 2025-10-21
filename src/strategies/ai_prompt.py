"""
AI提示词模板和数据封装模块

负责:
1. 将交易数据封装成结构化格式
2. 生成AI分析所需的提示词
3. 解析AI响应
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class AIPromptBuilder:
    """AI提示词构建器"""

    @staticmethod
    def build_analysis_data(
        symbol: str,
        market_data: Dict,
        technical_indicators: Dict,
        sentiment_data: Dict,
        portfolio: Dict,
        recent_trades: List[Dict],
        grid_status: Dict,
        risk_metrics: Dict
    ) -> Dict:
        """
        构建发送给AI的结构化数据包

        Args:
            symbol: 交易对
            market_data: 市场数据 (价格、成交量等)
            technical_indicators: 技术指标
            sentiment_data: 市场情绪数据
            portfolio: 持仓状态
            recent_trades: 最近交易记录
            grid_status: 网格策略状态
            risk_metrics: 风险指标

        Returns:
            结构化数据字典
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "market_data": market_data,
            "technical_indicators": technical_indicators,
            "third_party_signals": sentiment_data,
            "portfolio_status": portfolio,
            "recent_trades": recent_trades[-10:],  # 只保留最近10笔
            "grid_strategy_status": grid_status,
            "risk_metrics": risk_metrics
        }

    @staticmethod
    def build_prompt(data: Dict) -> str:
        """
        构建AI分析提示词

        Args:
            data: build_analysis_data返回的结构化数据

        Returns:
            完整的提示词字符串
        """
        md = data['market_data']
        ti = data['technical_indicators']
        fg = data['third_party_signals'].get('fear_greed', {})
        portfolio = data['portfolio_status']
        grid = data['grid_strategy_status']
        risk = data['risk_metrics']

        prompt = f"""你是一个专业的加密货币交易分析助手。请基于以下数据进行综合分析并给出交易建议。

**重要**: 你的角色是为一个运行中的网格交易系统提供"趋势判断和大局建议"。
- 网格策略会自动捕获小幅波动(1-4%),提供稳定收益
- 你的任务是识别更大的趋势机会,给出中长期的交易建议
- 你的建议应该与网格策略"协同"而非"替代"

【市场数据】
- 交易对: {data['symbol']}
- 当前价格: {md.get('current_price', 0):.2f} USDT
- 24小时涨跌: {md.get('24h_change', 0)}
- 24小时成交量: {md.get('24h_volume', 0)}
- 24小时最高: {md.get('24h_high', 0):.2f} USDT
- 24小时最低: {md.get('24h_low', 0):.2f} USDT

【技术指标分析】
1. RSI(14): {ti['rsi']['value']:.1f} ({ti['rsi']['trend']})
   - 信号: {ti['rsi']['signal']}

2. MACD:
   - MACD值: {ti['macd']['macd']:.4f}
   - 信号线: {ti['macd']['signal']:.4f}
   - 柱状图: {ti['macd']['histogram']:.4f}
   - 趋势: {ti['macd']['trend']}
   - 交叉状态: {ti['macd']['crossover']}

3. 布林带:
   - 上轨: {ti['bollinger_bands']['upper']:.2f} USDT
   - 中轨: {ti['bollinger_bands']['middle']:.2f} USDT
   - 下轨: {ti['bollinger_bands']['lower']:.2f} USDT
   - 带宽: {ti['bollinger_bands']['width']:.2f}
   - 价格位置: {ti['bollinger_bands']['position']}

4. 移动平均线:
   - EMA20: {ti['ema_20']:.2f} USDT
   - EMA50: {ti['ema_50']:.2f} USDT

5. 成交量分析:
   - 当前成交量: {ti['volume_analysis']['current_volume']:.2f}
   - 平均成交量: {ti['volume_analysis']['avg_volume']:.2f}
   - 成交量比率: {ti['volume_analysis']['volume_ratio']:.2f}x
   - 趋势: {ti['volume_analysis']['trend']}

【市场情绪】
- 恐惧贪婪指数: {fg.get('value', 50)} ({fg.get('classification', 'Unknown')})
- 情绪趋势: {fg.get('trend', 'unknown')}
- 综合情绪: {data['third_party_signals'].get('overall_sentiment', 'neutral')}

【当前持仓状态】
- 账户总价值: {portfolio.get('total_value_usdt', 0):.2f} USDT
- 基础资产价值: {portfolio.get('base_asset_value', 0):.2f} USDT
- 报价资产余额: {portfolio.get('quote_asset_value', 0):.2f} USDT
- 仓位比例: {portfolio.get('position_ratio', 0)*100:.1f}% (基础资产/总资产)
- 未实现盈亏: {portfolio.get('unrealized_pnl', 0):.2f} USDT ({portfolio.get('pnl_percentage', 0):.2f}%)

【网格策略运行状态】
⚠️ **重要**: 网格策略正在自动运行,会在以下价位自动交易:
- 基准价格: {grid.get('base_price', 0):.2f} USDT
- 网格大小: {grid.get('grid_size', 0):.2f}%
- 上轨(卖出触发): {grid.get('upper_band', 0):.2f} USDT
- 下轨(买入触发): {grid.get('lower_band', 0):.2f} USDT
- 当前波动率: {grid.get('current_volatility', 0):.2f}
- 下次网格买入价: {grid.get('next_buy_price', 0):.2f} USDT
- 下次网格卖出价: {grid.get('next_sell_price', 0):.2f} USDT

💡 **网格策略特点**:
- 会在价格上涨{grid.get('grid_size', 0):.2f}%时自动卖出
- 会在价格下跌{grid.get('grid_size', 0):.2f}%时自动买入
- 适合捕获横盘震荡行情的小幅波动

【风险控制指标】
- 最大仓位限制: {risk.get('max_position_ratio', 0)*100:.0f}%
- 最小仓位限制: {risk.get('min_position_ratio', 0)*100:.0f}%
- 当前风控状态: {risk.get('current_risk_state', 'UNKNOWN')}
- 连续亏损次数: {risk.get('consecutive_losses', 0)}
- 最大回撤: {risk.get('max_drawdown', 'N/A')}

【最近交易记录】
{AIPromptBuilder._format_recent_trades(data['recent_trades'])}

【分析要求】
作为"交易大脑",请综合分析当前市场环境,并给出建议。请特别注意:

1. **与网格策略的协同性**:
   - 网格策略会自动处理{grid.get('grid_size', 0):.2f}%左右的小幅波动
   - 你应该关注更大的趋势机会(比如>5-10%的价格变动)
   - 你的建议应该是对网格策略的"补充"而非"替代"

2. **趋势判断**:
   - 是否存在明确的上涨或下跌趋势?
   - 技术指标是否形成多重共振信号?
   - 市场情绪是否支持该方向?

3. **仓位管理**:
   - 当前仓位比例({portfolio.get('position_ratio', 0)*100:.1f}%)是否合理?
   - 在当前趋势下,应该增仓、减仓还是持仓观望?

4. **风险收益比**:
   - 建议的交易机会是否有足够的风险收益比?
   - 是否值得在网格策略之外额外建仓?

5. **市场环境判断**:
   - 当前是趋势市场还是震荡市场?
   - 震荡市场: 建议hold,让网格策略发挥作用
   - 趋势市场: 可以给出buy/sell建议,配合趋势

【输出格式要求】
请严格按照以下JSON格式返回你的建议(只返回JSON,不要有其他文字):
{{
  "action": "buy/sell/hold",
  "confidence": 0-100之间的整数,
  "suggested_amount_pct": 10-25之间的整数(占总资产的百分比,因为是趋势交易建议更大仓位),
  "reason": "简要理由,说明为什么这是一个值得在网格之外额外操作的机会,不超过150字",
  "risk_level": "low/medium/high",
  "time_horizon": "short/medium/long",
  "stop_loss": 止损价格(数字)或null,
  "take_profit": 止盈价格(数字)或null,
  "additional_notes": "补充说明,特别是与网格策略的协同建议"
}}

注意:
- confidence低于60表示市场不明朗,建议hold让网格策略工作
- 只有在明确的趋势机会时才建议buy/sell
- suggested_amount_pct建议范围10%-25%(因为是趋势建议,金额应该比网格单次交易更大)
- 如果action是hold,suggested_amount_pct设为0
- 价格建议应考虑当前价格{md.get('current_price', 0):.2f} USDT
- **重要**: 在震荡市场中应该建议hold,让网格策略发挥优势
- **重要**: 只在明确的趋势信号(多指标共振+市场情绪一致)时才建议交易
"""

        return prompt

    @staticmethod
    def _format_recent_trades(trades: List[Dict]) -> str:
        """格式化最近交易记录"""
        if not trades:
            return "暂无交易记录"

        lines = []
        for i, trade in enumerate(trades[-5:], 1):  # 只显示最近5笔
            lines.append(
                f"{i}. {trade.get('time', 'N/A')} | "
                f"{trade.get('side', 'N/A')} | "
                f"价格: {trade.get('price', 0):.2f} | "
                f"数量: {trade.get('amount', 0):.4f} | "
                f"盈亏: {trade.get('pnl', 'N/A')}"
            )

        return "\n".join(lines)

    @staticmethod
    def parse_ai_response(response_text: str) -> Optional[Dict]:
        """
        解析AI响应

        Args:
            response_text: AI返回的文本

        Returns:
            解析后的建议字典,或None(解析失败)
        """
        try:
            # 尝试提取JSON部分
            # 有些AI可能在JSON前后添加说明文字
            start = response_text.find('{')
            end = response_text.rfind('}') + 1

            if start == -1 or end == 0:
                raise ValueError("响应中未找到JSON")

            json_str = response_text[start:end]
            result = json.loads(json_str)

            # 验证必要字段
            required_fields = ['action', 'confidence', 'suggested_amount_pct', 'reason']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"缺少必要字段: {field}")

            # 验证值的合理性
            if result['action'] not in ['buy', 'sell', 'hold']:
                raise ValueError(f"无效的action: {result['action']}")

            if not 0 <= result['confidence'] <= 100:
                raise ValueError(f"无效的confidence: {result['confidence']}")

            if not 0 <= result['suggested_amount_pct'] <= 50:
                raise ValueError(f"无效的suggested_amount_pct: {result['suggested_amount_pct']}")

            return result

        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {e}")
        except Exception as e:
            raise ValueError(f"响应解析异常: {e}")

    @staticmethod
    def validate_suggestion(suggestion: Dict, current_price: float, max_position: float) -> Tuple[bool, Optional[str]]:
        """
        验证AI建议的合理性

        Args:
            suggestion: AI返回的建议
            current_price: 当前价格
            max_position: 最大仓位比例

        Returns:
            (是否通过验证, 失败原因)
        """
        # 检查止损价是否合理
        if suggestion.get('stop_loss') is not None:
            stop_loss = float(suggestion['stop_loss'])
            if suggestion['action'] == 'buy' and stop_loss >= current_price:
                return False, f"买入止损价{stop_loss}应低于当前价{current_price}"
            if suggestion['action'] == 'sell' and stop_loss <= current_price:
                return False, f"卖出止损价{stop_loss}应高于当前价{current_price}"

        # 检查止盈价是否合理
        if suggestion.get('take_profit') is not None:
            take_profit = float(suggestion['take_profit'])
            if suggestion['action'] == 'buy' and take_profit <= current_price:
                return False, f"买入止盈价{take_profit}应高于当前价{current_price}"
            if suggestion['action'] == 'sell' and take_profit >= current_price:
                return False, f"卖出止盈价{take_profit}应低于当前价{current_price}"

        # 检查金额比例
        amount_pct = suggestion['suggested_amount_pct']
        if amount_pct > 30:
            return False, f"建议金额比例过高: {amount_pct}%"

        # 检查置信度和行动的匹配
        if suggestion['confidence'] < 50 and suggestion['action'] != 'hold':
            return False, f"低置信度({suggestion['confidence']}%)不应建议交易"

        return True, None
