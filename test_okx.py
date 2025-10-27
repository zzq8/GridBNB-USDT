"""
OKX交易所连接测试脚本

用于验证OKX配置是否正确，以及API连接是否正常
"""
import asyncio
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.exchange_client import ExchangeClient
from src.config.settings import settings


async def test_okx_connection():
    """测试OKX交易所连接"""

    print("=" * 60)
    print("OKX交易所连接测试")
    print("=" * 60)

    # 1. 检查配置
    print("\n【步骤1】检查配置...")
    print(f"当前配置的交易所: {settings.EXCHANGE}")

    if settings.EXCHANGE.lower() != 'okx':
        print("❌ 错误: 当前配置的交易所不是OKX")
        print(f"   请在.env文件中设置: EXCHANGE=okx")
        return False

    print("✅ 交易所配置正确")

    # 检查API密钥
    if not settings.OKX_API_KEY or len(settings.OKX_API_KEY) < 10:
        print("❌ 错误: OKX_API_KEY未配置或格式错误")
        return False

    if not settings.OKX_API_SECRET or len(settings.OKX_API_SECRET) < 10:
        print("❌ 错误: OKX_API_SECRET未配置或格式错误")
        return False

    if not settings.OKX_PASSPHRASE:
        print("❌ 错误: OKX_PASSPHRASE未配置（OKX必需参数）")
        return False

    print(f"✅ API密钥已配置 (API Key前10位: {settings.OKX_API_KEY[:10]}...)")
    print(f"✅ API密钥密码已配置")
    print(f"✅ Passphrase已配置")

    # 2. 创建客户端
    print("\n【步骤2】创建ExchangeClient实例...")
    try:
        client = ExchangeClient()
        print(f"✅ 客户端创建成功，交易所类型: {client.exchange_name}")
    except Exception as e:
        print(f"❌ 客户端创建失败: {e}")
        return False

    # 3. 测试加载市场数据
    print("\n【步骤3】测试加载市场数据...")
    try:
        await client.load_markets()
        print(f"✅ 市场数据加载成功")
    except Exception as e:
        print(f"❌ 市场数据加载失败: {e}")
        await client.close()
        return False

    # 4. 测试获取行情
    print("\n【步骤4】测试获取行情数据...")
    try:
        test_symbol = "BNB/USDT"
        ticker = await client.fetch_ticker(test_symbol)
        print(f"✅ 行情获取成功")
        print(f"   交易对: {test_symbol}")
        print(f"   最新价格: {ticker['last']} USDT")
        print(f"   24h最高: {ticker.get('high', 'N/A')}")
        print(f"   24h最低: {ticker.get('low', 'N/A')}")
        print(f"   24h成交量: {ticker.get('volume', 'N/A')}")
    except Exception as e:
        print(f"❌ 行情获取失败: {e}")
        await client.close()
        return False

    # 5. 测试获取账户余额
    print("\n【步骤5】测试获取账户余额...")
    try:
        balance = await client.fetch_balance()
        print(f"✅ 余额获取成功")

        # 显示有余额的资产
        assets_with_balance = {k: v for k, v in balance.get('total', {}).items()
                               if float(v) > 0}

        if assets_with_balance:
            print(f"   账户中有余额的资产 ({len(assets_with_balance)}种):")
            for asset, amount in sorted(assets_with_balance.items(),
                                       key=lambda x: float(x[1]), reverse=True)[:5]:
                print(f"     - {asset}: {amount}")
            if len(assets_with_balance) > 5:
                print(f"     ... 还有 {len(assets_with_balance) - 5} 种资产")
        else:
            print("   ⚠️ 账户中暂无资产")
    except Exception as e:
        print(f"❌ 余额获取失败: {e}")
        await client.close()
        return False

    # 6. 测试获取理财账户余额（如果启用）
    if settings.ENABLE_SAVINGS_FUNCTION:
        print("\n【步骤6】测试获取理财账户余额...")
        try:
            funding_balance = await client.fetch_funding_balance()
            print(f"✅ 理财余额获取成功")

            if funding_balance:
                print(f"   理财账户中有余额的资产 ({len(funding_balance)}种):")
                for asset, amount in sorted(funding_balance.items(),
                                           key=lambda x: float(x[1]), reverse=True)[:5]:
                    print(f"     - {asset}: {amount}")
            else:
                print("   理财账户暂无资产")
        except Exception as e:
            print(f"⚠️ 理财余额获取失败（可能OKX资金账户为空）: {e}")

    # 7. 关闭连接
    print("\n【步骤7】关闭连接...")
    await client.close()
    print("✅ 连接已关闭")

    # 测试成功
    print("\n" + "=" * 60)
    print("🎉 OKX交易所连接测试全部通过！")
    print("=" * 60)
    print("\n下一步：")
    print("1. 确认.env中的交易对配置正确 (SYMBOLS)")
    print("2. 运行主程序: python src/main.py")
    print("3. 访问Web监控界面查看运行状态")

    return True


async def main():
    """主函数"""
    try:
        success = await test_okx_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生未预期的错误:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\n正在启动OKX连接测试...\n")
    asyncio.run(main())
