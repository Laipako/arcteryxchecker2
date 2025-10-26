import json
import os
from datetime import datetime
from supabase_client import get_supabase
import streamlit as st

# 购买计划存储文件路径（仅作备份用）
PLANS_FILE = "plans.json"

def get_user_id():
    """获取当前用户ID"""
    try:
        # 首先检查临时用户ID（用于开发/测试）
        if "temp_user_id" in st.session_state and st.session_state.temp_user_id:
            return st.session_state.temp_user_id
        
        # 然后检查Supabase会话
        supabase = get_supabase()
        if supabase and supabase.auth.get_session():
            return supabase.auth.get_session().user.id
        
        # 如果都没有，返回默认用户ID
        return "default_user"
    except Exception as e:
        print(f"获取用户ID失败: {e}")
        return "default_user"  # 降级到默认用户ID

def load_plans():
    """
    从Supabase加载所有购买计划
    返回格式: {store_name: [{product_info}, ...], ...}
    """
    try:
        user_id = get_user_id()
        if not user_id:
            print("用户未登录，无法加载计划")
            return {}
        
        supabase = get_supabase()
        if not supabase:
            print("Supabase连接失败，尝试从本地文件加载")
            return _load_plans_from_file()
        
        # 从Supabase查询用户的所有计划
        response = supabase.table('plan').select('*').eq('user_id', user_id).execute()
        
        if response.data:
            # 转换Supabase的行数据为原来的嵌套格式
            plans = {}
            for row in response.data:
                store_name = row.get('store_name')
                if store_name not in plans:
                    plans[store_name] = []
                
                # 构建产品信息
                product_info = {
                    'product_model': row.get('product_model'),
                    'exact_model': row.get('exact_model'),
                    'color': row.get('color'),
                    'size': row.get('size'),
                    'price_krw': row.get('price_krw'),
                    'year_info': row.get('year_info'),
                    'domestic_price_cny': row.get('domestic_price_cny'),
                    'added_at': row.get('added_at'),
                    'plan_id': row.get('plan_id'),
                    'id': row.get('id')  # Supabase主键
                }
                plans[store_name].append(product_info)
            
            return plans
        else:
            return {}
            
    except Exception as e:
        print(f"从Supabase加载购买计划失败: {e}，尝试使用本地文件")
        return _load_plans_from_file()

def _load_plans_from_file():
    """从本地JSON文件加载计划（备份方案）"""
    if not os.path.exists(PLANS_FILE):
        return {}
    
    try:
        with open(PLANS_FILE, 'r', encoding='utf-8') as f:
            plans = json.load(f)
            return plans
    except Exception as e:
        print(f"从本地文件加载购买计划失败: {e}")
        return {}

