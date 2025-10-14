# favorites_manager.py - 完整修改后的代码
import json
import os
from datetime import datetime
from utils import is_duplicate

# ⚠️⚠️⚠️ 修改点1：更改持久化文件路径
# 原代码：FAVORITES_FILE = "data/favorites.json"
# 新代码：使用Streamlit Cloud的持久化存储路径
PERSISTENT_FILE = "/app/streamlit-data/favorites.json"


def ensure_data_directory():
    """确保数据目录存在"""
    os.makedirs(os.path.dirname(PERSISTENT_FILE), exist_ok=True)


def load_favorites():
    """加载收藏列表"""
    ensure_data_directory()
    try:
        if os.path.exists(PERSISTENT_FILE):
            with open(PERSISTENT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"加载收藏数据失败: {e}")
    return []


def save_favorites(favorites):
    """保存收藏列表"""
    ensure_data_directory()
    try:
        with open(PERSISTENT_FILE, 'w', encoding='utf-8') as f:
            json.dump(favorites, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存收藏数据失败: {e}")
        return False


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

        # ⚠️⚠️⚠️ 修改点2：使用新的保存函数
        if save_favorites(favorites):
            return True, "成功添加到收藏"
        else:
            return False, "保存数据失败"

    except Exception as e:
        print(f"添加到收藏失败: {e}")
        return False, f"添加到收藏失败: {str(e)}"


def remove_from_favorites(index):
    """从收藏中移除产品"""
    favorites = load_favorites()
    if 0 <= index < len(favorites):
        removed_item = favorites.pop(index)
        # ⚠️⚠️⚠️ 修改点3：使用新的保存函数
        if save_favorites(favorites):
            return True, f"已移除: {removed_item['product_model']} {removed_item['color']} {removed_item['size']}"
        else:
            return False, "保存数据失败"
    return False, "索引超出范围"


def clear_favorites():
    """清空收藏列表"""
    # ⚠️⚠️⚠️ 修改点4：使用新的保存函数
    if save_favorites([]):
        return True, "已清空收藏列表"
    else:
        return False, "清空数据失败"