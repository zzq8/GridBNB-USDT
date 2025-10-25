import os
from dotenv import load_dotenv
import logging
import json
from pydantic_settings import BaseSettings
from typing import Optional, Dict
from pydantic import field_validator, ConfigDict, ConfigDict

from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent.parent / "config" / ".env")

class Settings(BaseSettings):
    """应用程序设置类，使用Pydantic进行类型验证和环境变量管理"""

    # --- 交易所选择配置 (企业级多交易所支持) ---
    EXCHANGE: str = "binance"  # 选择交易所: binance, okx

    # --- 从 .env 文件读取的必需配置 ---
    # Binance API
    BINANCE_API_KEY: str = ""  # 添加默认值以便测试
    BINANCE_API_SECRET: str = ""  # 添加默认值以便测试

    # OKX API (如果使用OKX)
    OKX_API_KEY: str = ""
    OKX_API_SECRET: str = ""
    OKX_PASSPHRASE: str = ""  # OKX特有参数

    # --- 策略核心配置 (从 .env 读取) ---
    SYMBOLS: str = "BNB/USDT"  # 从 .env 读取交易对列表字符串

    # 按交易对设置的初始参数 (JSON格式)
    INITIAL_PARAMS_JSON: Dict[str, Dict[str, float]] = {}

    INITIAL_GRID: float = 2.0  # 全局默认网格大小
    MIN_TRADE_AMOUNT: float = 20.0

    # --- 初始状态设置 (从 .env 读取) ---
    INITIAL_PRINCIPAL: float = 0.0

    # --- 可选配置 (从 .env 读取) ---
    PUSHPLUS_TOKEN: Optional[str] = None

    # --- 新增：告警系统配置 (阶段3优化) ---
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    WEBHOOK_URL: Optional[str] = None

    # 理财功能开关
    ENABLE_SAVINGS_FUNCTION: bool = True

    WEB_USER: Optional[str] = None
    WEB_PASSWORD: Optional[str] = None
    HTTP_PROXY: Optional[str] = None

    # --- 理财精度配置 (从JSON字符串解析) ---
    SAVINGS_PRECISIONS: Dict[str, int] = {'USDT': 2, 'BNB': 6, 'DEFAULT': 8}

    # --- 新增：从 .env 读取的高级策略配置 ---
    GRID_PARAMS_JSON: Dict = {}
    GRID_CONTINUOUS_PARAMS_JSON: Dict = {}
    DYNAMIC_INTERVAL_PARAMS_JSON: Dict = {}
    ENABLE_VOLUME_WEIGHTING: bool = True

    # --- AI辅助交易配置 ---
    AI_ENABLED: bool = False
    AI_PROVIDER: str = "openai"  # openai / anthropic
    AI_MODEL: str = "gpt-4-turbo"
    AI_API_KEY: Optional[str] = None
    AI_OPENAI_BASE_URL: Optional[str] = None
    AI_CONFIDENCE_THRESHOLD: int = 70
    AI_TRIGGER_INTERVAL: int = 900  # 秒 (15分钟)
    AI_MAX_CALLS_PER_DAY: int = 100
    AI_FALLBACK_TO_GRID: bool = True

    @field_validator('INITIAL_PARAMS_JSON', mode='before')
    @classmethod
    def parse_initial_params(cls, value):
        """解析按交易对设置的初始参数JSON字符串"""
        if isinstance(value, str) and value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError("INITIAL_PARAMS_JSON 格式无效，必须是合法的JSON字符串。")
        return value if value else {}  # 如果为空，返回空字典

    @field_validator('GRID_PARAMS_JSON', 'GRID_CONTINUOUS_PARAMS_JSON', 'DYNAMIC_INTERVAL_PARAMS_JSON', mode='before')
    @classmethod
    def parse_strategy_params_json(cls, value):
        """通用验证器，用于将策略相关的JSON字符串解析为字典"""
        if isinstance(value, str) and value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError(f"策略参数格式无效，必须是合法的JSON字符串。收到的值: {value}")
        return value if value else {}

    @field_validator('SAVINGS_PRECISIONS', mode='before')
    @classmethod
    def parse_savings_precisions(cls, value):
        """自定义验证器，用于将JSON字符串解析为字典"""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError("SAVINGS_PRECISIONS 格式无效，必须是合法的JSON字符串。")
        return value

    # --- 新增验证器：增强环境变量验证 ---

    @field_validator('BINANCE_API_KEY')
    @classmethod
    def validate_api_key(cls, v):
        """验证 Binance API Key 格式"""
        # 测试环境下允许空值
        if os.getenv('PYTEST_CURRENT_TEST'):
            return v
        if not v:
            raise ValueError("BINANCE_API_KEY 不能为空")
        if len(v) < 64:
            raise ValueError(f"BINANCE_API_KEY 格式无效: 长度应至少64位，当前 {len(v)} 位")
        return v

    @field_validator('BINANCE_API_SECRET')
    @classmethod
    def validate_api_secret(cls, v):
        """验证 Binance API Secret 格式"""
        # 测试环境下允许空值
        if os.getenv('PYTEST_CURRENT_TEST'):
            return v
        if not v:
            raise ValueError("BINANCE_API_SECRET 不能为空")
        if len(v) < 64:
            raise ValueError(f"BINANCE_API_SECRET 格式无效: 长度应至少64位，当前 {len(v)} 位")
        return v

    @field_validator('MIN_TRADE_AMOUNT')
    @classmethod
    def validate_min_trade_amount(cls, v):
        """验证最小交易金额"""
        if v < 10:
            raise ValueError(f"MIN_TRADE_AMOUNT 必须 >= 10 USDT (Binance 最小限制)，当前设置为 {v}")
        if v > 10000:
            logging.warning(f"MIN_TRADE_AMOUNT 设置过高 ({v} USDT)，建议在 10-1000 之间")
        return v

    @field_validator('INITIAL_GRID')
    @classmethod
    def validate_initial_grid(cls, v):
        """验证初始网格大小"""
        if v < 0.1 or v > 10:
            raise ValueError(f"INITIAL_GRID 必须在 0.1-10% 之间，当前设置为 {v}%")
        if v < 1.0:
            logging.warning(f"INITIAL_GRID 设置过小 ({v}%)，可能导致频繁交易和高手续费")
        return v

    @field_validator('SYMBOLS')
    @classmethod
    def validate_symbols(cls, v):
        """验证交易对列表格式"""
        if not v:
            raise ValueError("SYMBOLS 不能为空")
        symbols = [s.strip() for s in v.split(',')]
        for symbol in symbols:
            if '/' not in symbol:
                raise ValueError(f"交易对格式无效: {symbol}，应为 'BASE/QUOTE' 格式 (如 BNB/USDT)")
            base, quote = symbol.split('/')
            if not base or not quote:
                raise ValueError(f"交易对格式无效: {symbol}")
        return v

    @field_validator('INITIAL_PRINCIPAL')
    @classmethod
    def validate_initial_principal(cls, v):
        """验证初始本金"""
        if v < 0:
            raise ValueError(f"INITIAL_PRINCIPAL 不能为负数，当前设置为 {v}")
        if v > 0 and v < 100:
            logging.warning(f"INITIAL_PRINCIPAL 设置过小 ({v} USDT)，建议至少 500 USDT")
        return v

    @field_validator('AI_PROVIDER')
    @classmethod
    def validate_ai_provider(cls, v):
        """验证AI提供商"""
        valid_providers = ['openai', 'anthropic']
        if v not in valid_providers:
            raise ValueError(f"AI_PROVIDER 必须是 {valid_providers} 之一，当前设置为 {v}")
        return v

    @field_validator('AI_CONFIDENCE_THRESHOLD')
    @classmethod
    def validate_ai_confidence(cls, v):
        """验证AI置信度阈值"""
        if v < 0 or v > 100:
            raise ValueError(f"AI_CONFIDENCE_THRESHOLD 必须在 0-100 之间，当前设置为 {v}")
        if v < 50:
            logging.warning(f"AI_CONFIDENCE_THRESHOLD 设置过低 ({v}%)，建议至少50%")
        return v

    @field_validator('AI_TRIGGER_INTERVAL')
    @classmethod
    def validate_ai_trigger_interval(cls, v):
        """验证AI触发间隔"""
        if v < 60:
            raise ValueError(f"AI_TRIGGER_INTERVAL 不能小于60秒，当前设置为 {v}")
        if v < 300:
            logging.warning(f"AI_TRIGGER_INTERVAL 设置过短 ({v}秒)，可能导致频繁调用AI")
        return v

    @field_validator('AI_MAX_CALLS_PER_DAY')
    @classmethod
    def validate_ai_max_calls(cls, v):
        """验证每日最大AI调用次数"""
        if v < 1:
            raise ValueError(f"AI_MAX_CALLS_PER_DAY 必须至少为1，当前设置为 {v}")
        if v > 500:
            logging.warning(f"AI_MAX_CALLS_PER_DAY 设置过高 ({v})，可能产生高额费用")
        return v

    # --- 固定配置 (不常修改，保留在代码中) ---
    MIN_POSITION_PERCENT: float = 0.05
    MAX_POSITION_PERCENT: float = 0.15
    MAX_POSITION_RATIO: float = 0.9
    MIN_POSITION_RATIO: float = 0.1
    COOLDOWN: int = 60
    SAFETY_MARGIN: float = 0.95
    AUTO_ADJUST_BASE_PRICE: bool = False
    PUSHPLUS_TIMEOUT: int = 5
    LOG_LEVEL: int = logging.INFO
    DEBUG_MODE: bool = False
    API_TIMEOUT: int = 10000
    RECV_WINDOW: int = 5000
    RISK_CHECK_INTERVAL: int = 300
    MAX_RETRIES: int = 5
    RISK_FACTOR: float = 0.1
    VOLATILITY_WINDOW: int = 52  # 52日窗口
    VOLATILITY_EWMA_LAMBDA: float = 0.94  # EWMA衰减因子 (RiskMetrics标准)
    VOLATILITY_HYBRID_WEIGHT: float = 0.7  # EWMA权重，传统波动率权重为0.3

    # --- 交易限制配置 ---
    MIN_NOTIONAL_VALUE: float = 10.0  # 最小订单名义价值 (quote currency)
    MIN_AMOUNT_LIMIT: float = 0.0001  # 最小交易数量
    MAX_SINGLE_TRANSFER: float = 5000.0  # 单次最大划转金额
    POSITION_SCALE_FACTOR: float = 0.2

    # 常量化魔术数字
    SPOT_FUNDS_TARGET_RATIO: float = 0.16
    MIN_BNB_TRANSFER: float = 0.01

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'  # 忽略额外的字段
    )

