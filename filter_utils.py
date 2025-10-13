import pandas as pd
from io import BytesIO
from inventory_check import get_store_region


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


def apply_filters_and_sort(inventory_matrix, stock_filter, region_filter, sort_option):
    """应用筛选和排序"""
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


def convert_to_excel(df):
    """将DataFrame转换为Excel字节流"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='库存数据', index=True)
    excel_data = output.getvalue()
    return excel_data