"""
配置加载器 (Config Loader)

实现混合配置加载策略：
1. 启动时从数据库加载所有配置到内存缓存
2. 提供 reload() 方法手动刷新缓存
3. 三级优先级：数据库 > 环境变量 > 默认值

使用方式：
    from src.config.loader import config_loader

    # 获取配置值
    value = config_loader.get('INITIAL_GRID')

    # 刷新缓存
    config_loader.reload()
"""

import os
import json
import logging
from typing import Any, Optional, Dict

from src.database.connection import db_manager
from src.database.models import Configuration, ConfigStatusEnum
from src.config.config_definitions import ALL_CONFIGS, get_config_by_key

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器 - 混合模式（启动时加载 + 缓存 + reload）"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._loaded = False
        self._default_values: Dict[str, str] = {}
        self._sensitive_keys = {
            config_def['config_key']
            for config_def in ALL_CONFIGS
            if config_def.get('is_sensitive')
        }

        # 构建默认值字典（从 config_definitions.py）
        for config_def in ALL_CONFIGS:
            self._default_values[config_def['config_key']] = config_def['default_value']

        # 首次加载配置
        self.reload()

    def reload(self):
        """重新从数据库加载所有配置到缓存"""
        try:
            logger.info("正在从数据库加载配置...")
            new_cache = {}

            with db_manager.get_session() as session:
                # 查询所有活跃配置
                configs = session.query(Configuration).filter(
                    Configuration.status == ConfigStatusEnum.ACTIVE
                ).all()

                for config in configs:
                    # 解析配置值
                    parsed_value = self._parse_value(
                        config.config_value,
                        config.data_type
                    )
                    new_cache[config.config_key] = parsed_value

            # 原子性更新缓存
            self._cache = new_cache
            self._loaded = True

            logger.info(f"✓ 成功加载 {len(self._cache)} 个配置项到缓存")

        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            if not self._loaded:
                # 首次加载失败，使用默认值
                logger.warning("使用默认配置值")
                self._cache = {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（三级优先级）

        优先级：
        1. 数据库缓存
        2. 环境变量（用于测试或临时覆盖）
        3. 配置默认值
        4. 函数默认参数

        Args:
            key: 配置键
            default: 如果所有来源都没有，返回此默认值

        Returns:
            配置值
        """
        # 1. 尝试从缓存读取（数据库配置）
        if key in self._cache:
            return self._cache[key]

        # 2. 尝试从环境变量读取
        env_value = os.getenv(key)
        if env_value is not None:
            # 根据配置定义解析类型
            try:
                config_def = get_config_by_key(key)
                return self._parse_value(env_value, config_def['data_type'])
            except ValueError:
                # 配置键不在定义中，返回原始字符串
                return env_value

        # 3. 使用配置定义中的默认值
        if key in self._default_values:
            default_value = self._default_values[key]
            # 解析默认值
            try:
                config_def = get_config_by_key(key)
                return self._parse_value(default_value, config_def['data_type'])
            except Exception:
                return default_value

        # 4. 返回函数参数的默认值
        return default

    def get_all(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        获取所有配置（用于导出）

        Args:
            include_sensitive: 是否包含敏感配置

        Returns:
            配置字典
        """
        result: Dict[str, Any] = {}
        for key, value in self._cache.items():
            if not include_sensitive and key in self._sensitive_keys:
                continue
            result[key] = value
        return result

    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值（仅更新缓存，不写入数据库）

        注意：要持久化配置，应该通过API端点更新数据库

        Args:
            key: 配置键
            value: 配置值

        Returns:
            是否成功
        """
        self._cache[key] = value
        return True

    def _parse_value(self, value: str, data_type: str) -> Any:
        """
        根据数据类型解析配置值

        Args:
            value: 字符串形式的配置值
            data_type: 数据类型（string/number/boolean/json）

        Returns:
            解析后的值
        """
        if data_type == 'string':
            return str(value)

        elif data_type == 'number':
            # 尝试转换为浮点数或整数
            try:
                if '.' in str(value):
                    return float(value)
                else:
                    return int(value)
            except (ValueError, TypeError):
                logger.warning(f"无法将 '{value}' 转换为数字，返回原始值")
                return value

        elif data_type == 'boolean':
            # 布尔值转换
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)

        elif data_type == 'json':
            # JSON解析
            if isinstance(value, (dict, list)):
                return value
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"无法解析JSON: {value}")
                return {}

        else:
            # 未知类型，返回原始值
            return value

    def is_loaded(self) -> bool:
        """检查配置是否已加载"""
        return self._loaded

    def get_cache_size(self) -> int:
        """获取缓存中的配置项数量"""
        return len(self._cache)

    def clear_cache(self):
        """清空缓存（用于测试）"""
        self._cache = {}
        self._loaded = False


# 全局配置加载器实例
config_loader = ConfigLoader()


# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """便捷函数：获取配置值"""
    return config_loader.get(key, default)


def reload_config():
    """便捷函数：重新加载配置"""
    config_loader.reload()


def get_all_configs(include_sensitive: bool = False) -> Dict[str, Any]:
    """便捷函数：获取所有配置"""
    return config_loader.get_all(include_sensitive)


if __name__ == '__main__':
    # 测试代码
    print("ConfigLoader 测试")
    print("=" * 60)

    # 测试获取配置
    print(f"INITIAL_GRID: {config_loader.get('INITIAL_GRID')}")
    print(f"MIN_TRADE_AMOUNT: {config_loader.get('MIN_TRADE_AMOUNT')}")
    print(f"SYMBOLS: {config_loader.get('SYMBOLS')}")
    print(f"ENABLE_STOP_LOSS: {config_loader.get('ENABLE_STOP_LOSS')}")
    print(f"GRID_PARAMS_JSON: {config_loader.get('GRID_PARAMS_JSON')}")

    # 测试API密钥配置
    print(f"\nBINANCE_API_KEY: {config_loader.get('BINANCE_API_KEY', '(未设置)')[:10]}...")

    # 缓存信息
    print(f"\n缓存状态:")
    print(f"  已加载: {config_loader.is_loaded()}")
    print(f"  配置数量: {config_loader.get_cache_size()}")

    print("\n✓ 测试完成")