def save_plans(plans):
    """
    保存购买计划到Supabase
    """
    try:
        user_id = get_user_id()
        if not user_id:
            print("用户未登录，无法保存计划")
            return False
        
        supabase = get_supabase()
        if not supabase:
            print("Supabase连接失败，仅保存到本地文件")
            try:
                with open(PLANS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(plans, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"保存本地备份失败: {e}")
            return False
        
        # 删除该用户的所有旧计划
        supabase.table('plan').delete().eq('user_id', user_id).execute()
        
        # 将新计划保存到Supabase
        for store_name, products in plans.items():
            for idx, product_info in enumerate(products, 1):
                insert_data = {
                    'user_id': user_id,
                    'store_name': store_name,
                    'product_model': product_info.get('product_model'),
                    'exact_model': product_info.get('exact_model'),
                    'color': product_info.get('color'),
                    'size': product_info.get('size'),
                    'price_krw': product_info.get('price_krw'),
                    'year_info': product_info.get('year_info'),
                    'domestic_price_cny': product_info.get('domestic_price_cny'),
                    'plan_id': product_info.get('plan_id', idx),
                    'added_at': product_info.get('added_at', datetime.now().isoformat())
                }
                supabase.table('plan').insert(insert_data).execute()
        
        # 同时保存到本地文件作为备份
        try:
            with open(PLANS_FILE, 'w', encoding='utf-8') as f:
                json.dump(plans, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存本地备份失败: {e}")
        
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
        user_id = get_user_id()
        if not user_id:
            print("用户未登录，无法添加计划")
            return False
        
        supabase = get_supabase()
        if not supabase:
            print("Supabase连接失败")
            return False
        
        product_model = product_info.get('product_model')
        color = product_info.get('color')
        size = product_info.get('size')
        
        # 检查产品是否已在任何其他店铺的计划中
        existing = supabase.table('plan').select('*').eq('user_id', user_id).neq('store_name', store_name).eq('product_model', product_model).eq('color', color).eq('size', size).execute()
        
        if existing.data:
            print(f"产品已存在于{existing.data[0].get('store_name')}的计划中，不能加入其他店铺")
            return False
        
        # 检查产品是否已存在于此店铺
        existing_in_store = supabase.table('plan').select('*').eq('user_id', user_id).eq('store_name', store_name).eq('product_model', product_model).eq('color', color).eq('size', size).execute()
        
        if existing_in_store.data:
            print(f"产品已存在于{store_name}的计划中")
            return False
        
        # 获取该店铺现有产品数量以设置plan_id
        store_products = supabase.table('plan').select('plan_id').eq('user_id', user_id).eq('store_name', store_name).execute()
        plan_id = len(store_products.data) + 1 if store_products.data else 1
        
        # 准备要插入的数据
        insert_data = {
            'user_id': user_id,
            'store_name': store_name,
            'product_model': product_model,
            'exact_model': product_info.get('exact_model'),
            'color': color,
            'size': size,
            'price_krw': product_info.get('price_krw'),
            'year_info': product_info.get('year_info'),
            'domestic_price_cny': product_info.get('domestic_price_cny'),
            'plan_id': plan_id,
            'added_at': datetime.now().isoformat()
        }
        
        # 插入到Supabase
        response = supabase.table('plan').insert(insert_data).execute()
        
        if response.data:
            print(f"成功将产品添加到{store_name}的计划中")
            
            # 同时更新本地缓存
            plans = load_plans()
            if store_name not in plans:
                plans[store_name] = []
            product_info['added_at'] = insert_data['added_at']
            product_info['plan_id'] = plan_id
            product_info['id'] = response.data[0].get('id')
            plans[store_name].append(product_info)
            save_plans(plans)
            
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
        user_id = get_user_id()
        if not user_id:
            return False, None
        
        supabase = get_supabase()
        if not supabase:
            # 回退到本地检查
            plans = _load_plans_from_file()
            for store_name, products in plans.items():
                for product in products:
                    if (product.get('product_model') == product_model and
                        product.get('color') == color and
                        product.get('size') == size):
                        return True, store_name
            return False, None
        
        response = supabase.table('plan').select('store_name').eq('user_id', user_id).eq('product_model', product_model).eq('color', color).eq('size', size).limit(1).execute()
        
        if response.data:
            return True, response.data[0].get('store_name')
        
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
        user_id = get_user_id()
        if not user_id:
            print("用户未登录")
            return False
        
        supabase = get_supabase()
        if not supabase:
            print("Supabase连接失败")
            return False
        
        # 查询要删除的产品
        response = supabase.table('plan').select('id').eq('user_id', user_id).eq('store_name', store_name).eq('product_model', product_model).eq('color', color).eq('size', size).execute()
        
        if not response.data:
            return False
        
        product_id = response.data[0].get('id')
        
        # 从Supabase删除
        delete_response = supabase.table('plan').delete().eq('id', product_id).execute()
        
        if delete_response:
            print(f"成功从{store_name}的计划中删除产品")
            
            # 同时更新本地缓存
            plans = load_plans()
            if store_name in plans:
                for i, product in enumerate(plans[store_name]):
                    if (product.get('product_model') == product_model and
                        product.get('color') == color and
                        product.get('size') == size):
                        plans[store_name].pop(i)
                        break
                
                if not plans[store_name]:
                    del plans[store_name]
                
                save_plans(plans)
            
            return True
        else:
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
        user_id = get_user_id()
        if not user_id:
            return False
        
        supabase = get_supabase()
        if not supabase:
            return False
        
        # 从Supabase删除整个店铺的记录
        response = supabase.table('plan').delete().eq('user_id', user_id).eq('store_name', store_name).execute()
        
        if response:
            print(f"成功清空{store_name}的计划")
            
            # 同时更新本地缓存
            plans = load_plans()
            if store_name in plans:
                del plans[store_name]
                save_plans(plans)
            
            return True
        
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
        product_id: 产品ID (Supabase主键或格式: "store_name_idx_timestamp")
    
    返回: True表示成功，False表示失败
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return False
        
        supabase = get_supabase()
        if not supabase:
            return False
        
        # 尝试直接用ID删除（如果是Supabase主键）
        try:
            delete_response = supabase.table('plan').delete().eq('id', product_id).eq('user_id', user_id).execute()
            if delete_response:
                print(f"成功删除产品: {product_id}")
                return True
        except:
            pass
        
        # 如果直接ID删除失败，尝试从本地缓存查找
        plans = load_plans()
        
        for store in plans.keys():
            for idx, product in enumerate(plans[store]):
                if (product.get('id') == product_id or 
                    f"{store}_{idx}_{product.get('added_at', '')}" == product_id):
                    plans[store].pop(idx)
                    
                    if not plans[store]:
                        del plans[store]
                    
                    save_plans(plans)
                    print(f"成功删除产品: {product_id}")
                    return True
        
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
        user_id = get_user_id()
        if not user_id:
            return False
        
        supabase = get_supabase()
        if not supabase:
            return False
        
        # 从Supabase删除
        response = supabase.table('plan').delete().eq('user_id', user_id).eq('store_name', store_name).execute()
        
        if response:
            print(f"成功删除店铺: {store_name}")
            
            # 同时更新本地缓存
            plans = load_plans()
            if store_name in plans:
                del plans[store_name]
                save_plans(plans)
            
            return True
        else:
            print(f"店铺不存在: {store_name}")
            return False
        
    except Exception as e:
        print(f"删除店铺失败: {e}")
        return False