# 创建全局设置实例
settings = Settings()

# 提供一个解析后的列表，方便使用
SYMBOLS_LIST = [s.strip() for s in settings.SYMBOLS.split(',') if s.strip()]

# 保留必要的向后兼容性常量，但建议逐步迁移到 settings.XXX 的形式
FLIP_THRESHOLD = lambda grid_size: (grid_size / 5) / 100  # 网格大小的1/5的1%

class TradingConfig:
    """
    交易配置类，现在只包含从settings派生或转换而来的复杂策略参数。
    简单的配置项直接从全局的 settings 对象获取。

    这个类的职责：
    1. 将JSON格式的策略参数转换为Python字典
    2. 为复杂的策略参数提供默认值
    3. 进行配置验证
    """

    RISK_PARAMS = {
        'position_limit': settings.MAX_POSITION_RATIO
    }

    # 将硬编码的字典替换为从 settings 中获取，如果为空则使用默认值
    GRID_PARAMS = settings.GRID_PARAMS_JSON if settings.GRID_PARAMS_JSON else {
        'initial': settings.INITIAL_GRID,
        'min': 1.0,  # 网格大小的绝对最小值
        'max': 4.0,  # 网格大小的绝对最大值
        'volatility_threshold': {
            'ranges': [
                # --- 更直接、更敏感的波动率-网格映射关系 ---
                {'range': [0, 0.10], 'grid': 1.0},      # 波动率 0% 到 10% (不含)，网格 1.0%
                {'range': [0.10, 0.20], 'grid': 2.0},   # 波动率 10% 到 20% (不含)，网格 2.0%
                {'range': [0.20, 0.30], 'grid': 3.0},   # 波动率 20% 到 30% (不含)，网格 3.0%
                {'range': [0.30, 0.40], 'grid': 4.0},   # 波动率 30% 到 40% (不含)，网格 4.0%
                {'range': [0.40, 999], 'grid': 4.0}     # 波动率 40% 及以上，统一使用最大网格 4.0%
            ]
        }
    }

    # 连续网格调整参数
    GRID_CONTINUOUS_PARAMS = settings.GRID_CONTINUOUS_PARAMS_JSON if settings.GRID_CONTINUOUS_PARAMS_JSON else {
        'base_grid': 2.5,          # 波动率处于中心点时，我们期望的基础网格大小 (例如 2.5%)
        'center_volatility': 0.25, # 我们定义的市场"正常"波动率水平 (例如 0.25 或 25%)
        'sensitivity_k': 10.0      # 灵敏度系数k。k越大，网格对波动率变化的反应越剧烈。
                                   # k=10.0 意味着波动率每变化1%(0.01)，网格大小变化 0.1% (10.0 * 0.01)
    }

    # 成交量加权波动率计算开关
    ENABLE_VOLUME_WEIGHTING = settings.ENABLE_VOLUME_WEIGHTING

    # 动态时间间隔参数
    DYNAMIC_INTERVAL_PARAMS = settings.DYNAMIC_INTERVAL_PARAMS_JSON if settings.DYNAMIC_INTERVAL_PARAMS_JSON else {
        # 定义波动率区间与对应调整间隔（小时）的映射关系
        'volatility_to_interval_hours': [
            # 格式: {'range': [最低波动率(含), 最高波动率(不含)], 'interval_hours': 对应的小时间隔}
            # --- 与新的网格映射保持一致的时间间隔 ---
            {'range': [0, 0.10], 'interval_hours': 1.0},      # 波动率 < 10%，每 1 小时检查一次
            {'range': [0.10, 0.20], 'interval_hours': 0.5},   # 波动率 10-20%，每 30 分钟检查一次
            {'range': [0.20, 0.30], 'interval_hours': 0.25},  # 波动率 20-30%，每 15 分钟检查一次
            {'range': [0.30, 999], 'interval_hours': 0.125},  # 波动率 > 30%，每 7.5 分钟检查一次
        ],
        # 定义一个默认间隔，以防波动率计算失败或未匹配到任何区间
        'default_interval_hours': 1.0
    }

    # 保留的策略相关基础值
    BASE_AMOUNT = 50.0  # 基础交易金额（可调整）

    def __init__(self):
        # 添加配置验证
        if settings.MIN_POSITION_RATIO >= settings.MAX_POSITION_RATIO:
            raise ValueError("底仓比例不能大于或等于最大仓位比例")

        if self.GRID_PARAMS['min'] > self.GRID_PARAMS['max']:
            raise ValueError("网格最小值不能大于最大值")

        # API密钥验证已由Pydantic在settings实例化时自动完成

        # 验证数值范围
        if settings.INITIAL_PRINCIPAL < 0:
            raise ValueError("INITIAL_PRINCIPAL不能为负数")

        # INITIAL_BASE_PRICE已移除，现在使用INITIAL_PARAMS_JSON中的交易对特定配置
        
    # Removed unused update methods (update_risk_params, update_grid_params, 
    # update_symbol, update_initial_base_price, update_risk_check_interval, 
    # update_max_retries, update_risk_factor, update_base_amount, 
    # update_min_trade_amount, update_max_position_ratio, 
    # update_min_position_ratio, update_all)

    # Removed unused validate_config method
# End of class definition 
