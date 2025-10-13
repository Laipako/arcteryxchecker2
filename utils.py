import re

def standardize_model_name(model_name):
    """标准化产品型号名称"""
    if not model_name:
        return ""
    # 转换为小写并移除多余空格
    return re.sub(r'\s+', ' ', model_name.strip().lower())

def is_duplicate(favorites, new_item):
    """检查是否重复收藏"""
    for item in favorites:
        if (standardize_model_name(item['product_model']) == standardize_model_name(new_item['product_model']) and
            item['color'] == new_item['color'] and
            item['size'] == new_item['size']):
            return True
    return False

def is_duplicate(favorites, new_item):
    """检查是否重复收藏（更新逻辑）"""
    for item in favorites:
        if (standardize_model_name(item['product_model']) == standardize_model_name(new_item['product_model']) and
            item['color'] == new_item['color'] and
            item['size'] == new_item['size']):
            return True
    return False