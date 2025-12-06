"""
Prometheus 指标路由

提供受保护的 API 端点和 Prometheus 抓取所需的公开端点。
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Response

from src.fastapi_app.dependencies import get_current_active_user
from src.database import User

try:
    from src.monitoring.metrics import get_metrics as get_metrics_manager
    from prometheus_client import CONTENT_TYPE_LATEST
    _metrics_import_error = None
except Exception as exc:  # pragma: no cover - 仅在缺失依赖时触发
    get_metrics_manager = None
    CONTENT_TYPE_LATEST = "text/plain"
    _metrics_import_error = exc

logger = logging.getLogger(__name__)

router = APIRouter()


def _generate_metrics_payload() -> bytes:
    """
    生成 Prometheus 指标内容

    Raises:
        HTTPException: 当 Prometheus 客户端不可用时
    """
    if not get_metrics_manager:
        detail = "Prometheus metrics backend not available"
        if _metrics_import_error:
            detail += f": {_metrics_import_error}"
        raise HTTPException(status_code=503, detail=detail)

    metrics = get_metrics_manager()
    return metrics.get_metrics()


@router.get("/metrics", summary="Prometheus 指标", include_in_schema=False)
async def secure_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """
    返回 Prometheus 指标（需要认证），便于在前端界面中查看
    """
    payload = _generate_metrics_payload()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


async def public_metrics_endpoint():
    """
    公开的 Prometheus 抓取端点（不需要认证）
    """
    payload = _generate_metrics_payload()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


__all__ = ["router", "public_metrics_endpoint"]
