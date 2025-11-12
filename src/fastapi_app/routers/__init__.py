"""
FastAPI 路由模块
"""

from src.fastapi_app.routers import (
    auth,
    config,
    history,
    template,
    sse,
    dashboard,
    logs,
    trades,
    metrics,
)

__all__ = [
    'auth',
    'config',
    'history',
    'template',
    'sse',
    'dashboard',
    'logs',
    'trades',
    'metrics',
]
