import streamlit as st
from supabase_client import get_supabase

def load_plans():
    """从Supabase加载所有购买计划"""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
        response = supabase.table("plan").select("*").execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"加载购买计划失败: {e}")
        return []


def add_to_plan(store_name: str, product_info: dict) -> bool:
    """
    添加产品到购买计划
    product_info 应包含: product_model, exact_model, color, size, price_krw, year_info, domestic_price_cny(可选)
    """
    try:
        supabase = get_supabase()
        if not supabase:
            st.error("Supabase 连接不可用")
            return False
        # 检查是否已存在该产品在该店铺
        existing = supabase.table("plan").select("*").eq(
            "store_name", store_name
        ).eq("product_model", product_info["product_model"]).eq(
            "color", product_info["color"]
        ).eq("size", product_info["size"]).execute()
        
        if existing.data:
            st.warning(f"该产品已在 {store_name} 的购买计划中")
            return False
        
        # 获取国内价格（从product_info传入或为None）
        domestic_price_cny = product_info.get("domestic_price_cny", None)
        
        # 添加到购买计划
        plan_data = {
            "store_name": store_name,
            "product_model": product_info["product_model"],
            "exact_model": product_info.get("exact_model", ""),
            "color": product_info["color"],
            "size": product_info["size"],
            "price_krw": int(product_info["price_krw"]),
            "year_info": product_info.get("year_info", ""),
            "domestic_price_cny": domestic_price_cny
        }
        
        supabase.table("plan").insert(plan_data).execute()
        st.success(f"已将 {product_info['product_model']} {product_info['color']} {product_info['size']} 加入 {store_name} 的购买计划")
        return True
    except Exception as e:
        st.error(f"添加到购买计划失败: {e}")
        return False


def remove_product_from_plan(plan_id: int) -> bool:
    """从购买计划中删除单个产品"""
    try:
        supabase = get_supabase()
        if not supabase:
            st.error("Supabase 连接不可用")
            return False
        supabase.table("plan").delete().eq("id", plan_id).execute()
        return True
    except Exception as e:
        st.error(f"删除产品失败: {e}")
        return False


def remove_store_from_plan(store_name: str) -> bool:
    """删除购买计划中的整个店铺及其所有产品"""
    try:
        supabase = get_supabase()
        if not supabase:
            st.error("Supabase 连接不可用")
            return False
        supabase.table("plan").delete().eq("store_name", store_name).execute()
        return True
    except Exception as e:
        st.error(f"删除店铺失败: {e}")
        return False


def get_plans_grouped_by_store() -> dict:
    """
    获取购买计划，按店铺分组
    返回格式: {店铺名: [产品1, 产品2, ...]}
    """
    plans = load_plans()
    grouped = {}
    
    for plan in plans:
        store = plan["store_name"]
        if store not in grouped:
            grouped[store] = []
        grouped[store].append(plan)
    
    # 按店铺名称排序（按字母顺序）
    return dict(sorted(grouped.items()))


def calculate_store_total_price(products: list) -> int:
    """计算店铺下所有产品的税前总价"""
    return sum(product["price_krw"] for product in products)


def calculate_store_domestic_total(products: list) -> tuple:
    """
    计算店铺下所有产品的国内价格总额
    返回: (国内价格总额, 是否所有产品都有国内价格)
    """
    total_domestic_price = 0
    has_all_prices = True
    
    for product in products:
        domestic_price = product.get("domestic_price_cny")
        if not domestic_price or float(domestic_price) <= 0:
            has_all_prices = False
            break
        total_domestic_price += float(domestic_price)
    
    return (total_domestic_price if has_all_prices else 0, has_all_prices)


def check_product_in_plan(product_model: str, color: str, size: str) -> tuple:
    """
    检查产品是否已在购买计划中
    返回: (是否存在, 店铺名称 或 None)
    """
    try:
        plans = load_plans()
        for plan in plans:
            if (plan["product_model"] == product_model and 
                plan["color"] == color and 
                plan["size"] == size):
                return (True, plan["store_name"])
        return (False, None)
    except Exception as e:
        st.error(f"检查购买计划失败: {e}")
        return (False, None)
