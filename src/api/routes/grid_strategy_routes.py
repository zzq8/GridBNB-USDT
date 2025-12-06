"""
网格策略 API 路由

提供网格策略的 RESTful API 接口

创建日期: 2025-11-07
作者: AI Assistant
版本: v1.0.0
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from pydantic import BaseModel
import json
import os
import logging

from src.strategies.grid_strategy_config import GridStrategyConfig, StrategyTemplates

router = APIRouter(prefix="/api/grid-strategies", tags=["grid-strategies"])
logger = logging.getLogger(__name__)

# ========================================
# 📁 数据存储配置
# ========================================
STRATEGIES_DIR = os.path.join(os.path.dirname(__file__), '../data/strategies')
os.makedirs(STRATEGIES_DIR, exist_ok=True)


# ========================================
# 📤 响应模型
# ========================================

class GridStrategyResponse(BaseModel):
    """策略响应模型"""
    id: int
    message: str
    config: GridStrategyConfig


class StrategyListResponse(BaseModel):
    """策略列表响应"""
    total: int
    strategies: List[GridStrategyConfig]


# ========================================
# 💾 数据持久化函数
# ========================================

def _get_strategy_file_path(strategy_id: int) -> str:
    """获取策略文件路径"""
    return os.path.join(STRATEGIES_DIR, f"strategy_{strategy_id}.json")


def _save_strategy(config: GridStrategyConfig) -> int:
    """
    保存策略到文件

    Returns:
        策略ID
    """
    # 生成新ID
    if config.strategy_id is None:
        # 查找最大ID
        max_id = 0
        for filename in os.listdir(STRATEGIES_DIR):
            if filename.startswith('strategy_') and filename.endswith('.json'):
                try:
                    file_id = int(filename.replace('strategy_', '').replace('.json', ''))
                    max_id = max(max_id, file_id)
                except ValueError:
                    continue
        config.strategy_id = max_id + 1

    # 保存到文件
    file_path = _get_strategy_file_path(config.strategy_id)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(config.model_dump(mode='json'), f, indent=2, ensure_ascii=False)

    logger.info(f"策略已保存 | ID: {config.strategy_id} | 文件: {file_path}")
    return config.strategy_id


def _load_strategy(strategy_id: int) -> Optional[GridStrategyConfig]:
    """从文件加载策略"""
    file_path = _get_strategy_file_path(strategy_id)

    if not os.path.exists(file_path):
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return GridStrategyConfig(**data)


def _list_all_strategies() -> List[GridStrategyConfig]:
    """列出所有策略"""
    strategies = []

    for filename in os.listdir(STRATEGIES_DIR):
        if filename.startswith('strategy_') and filename.endswith('.json'):
            try:
                strategy_id = int(filename.replace('strategy_', '').replace('.json', ''))
                strategy = _load_strategy(strategy_id)
                if strategy:
                    strategies.append(strategy)
            except Exception as e:
                logger.error(f"加载策略失败 | 文件: {filename} | 错误: {e}")

    return sorted(strategies, key=lambda s: s.strategy_id)


def _delete_strategy(strategy_id: int) -> bool:
    """删除策略"""
    file_path = _get_strategy_file_path(strategy_id)

    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"策略已删除 | ID: {strategy_id}")
        return True

    return False


# ========================================
# 🌐 API 端点
# ========================================

@router.post("/", response_model=GridStrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_grid_strategy(config: GridStrategyConfig):
    """
    创建新的网格策略配置

    - **strategy_name**: 策略名称
    - **symbol**: 交易对（如 BNB/USDT）
    - 支持所有39个配置字段

    返回创建的策略ID和配置
    """
    try:
        # 验证配置
        # Pydantic 已经自动完成验证

        # 保存策略
        strategy_id = _save_strategy(config)

        return GridStrategyResponse(
            id=strategy_id,
            message="网格策略创建成功",
            config=config
        )

    except Exception as e:
        logger.error(f"创建策略失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建策略失败: {str(e)}"
        )


@router.get("/", response_model=StrategyListResponse)
async def list_grid_strategies():
    """
    获取所有网格策略列表

    返回所有已保存的策略配置
    """
    try:
        strategies = _list_all_strategies()

        return StrategyListResponse(
            total=len(strategies),
            strategies=strategies
        )

    except Exception as e:
        logger.error(f"获取策略列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略列表失败: {str(e)}"
        )


@router.get("/{strategy_id}", response_model=GridStrategyConfig)
async def get_grid_strategy(strategy_id: int):
    """
    获取指定ID的网格策略配置

    - **strategy_id**: 策略ID

    返回策略配置详情
    """
    strategy = _load_strategy(strategy_id)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略不存在 | ID: {strategy_id}"
        )

    return strategy


@router.put("/{strategy_id}", response_model=GridStrategyResponse)
async def update_grid_strategy(strategy_id: int, config: GridStrategyConfig):
    """
    更新网格策略配置

    - **strategy_id**: 策略ID
    - 请求体包含完整的策略配置

    返回更新后的策略
    """
    # 检查策略是否存在
    existing = _load_strategy(strategy_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略不存在 | ID: {strategy_id}"
        )

    try:
        # 更新ID
        config.strategy_id = strategy_id

        # 保存策略
        _save_strategy(config)

        return GridStrategyResponse(
            id=strategy_id,
            message="策略更新成功",
            config=config
        )

    except Exception as e:
        logger.error(f"更新策略失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新策略失败: {str(e)}"
        )


@router.delete("/{strategy_id}")
async def delete_grid_strategy(strategy_id: int):
    """
    删除网格策略

    - **strategy_id**: 策略ID

    返回删除结果
    """
    success = _delete_strategy(strategy_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略不存在 | ID: {strategy_id}"
        )

    return {"message": f"策略已删除 | ID: {strategy_id}"}


@router.get("/templates/list")
async def list_strategy_templates():
    """
    获取预设策略模板列表

    返回可用的策略模板
    """
    return {
        "templates": [
            {
                "name": "conservative_grid",
                "description": "保守型网格策略",
                "suitable_for": ["BNB/USDT", "ETH/USDT"]
            },
            {
                "name": "aggressive_grid",
                "description": "激进型网格策略（不对称）",
                "suitable_for": ["ETH/USDT", "BTC/USDT"]
            }
        ]
    }


@router.post("/templates/{template_name}")
async def create_from_template(template_name: str, symbol: str = "BNB/USDT"):
    """
    从模板创建策略

    - **template_name**: 模板名称（conservative_grid/aggressive_grid）
    - **symbol**: 交易对

    返回创建的策略
    """
    try:
        if template_name == "conservative_grid":
            config = StrategyTemplates.conservative_grid(symbol)
        elif template_name == "aggressive_grid":
            config = StrategyTemplates.aggressive_grid(symbol)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模板不存在: {template_name}"
            )

        # 保存策略
        strategy_id = _save_strategy(config)

        return GridStrategyResponse(
            id=strategy_id,
            message=f"从模板 '{template_name}' 创建策略成功",
            config=config
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从模板创建策略失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"从模板创建策略失败: {str(e)}"
        )


# ========================================
# 🔌 策略状态控制（占位符，需要与 trader 集成）
# ========================================

@router.post("/{strategy_id}/start")
async def start_grid_strategy(strategy_id: int):
    """
    启动策略（占位符）

    TODO: 集成到 main.py 的 trader 启动逻辑
    """
    strategy = _load_strategy(strategy_id)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略不存在 | ID: {strategy_id}"
        )

    # TODO: 实际启动策略的逻辑
    # 这里需要与 main.py 中的 GridTrader 集成
    # 可能需要：
    # 1. 创建 GridTrader 实例
    # 2. 使用 GridTriggerEngine 和 GridOrderEngine
    # 3. 启动 main_loop

    return {
        "message": f"策略启动请求已接收 | ID: {strategy_id}",
        "note": "此功能需要与 GridTrader 集成后才能实际启动"
    }


@router.post("/{strategy_id}/stop")
async def stop_grid_strategy(strategy_id: int):
    """
    停止策略（占位符）

    TODO: 集成到 trader 停止逻辑
    """
    strategy = _load_strategy(strategy_id)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略不存在 | ID: {strategy_id}"
        )

    # TODO: 实际停止策略的逻辑

    return {
        "message": f"策略停止请求已接收 | ID: {strategy_id}",
        "note": "此功能需要与 GridTrader 集成后才能实际停止"
    }
