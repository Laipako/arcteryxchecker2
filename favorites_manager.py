# favorites_manager.py
import json
import os
from datetime import datetime
from utils import is_duplicate
from supabase_client import supabase_manager  # 修改：替换MongoDB导入


def load_favorites():
    """从 Supabase 加载所有收藏产品"""
    try:
        client = supabase_manager.get_client()
        response = client.table('favorites').select('*').order('added_time', desc=True).execute()

        favorites = response.data if response.data else []
        return favorites

    except Exception as e:
        print(f"❌❌ 从Supabase加载收藏失败: {e}")
        return []


def add_to_favorites(product_info):
    """添加产品到 Supabase 收藏"""
    try:
        # 检查是否重复
        existing_favorites = load_favorites()
        if is_duplicate(existing_favorites, product_info):
            return False, "该产品已存在于收藏中"

        # 准备插入数据
        product_data = {
            "product_model": product_info["product_model"],
            "exact_model": product_info["exact_model"],
            "year_info": product_info["year_info"],
            "color": product_info["color"],
            "size": product_info["size"],
            "price": product_info["price"],
            "korea_price_cny": product_info["korea_price_cny"],
            "china_price_cny": product_info["china_price_cny"],
            "discount_rate": product_info["discount_rate"],
            "sku": product_info["sku"],
            "image_url": product_info["image_url"],
            # "added_time": datetime.now().isoformat()
        }

        # 插入数据
        client = supabase_manager.get_client()
        response = client.table('favorites').insert(product_data).execute()

        if response.data:
            return True, "成功添加到收藏"
        else:
            return False, "添加到数据库失败"

    except Exception as e:
        print(f"❌❌ 添加到收藏失败: {e}")
        return False, f"添加到收藏失败: {str(e)}"


def remove_from_favorites(index):
    """根据索引从收藏中移除产品"""
    try:
        favorites = load_favorites()
        if 0 <= index < len(favorites):
            id_to_remove = favorites[index]['id']
            client = supabase_manager.get_client()
            response = client.table('favorites').delete().eq('id', id_to_remove).execute()

            if response.data:
                return True, f"已从收藏中移除"
            else:
                return False, "删除失败，未找到对应记录"
        else:
            return False, "索引超出范围"

    except Exception as e:
        print(f"❌❌ 从收藏移除失败: {e}")
        return False, f"数据库错误: {str(e)}"


def clear_favorites():
    """清空收藏表"""
    try:
        client = supabase_manager.get_client()
        response = client.table('favorites').delete().neq('id', '').execute()

        deleted_count = len(response.data) if response.data else 0
        return True, f"已清空收藏列表，删除了 {deleted_count} 条记录"
    except Exception as e:
        print(f"❌❌ 清空收藏失败: {e}")
        return False, f"清空失败: {str(e)}"