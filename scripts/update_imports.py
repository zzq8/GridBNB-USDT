#!/usr/bin/env python3
"""
自动更新所有导入路径的脚本
"""
import os
import re
from pathlib import Path

# 定义导入映射规则
IMPORT_MAPPINGS = {
    # 旧导入 -> 新导入
    r'^from config import': 'from src.config.settings import',
    r'^import config': 'import src.config.settings as config',
    r'^from exchange_client import': 'from src.core.exchange_client import',
    r'^import exchange_client': 'import src.core.exchange_client',
    r'^from trader import': 'from src.core.trader import',
    r'^import trader': 'import src.core.trader',
    r'^from order_tracker import': 'from src.core.order_tracker import',
    r'^import order_tracker': 'import src.core.order_tracker',
    r'^from position_controller_s1 import': 'from src.strategies.position_controller_s1 import',
    r'^import position_controller_s1': 'import src.strategies.position_controller_s1',
    r'^from risk_manager import': 'from src.strategies.risk_manager import',
    r'^import risk_manager': 'import src.strategies.risk_manager',
    r'^from monitor import': 'from src.services.monitor import',
    r'^import monitor': 'import src.services.monitor',
    r'^from web_server import': 'from src.services.web_server import',
    r'^import web_server': 'import src.services.web_server',
    r'^from helpers import': 'from src.utils.helpers import',
    r'^import helpers': 'import src.utils.helpers',
    r'^from api_key_manager import': 'from src.security.api_key_manager import',
    r'^import api_key_manager': 'import src.security.api_key_manager',
    r'^from api_key_validator import': 'from src.security.api_key_validator import',
    r'^import api_key_validator': 'import src.security.api_key_validator',
}

def update_imports_in_file(file_path):
    """更新单个文件中的导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        lines = content.split('\n')
        updated_lines = []

        for line in lines:
            updated_line = line
            for old_pattern, new_import in IMPORT_MAPPINGS.items():
                if re.match(old_pattern, line.strip()):
                    # 提取导入的内容
                    if 'from' in line and 'import' in line:
                        # from xxx import yyy 格式
                        match = re.search(r'from\s+\S+\s+import\s+(.+)', line)
                        if match:
                            imports = match.group(1)
                            updated_line = f"{new_import} {imports}"
                    else:
                        # import xxx 格式
                        updated_line = new_import
                    break

            updated_lines.append(updated_line)

        new_content = '\n'.join(updated_lines)

        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated: {file_path}")
            return True
        else:
            print(f"Skipped: {file_path} (no changes needed)")
            return False
    except Exception as e:
        print(f"Error {file_path}: {e}")
        return False

def main():
    """主函数"""
    base_dir = Path(__file__).parent.parent

    # 需要更新的目录
    directories = [
        base_dir / 'src',
        base_dir / 'tests',
    ]

    updated_count = 0
    total_count = 0

    for directory in directories:
        if not directory.exists():
            continue

        for py_file in directory.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            total_count += 1
            if update_imports_in_file(py_file):
                updated_count += 1

    print(f"\nSummary: Updated {updated_count}/{total_count} files")

if __name__ == '__main__':
    main()
