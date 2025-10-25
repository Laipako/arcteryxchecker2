import json
import os
from datetime import datetime

# 购买计划存储文件路径
PLANS_FILE = "plans.json"

def load_plans():
    """
    加载所有购买计划
    返回格式: {store_name: [{product_info}, ...], ...}
    """
    if not os.path.exists(PLANS_FILE):
        return {}
    
    try:
        with open(PLANS_FILE, 'r', encoding='utf-8') as f:
            plans = json.load(f)
            return plans
    except Exception as e:
        print(f"加载购买计划失败: {e}")
        return {}

def save_plans(plans):
    """
    保存购买计划到文件
    """
    try:
        with open(PLANS_FILE, 'w', encoding='utf-8') as f:
            json.dump(plans, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存购买计划失败: {e}")
        return False

def add_to_plan(store_name, product_info):
    """
    将产品添加到指定店铺的购买计划
    
    参数:
        store_name: 店铺名称
        product_info: 产品信息字典，包含:
            - product_model: 产品型号
            - exact_model: 精确型号
            - color: 颜色
            - size: 尺码
            - price_krw: 韩元价格
            - year_info: 年份信息
            - domestic_price_cny: 国内价格（可选）
    
    返回: True表示成功，False表示失败
    """
    try:
        plans = load_plans()
        
        # 检查产品是否已在任何其他店铺的计划中
        product_model = product_info.get('product_model')
        color = product_info.get('color')
        size = product_info.get('size')
        
        for existing_store, products in plans.items():
            if existing_store != store_name:  # 只检查其他店铺
                for item in products:
                    if (item.get('product_model') == product_model and
                        item.get('color') == color and
                        item.get('size') == size):
                        print(f"产品已存在于{existing_store}的计划中，不能加入其他店铺")
                        return False
        
        # 如果店铺不存在，创建新店铺计划
        if store_name not in plans:
            plans[store_name] = []
        
        # 检查产品是否已存在于此店铺（避免重复）
        for item in plans[store_name]:
            if (item.get('product_model') == product_model and
                item.get('color') == color and
                item.get('size') == size):
                print(f"产品已存在于{store_name}的计划中")
                return False
        
        # 添加时间戳和ID
        product_info['added_at'] = datetime.now().isoformat()
        product_info['plan_id'] = len(plans[store_name]) + 1
        
        # 添加到店铺计划
        plans[store_name].append(product_info)
        
        # 保存到文件
        if save_plans(plans):
            print(f"成功将产品添加到{store_name}的计划中")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"添加到计划失败: {e}")
        return False

def check_product_in_plan(product_model, color, size):
    """
    检查产品是否已在某个店铺的购买计划中
    
    返回: (is_in_plan, store_name)
        - is_in_plan: 布尔值，产品是否在计划中
        - store_name: 如果在计划中，返回店铺名称；否则为None
    """
    try:
        plans = load_plans()
        
        for store_name, products in plans.items():
            for product in products:
                if (product.get('product_model') == product_model and
                    product.get('color') == color and
                    product.get('size') == size):
                    return True, store_name
        
        return False, None
        
    except Exception as e:
        print(f"检查产品计划状态失败: {e}")
        return False, None

def remove_from_plan(store_name, product_model, color, size):
    """
    从购买计划中删除指定产品
    
    返回: True表示成功，False表示失败
    """
    try:
        plans = load_plans()
        
        if store_name not in plans:
            return False
        
        # 找到并删除产品
        for i, product in enumerate(plans[store_name]):
            if (product.get('product_model') == product_model and
                product.get('color') == color and
                product.get('size') == size):
                plans[store_name].pop(i)
                
                # 如果店铺计划为空，删除店铺
                if not plans[store_name]:
                    del plans[store_name]
                
                # 保存到文件
                if save_plans(plans):
                    print(f"成功从{store_name}的计划中删除产品")
                    return True
                else:
                    return False
        
        return False
        
    except Exception as e:
        print(f"删除计划产品失败: {e}")
        return False

def get_plan_by_store(store_name):
    """
    获取指定店铺的购买计划
    
    返回: 该店铺的产品列表，如果店铺不存在则返回空列表
    """
    try:
        plans = load_plans()
        return plans.get(store_name, [])
    except Exception as e:
        print(f"获取店铺计划失败: {e}")
        return []

