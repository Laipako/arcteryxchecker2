# favorites_manager.py
import json
import os
from datetime import datetime
from utils import is_duplicate
from database import db_manager
from pymongo.errors import PyMongoError


def load_favorites():
    """从 MongoDB 加载所有收藏产品"""
    try:
        collection = db_manager.get_collection()
        favorites = list(collection.find({}).sort("added_time", -1))

        # 转换 MongoDB 的 _id 字段
        for fav in favorites:
            fav['id'] = str(fav['_id'])
            del fav['_id']

        return favorites

    except Exception as e:
        print(f"❌ 从数据库加载收藏失败: {e}")
        return []


def add_to_favorites(product_info):
    """添加产品到 MongoDB 收藏"""
    try:
        # 检查是否重复
        existing_favorites = load_favorites()
        if is_duplicate(existing_favorites, product_info):
            return False, "该产品已存在于收藏中"

        # 准备插入数据
        product_doc = {
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
            "added_time": datetime.now()
        }

        # 插入数据库
        collection = db_manager.get_collection()
        result = collection.insert_one(product_doc)

        if result.inserted_id:
            return True, "成功添加到收藏"
        else:
            return False, "添加到数据库失败"

    except Exception as e:
        print(f"❌ 添加到收藏失败: {e}")
        return False, f"添加到收藏失败: {str(e)}"


def remove_from_favorites(index):
    """根据索引从收藏中移除产品"""
    try:
        favorites = load_favorites()
        if 0 <= index < len(favorites):
            sku_to_remove = favorites[index]['sku']
            collection = db_manager.get_collection()
            result = collection.delete_one({"sku": sku_to_remove})

            if result.deleted_count > 0:
                return True, f"已从收藏中移除"
            else:
                return False, "删除失败，未找到对应记录"
        else:
            return False, "索引超出范围"

    except Exception as e:
        print(f"❌ 从收藏移除失败: {e}")
        return False, f"数据库错误: {str(e)}"


def clear_favorites():
    """清空收藏集合"""
    try:
        collection = db_manager.get_collection()
        result = collection.delete_many({})
        return True, f"已清空收藏列表，删除了 {result.deleted_count} 条记录"
    except Exception as e:
        print(f"❌ 清空收藏失败: {e}")
        return False, f"清空失败: {str(e)}"