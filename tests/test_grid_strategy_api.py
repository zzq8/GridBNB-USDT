"""
网格策略 API 集成测试

验证网格策略路由是否正确注册到 FastAPI 应用中
"""

import pytest
from fastapi.testclient import TestClient
from src.fastapi_app.main import create_app


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app()
    return TestClient(app)


class TestGridStrategyAPIIntegration:
    """网格策略 API 集成测试"""

    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "GridBNB" in data["service"]

    def test_get_strategies_empty(self, client):
        """测试获取策略列表（空）"""
        response = client.get("/api/grid-strategies/")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "strategies" in data
        assert isinstance(data["strategies"], list)

    def test_get_templates_list(self, client):
        """测试获取模板列表"""
        response = client.get("/api/grid-strategies/templates/list")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        templates = data["templates"]
        assert len(templates) >= 2  # 至少有保守型和激进型

        # 验证模板结构
        template_names = [t["name"] for t in templates]
        assert "conservative_grid" in template_names
        assert "aggressive_grid" in template_names

    def test_create_strategy_from_template(self, client):
        """测试从模板创建策略"""
        response = client.post(
            "/api/grid-strategies/templates/conservative_grid",
            params={"symbol": "BNB/USDT"}
        )
        assert response.status_code in [200, 201]  # 接受200或201
        data = response.json()
        assert data["id"] > 0
        assert "message" in data
        assert "conservative_grid" in data["message"] or "成功" in data["message"]
        assert data["config"]["symbol"] == "BNB/USDT"

        # 保存策略ID供后续测试使用
        return data["id"]

    def test_create_custom_strategy(self, client):
        """测试创建自定义策略"""
        strategy_data = {
            "strategy_name": "测试策略",
            "symbol": "ETH/USDT",
            "base_currency": "ETH",
            "quote_currency": "USDT",
            "grid_type": "percent",
            "trigger_base_price_type": "current",
            "rise_sell_percent": 2.0,
            "fall_buy_percent": 2.0,
            "order_type": "limit",
            "buy_price_mode": "bid1",
            "sell_price_mode": "ask1",
            "amount_mode": "percent",
            "grid_symmetric": True,
            "order_quantity": 15.0
        }

        response = client.post("/api/grid-strategies/", json=strategy_data)
        assert response.status_code in [200, 201]  # 接受200或201
        data = response.json()
        assert data["id"] > 0
        assert data["config"]["strategy_name"] == "测试策略"
        assert data["config"]["rise_sell_percent"] == 2.0

    def test_get_strategy_by_id(self, client):
        """测试根据ID获取策略"""
        # 先创建一个策略
        create_response = client.post(
            "/api/grid-strategies/templates/conservative_grid",
            params={"symbol": "BNB/USDT"}
        )
        strategy_id = create_response.json()["id"]

        # 获取策略详情
        response = client.get(f"/api/grid-strategies/{strategy_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["strategy_id"] == strategy_id
        assert data["symbol"] == "BNB/USDT"

    def test_get_nonexistent_strategy(self, client):
        """测试获取不存在的策略"""
        response = client.get("/api/grid-strategies/99999")
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

    def test_update_strategy(self, client):
        """测试更新策略"""
        # 先创建一个完整的策略
        create_data = {
            "strategy_name": "待更新策略",
            "symbol": "BNB/USDT",
            "base_currency": "BNB",
            "quote_currency": "USDT",
            "grid_type": "percent",
            "trigger_base_price_type": "current",
            "rise_sell_percent": 1.5,
            "fall_buy_percent": 1.5,
            "order_type": "limit",
            "buy_price_mode": "bid1",
            "sell_price_mode": "ask1",
            "amount_mode": "percent",
            "grid_symmetric": True,
            "order_quantity": 10.0
        }
        create_response = client.post("/api/grid-strategies/", json=create_data)
        strategy_id = create_response.json()["id"]

        # 更新策略（使用完整配置）
        update_data = create_data.copy()
        update_data["rise_sell_percent"] = 3.0
        update_data["fall_buy_percent"] = 3.0

        response = client.put(f"/api/grid-strategies/{strategy_id}", json=update_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["config"]["rise_sell_percent"] == 3.0
        assert data["config"]["fall_buy_percent"] == 3.0

    def test_delete_strategy(self, client):
        """测试删除策略"""
        # 先创建一个策略
        create_response = client.post(
            "/api/grid-strategies/templates/conservative_grid",
            params={"symbol": "BNB/USDT"}
        )
        strategy_id = create_response.json()["id"]

        # 删除策略
        response = client.delete(f"/api/grid-strategies/{strategy_id}")
        assert response.status_code in [200, 204]  # 接受200或204

        # 验证删除响应
        if response.status_code == 200:
            data = response.json()
            assert "message" in data or "id" in data

        # 验证策略已删除
        get_response = client.get(f"/api/grid-strategies/{strategy_id}")
        assert get_response.status_code == 404

    def test_api_documentation_accessible(self, client):
        """测试 API 文档是否可访问"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert b"swagger" in response.content.lower()

    def test_create_strategy_validation_error(self, client):
        """测试创建策略时的验证错误"""
        # 缺少必需字段
        invalid_data = {
            "strategy_name": "无效策略",
            # 缺少 symbol, base_currency, quote_currency
        }

        response = client.post("/api/grid-strategies/", json=invalid_data)
        assert response.status_code == 422  # Validation Error
        data = response.json()
        assert "detail" in data

    def test_create_from_nonexistent_template(self, client):
        """测试从不存在的模板创建策略"""
        response = client.post(
            "/api/grid-strategies/templates/nonexistent_template",
            params={"symbol": "BNB/USDT"}
        )
        assert response.status_code in [400, 404]  # 接受400或404
        data = response.json()
        assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