def calculate_plan_total(store_name):
    """
    计算指定店铺计划的总价
    
    返回: (total_krw, total_cny, num_products)
    """
    try:
        products = get_plan_by_store(store_name)
        total_krw = sum(int(product.get('price_krw', 0)) for product in products)
        total_cny = sum(float(product.get('domestic_price_cny', 0) or 0) for product in products)
        
        return total_krw, total_cny, len(products)
    except Exception as e:
        print(f"计算计划总价失败: {e}")
        return 0, 0, 0

def clear_plan(store_name):
    """
    清空指定店铺的购买计划
    
    返回: True表示成功，False表示失败
    """
    try:
        plans = load_plans()
        
        if store_name in plans:
            del plans[store_name]
            return save_plans(plans)
        
        return False
        
    except Exception as e:
        print(f"清空计划失败: {e}")
        return False

# ============= 新增函数 =============

def get_plans_grouped_by_store():
    """
    获取按店铺分组的所有购买计划
    
    返回格式: {store_name: [product_info_with_id, ...], ...}
    每个产品包含添加时间戳和ID
    """
    try:
        plans = load_plans()
        result = {}
        
        for store_name, products in plans.items():
            result[store_name] = []
            for idx, product in enumerate(products):
                # 确保每个产品都有ID
                product_with_id = product.copy()
                if 'id' not in product_with_id:
                    product_with_id['id'] = f"{store_name}_{idx}_{product.get('added_at', '')}"
                result[store_name].append(product_with_id)
        
        return result
    except Exception as e:
        print(f"获取分组计划失败: {e}")
        return {}

def calculate_store_total_price(products):
    """
    计算店铺中所有产品的总价
    
    参数:
        products: 产品列表
    
    返回: 总价（韩元）
    """
    try:
        total = sum(int(product.get('price_krw', 0)) for product in products)
        return total
    except Exception as e:
        print(f"计算店铺总价失败: {e}")
        return 0

def calculate_store_domestic_total(products):
    """
    计算店铺中所有产品的国内总价
    
    参数:
        products: 产品列表
    
    返回: (total_cny, has_all_prices)
        - total_cny: 国内总价（人民币）
        - has_all_prices: 是否所有产品都有国内价格数据
    """
    try:
        total_cny = 0
        products_with_price = 0
        
        for product in products:
            domestic_price = product.get('domestic_price_cny')
            if domestic_price:
                total_cny += float(domestic_price)
                products_with_price += 1
        
        has_all_prices = (products_with_price == len(products))
        return total_cny, has_all_prices
    except Exception as e:
        print(f"计算国内总价失败: {e}")
        return 0, False

def remove_product_from_plan(product_id):
    """
    从购买计划中删除指定产品（通过ID）
    
    参数:
        product_id: 产品ID (格式: "store_name_idx_timestamp")
    
    返回: True表示成功，False表示失败
    """
    try:
        plans = load_plans()
        
        # 解析产品ID获取店铺名称
        id_parts = str(product_id).rsplit('_', 1)
        if len(id_parts) < 2:
            return False
        
        store_name = id_parts[0].rsplit('_', 1)[0] if '_' in id_parts[0] else None
        
        # 查找并删除产品
        for store in plans.keys():
            for idx, product in enumerate(plans[store]):
                # 用多种方式匹配ID以确保兼容性
                if (product.get('id') == product_id or 
                    f"{store}_{idx}_{product.get('added_at', '')}" == product_id):
                    plans[store].pop(idx)
                    
                    # 如果店铺计划为空，删除店铺
                    if not plans[store]:
                        del plans[store]
                    
                    # 保存到文件
                    if save_plans(plans):
                        print(f"成功删除产品: {product_id}")
                        return True
                    else:
                        return False
        
        print(f"未找到产品: {product_id}")
        return False
        
    except Exception as e:
        print(f"删除产品失败: {e}")
        return False

def remove_store_from_plan(store_name):
    """
    从购买计划中删除指定店铺及其所有产品
    
    参数:
        store_name: 店铺名称
    
    返回: True表示成功，False表示失败
    """
    try:
        plans = load_plans()
        
        if store_name in plans:
            del plans[store_name]
            if save_plans(plans):
                print(f"成功删除店铺: {store_name}")
                return True
            else:
                return False
        else:
            print(f"店铺不存在: {store_name}")
            return False
        
    except Exception as e:
        print(f"删除店铺失败: {e}")
        return False
