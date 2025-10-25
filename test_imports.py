#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断脚本 - 测试所有导入
用于定位导入问题
"""

import sys
import traceback

print("=" * 60)
print("🔍 ArcTeryx Checker - 导入诊断")
print("=" * 60)
print()

# 测试基础库
basic_libs = [
    ('streamlit', 'st'),
    ('requests', 'requests'),
    ('pandas', 'pd'),
    ('lxml', 'lxml'),
    ('openpyxl', 'openpyxl'),
    ('beautifulsoup4', 'BeautifulSoup'),
    ('pymongo', 'pymongo'),
    ('dnspython', 'dns'),
    ('python-dotenv', 'dotenv'),
]

print("📦 基础库测试:")
print("-" * 60)
for lib_name, import_name in basic_libs:
    try:
        __import__(import_name)
        print(f"✅ {lib_name:20} - OK")
    except ImportError as e:
        print(f"❌ {lib_name:20} - FAILED: {e}")

print()
print("📦 特殊库测试:")
print("-" * 60)

# 测试 supabase
try:
    from supabase import create_client, Client
    print(f"✅ supabase                - OK")
except ImportError as e:
    print(f"❌ supabase                - FAILED: {e}")

print()
print("🔗 导入链测试:")
print("-" * 60)

# 测试导入链
try:
    print("正在导入 supabase_client...", end="")
    from supabase_client import get_supabase
    print(" ✅")
except Exception as e:
    print(f" ❌")
    print(f"   错误: {e}")
    traceback.print_exc()

try:
    print("正在导入 purchase_plan_manager...", end="")
    from purchase_plan_manager import add_to_plan, check_product_in_plan, load_plans
    print(" ✅")
except Exception as e:
    print(f" ❌")
    print(f"   错误: {e}")
    traceback.print_exc()

try:
    print("正在导入 plan_display...", end="")
    from plan_display import show_purchase_plan_tab
    print(" ✅")
except Exception as e:
    print(f" ❌")
    print(f"   错误: {e}")
    traceback.print_exc()

print()
print("=" * 60)
print("诊断完成！")
print("=" * 60)
