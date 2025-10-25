import pandas as pd
from io import BytesIO
from inventory_check import get_store_region
import streamlit as st
import hashlib
import json


def any_has_stock(products):
    """检查店铺中是否有任何产品有库存"""
    for stock in products.values():
        if stock and str(stock).isdigit() and int(stock) > 0:
            return True
    return False


def store_in_region(store_name, target_region):
    """检查店铺是否在目标区域"""
    if target_region == "全部":
        return True
    return get_store_region(store_name) == target_region


def _hash_inventory_matrix(inventory_matrix):
    """为库存矩阵生成哈希值（用于缓存）"""
    try:
        matrix_json = json.dumps(inventory_matrix, sort_keys=True, default=str)
        return hashlib.md5(matrix_json.encode()).hexdigest()
    except:
        return None


@st.cache_data(ttl=3600)
def apply_filters_and_sort(inventory_matrix_hash, stock_filter, region_filter, sort_option):
    """应用筛选和排序（缓存优化版）
    
    注意：接收库存矩阵的哈希值以便缓存，调用时使用 _hash_inventory_matrix()
    """
    # 由于接收的是哈希值，这个函数在实际调用时应该是这样的：
    # 实际应该直接在main.py中调用不缓存的版本
    # 这个设计有问题，改为使用装饰器工厂
    pass


def apply_filters_and_sort_internal(inventory_matrix, stock_filter, region_filter, sort_option):
    """应用筛选和排序的内部实现"""
    filtered_data = {}

    for store_name, products in inventory_matrix.items():
        # 库存状态筛选
        if stock_filter != "全部":
            has_stock = any_has_stock(products)
            if (stock_filter == "有库存" and not has_stock) or \
                    (stock_filter == "无库存" and has_stock):
                continue

        # 区域筛选
        if region_filter != "全部" and not store_in_region(store_name, region_filter):
            continue

        filtered_data[store_name] = products

    # 排序
    if sort_option != "默认":
        sorted_items = sorted(
            filtered_data.items(),
            key=lambda x: sum(int(stock) for stock in x[1].values() if stock and str(stock).isdigit()),
            reverse=(sort_option == "库存总量降序")
        )
        filtered_data = dict(sorted_items)

    return filtered_data


# 创建缓存版本（使用会话状态缓存）
def apply_filters_and_sort(inventory_matrix, stock_filter, region_filter, sort_option):
    """应用筛选和排序（支持会话状态缓存）"""
    # 生成缓存键
    cache_key = f"filtered_matrix_{stock_filter}_{region_filter}_{sort_option}_{_hash_inventory_matrix(inventory_matrix)}"
    
    # 检查会话状态缓存
    if "filter_cache" not in st.session_state:
        st.session_state.filter_cache = {}
    
    if cache_key in st.session_state.filter_cache:
        return st.session_state.filter_cache[cache_key]
    
    # 执行过滤和排序
    result = apply_filters_and_sort_internal(inventory_matrix, stock_filter, region_filter, sort_option)
    
    # 缓存结果
    st.session_state.filter_cache[cache_key] = result
    
    return result


@st.cache_data(ttl=3600)
def convert_to_excel(df_dict_str):
    """将DataFrame转换为Excel字节流（缓存优化版）"""
    # 从字典字符串重建DataFrame
    df_dict = json.loads(df_dict_str)
    df = pd.DataFrame.from_dict(df_dict, orient='index')
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='库存数据', index=True)
    excel_data = output.getvalue()
    return excel_data