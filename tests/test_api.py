"""
API 集成测试脚本

测试所有新的 RESTful API endpoints。
"""

import os
import sys
import asyncio
import logging

# 设置测试环境变量（在导入其他模块之前）
os.environ['PYTEST_CURRENT_TEST'] = 'test_api.py'
os.environ['BINANCE_API_KEY'] = 'a' * 64  # 64位测试密钥
os.environ['BINANCE_API_SECRET'] = 'b' * 64  # 64位测试密钥

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import uvicorn
from aiohttp import ClientSession
from src.fastapi_app.main import create_app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class FastAPITestServer:
    """轻量级 FastAPI 测试服务器"""

    def __init__(self, host: str = '127.0.0.1', port: int = 58182):
        self.host = host
        self.port = port
        self.app = create_app(traders={})
        self.config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False,
            loop="asyncio",
        )
        self.server = uvicorn.Server(self.config)
        self.task = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()

    async def start(self):
        if self.task:
            return
        loop = asyncio.get_running_loop()
        self.task = loop.create_task(self.server.serve())
        # 等待服务器就绪
        await asyncio.sleep(0.5)

    async def stop(self):
        if self.task:
            self.server.should_exit = True
            await self.task
            self.task = None


class APITester:
    """API测试类"""

    def __init__(self, base_url: str = 'http://localhost:58182'):
        self.base_url = base_url
        self.token = None
        self.session = None

    async def __aenter__(self):
        self.session = ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def test_login(self):
        """测试1: 用户登录"""
        logger.info("\n测试 1: 用户登录")
        try:
            async with self.session.post(
                f'{self.base_url}/api/auth/login',
                json={'username': 'admin', 'password': 'admin123'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.token = data['access_token']
                    logger.info(f"✓ 登录成功: {data['user']['username']}")
                    logger.info(f"  Token: {self.token[:20]}...")
                    return True
                else:
                    logger.error(f"✗ 登录失败: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"✗ 登录异常: {e}")
            return False

    async def test_get_current_user(self):
        """测试2: 获取当前用户信息"""
        logger.info("\n测试 2: 获取当前用户信息")
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            async with self.session.get(
                f'{self.base_url}/api/auth/me',
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✓ 用户信息获取成功:")
                    logger.info(f"  用户名: {data['username']}")
                    logger.info(f"  管理员: {data['is_admin']}")
                    logger.info(f"  登录次数: {data['login_count']}")
                    return True
                else:
                    logger.error(f"✗ 获取用户信息失败: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"✗ 获取用户信息异常: {e}")
            return False

    async def test_list_configs(self):
        """测试3: 获取配置列表"""
        logger.info("\n测试 3: 获取配置列表")
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            async with self.session.get(
                f'{self.base_url}/api/configs',
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✓ 配置列表获取成功:")
                    logger.info(f"  总数: {data['total']}")
                    logger.info(f"  页面: {data['page']}")
                    logger.info(f"  每页: {data['page_size']}")
                    logger.info(f"  条目数: {len(data['items'])}")
                    return True
                else:
                    logger.error(f"✗ 获取配置列表失败: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"✗ 获取配置列表异常: {e}")
            return False

    async def test_list_templates(self):
        """测试4: 获取配置模板列表"""
        logger.info("\n测试 4: 获取配置模板列表")
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            async with self.session.get(
                f'{self.base_url}/api/templates',
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✓ 模板列表获取成功:")
                    logger.info(f"  总数: {data['total']}")
                    for template in data['items']:
                        logger.info(f"  - {template['display_name']} ({template['template_type']})")
                    return True
                else:
                    logger.error(f"✗ 获取模板列表失败: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"✗ 获取模板列表异常: {e}")
            return False

    async def test_unauthorized_access(self):
        """测试5: 未授权访问（应该失败）"""
        logger.info("\n测试 5: 未授权访问")
        try:
            # 不带token访问
            async with self.session.get(
                f'{self.base_url}/api/configs'
            ) as resp:
                if resp.status in (401, 403):
                    logger.info(f"✓ 未授权访问正确被拒绝 ({resp.status})")
                    return True
                else:
                    logger.error(f"✗ 未授权访问应返回401/403，实际: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"✗ 未授权访问测试异常: {e}")
            return False

    async def test_sse_status(self):
        """测试6: SSE连接状态"""
        logger.info("\n测试 6: SSE连接状态")
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            async with self.session.get(
                f'{self.base_url}/api/sse/status',
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✓ SSE状态获取成功:")
                    logger.info(f"  活跃连接: {data['active_connections']}")
                    return True
                else:
                    logger.error(f"✗ 获取SSE状态失败: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"✗ 获取SSE状态异常: {e}")
            return False


async def run_tests():
    """运行所有测试"""
    logger.info("\n" + "=" * 60)
    logger.info("API 集成测试")
    logger.info("=" * 60)

    results = {}

    async with FastAPITestServer():
        logger.info("✓ 测试服务器已启动在端口 58182")

        async with APITester('http://127.0.0.1:58182') as tester:
            results['login'] = await tester.test_login()
            if results['login']:
                results['current_user'] = await tester.test_get_current_user()
                results['list_configs'] = await tester.test_list_configs()
                results['list_templates'] = await tester.test_list_templates()
                results['sse_status'] = await tester.test_sse_status()
            results['unauthorized'] = await tester.test_unauthorized_access()

    logger.info("\n测试服务器已关闭")

    # 汇总结果
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{test_name:20s} {status}")

    logger.info("\n" + "-" * 60)
    logger.info(f"总计: {passed}/{total} 测试通过")
    logger.info("=" * 60 + "\n")

    return passed == total


if __name__ == '__main__':
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
