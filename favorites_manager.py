import json
import os
from datetime import datetime
from utils import is_duplicate

FAVORITES_FILE = "data/favorites.json"


def ensure_data_directory():
    """确保数据目录存在"""
    os.makedirs(os.path.dirname(FAVORITES_FILE), exist_ok=True)


def load_favorites():
    """加载收藏列表"""
    ensure_data_directory()
    try:
        if os.path.exists(FAVORITES_FILE):
            with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    return []


def save_favorites(favorites):
    """保存收藏列表"""
    ensure_data_directory()
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)


def add_to_favorites(product_info):
    """添加产品到收藏"""
    try:
        favorites = load_favorites()

        # 检查是否重复
        if is_duplicate(favorites, product_info):
            return False, "该产品已存在于收藏中"

        # 添加时间戳
        product_info['added_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        product_info['image_url'] = product_info.get('image_url', '')  # 新增图片URL字段
        favorites.append(product_info)
        save_favorites(favorites)
        return True, "成功添加到收藏"

    except Exception as e:
        print(f"添加到收藏失败: {e}")
        return False, f"添加到收藏失败: {str(e)}"


def remove_from_favorites(index):
    """从收藏中移除产品"""
    favorites = load_favorites()
    if 0 <= index < len(favorites):
        removed_item = favorites.pop(index)
        save_favorites(favorites)
        return True, f"已移除: {removed_item['product_model']} {removed_item['color']} {removed_item['size']}"
    return False, "索引超出范围"


def clear_favorites():
    """清空收藏列表"""
    save_favorites([])
    return True, "已清空收藏列表"