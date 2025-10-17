# favorites_manager.py - 完整修改版
import json
import os
from datetime import datetime
from utils import is_duplicate

# ✅ 使用相对路径，避免权限问题
PERSISTENT_FILE = "favorites.json"


def load_favorites():
    """加载收藏列表（增强容错性）"""
    try:
        if not os.path.exists(PERSISTENT_FILE):
            return []

        with open(PERSISTENT_FILE, 'r', encoding='utf-8') as f:
            favorites = json.load(f)

        # 验证数据格式
        if not isinstance(favorites, list):
            print("❌❌ 收藏数据格式错误，重置为空列表")
            return []

        # 安全修复数据
        return repair_incomplete_favorites(favorites) if favorites else []

    except Exception as e:
        print(f"❌❌ 加载收藏数据失败: {e}")
        return []  # 确保返回空列表而不是None

def save_favorites(favorites):
    """保存收藏列表"""
    try:
        with open(PERSISTENT_FILE, 'w', encoding='utf-8') as f:
            json.dump(favorites, f, ensure_ascii=False, indent=2)
        print(f"✅ 成功保存 {len(favorites)} 条收藏记录")
        return True
    except Exception as e:
        print(f"❌ 保存收藏数据失败: {e}")
        return False


# ⚠️⚠️⚠️ 修改点2：新增数据完整性修复函数
def repair_incomplete_favorites(favorites):
    """修复已保存的不完整收藏数据"""
    repaired_count = 0

    for favorite in favorites:
        if not isinstance(favorite, dict):
            continue  # 跳过无效条目
        # 修复 exact_model 字段
        if 'exact_model' not in favorite:
            favorite['exact_model'] = favorite.get('product_model', '未知型号')
            repaired_count += 1

        # 修复 year_info 字段
        if 'year_info' not in favorite:
            favorite['year_info'] = '未知年份'
            repaired_count += 1

        # 修复 china_price_cny 字段
        if 'china_price_cny' not in favorite:
            favorite['china_price_cny'] = None
            repaired_count += 1

        # 修复 image_url 字段
        if 'image_url' not in favorite:
            favorite['image_url'] = ''
            repaired_count += 1

        # 修复 discount_rate 字段
        if 'discount_rate' not in favorite:
            favorite['discount_rate'] = '暂无'
            repaired_count += 1

        # 修复 added_time 字段
        if 'added_time' not in favorite:
            favorite['added_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            repaired_count += 1

    if repaired_count > 0:
        print(f"✅ 修复了 {repaired_count} 条不完整数据")
        save_favorites(favorites)  # 保存修复后的数据

    return favorites


# ⚠️⚠️⚠️ 修改点3：增强 add_to_favorites 函数
def add_to_favorites(product_info):
    """添加产品到收藏（增强版）"""
    try:
        # 确保数据完整性
        product_info = ensure_product_info_complete(product_info)

        favorites = load_favorites()

        if is_duplicate(favorites, product_info):
            return False, "该产品已存在于收藏中"

        # 添加时间戳
        product_info['added_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        favorites.append(product_info)

        if save_favorites(favorites):
            return True, "成功添加到收藏"
        else:
            return False, "保存数据失败"

    except Exception as e:
        print(f"❌ 添加到收藏失败: {e}")
        return False, f"添加到收藏失败: {str(e)}"


# ⚠️⚠️⚠️ 修改点4：新增数据完整性验证函数
def ensure_product_info_complete(product_info):
    """确保产品信息完整"""
    required_fields = {
        'exact_model': product_info.get('product_model', '未知型号'),
        'year_info': product_info.get('year_info', '未知年份'),
        'china_price_cny': product_info.get('china_price_cny'),
        'image_url': product_info.get('image_url', ''),
        'discount_rate': product_info.get('discount_rate', '暂无'),
        'added_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    for field, default_value in required_fields.items():
        if field not in product_info:
            product_info[field] = default_value

    return product_info


# 以下函数保持不变
def remove_from_favorites(index):
    """从收藏中移除产品"""
    favorites = load_favorites()
    if 0 <= index < len(favorites):
        removed_item = favorites.pop(index)
        if save_favorites(favorites):
            return True, f"已移除: {removed_item['product_model']} {removed_item['color']} {removed_item['size']}"
        else:
            return False, "保存数据失败"
    return False, "索引超出范围"


def clear_favorites():
    """清空收藏列表"""
    if save_favorites([]):
        return True, "已清空收藏列表"
    else:
        return False, "清空数据失败"