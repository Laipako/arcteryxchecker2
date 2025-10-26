import requests
import json
from urllib.parse import quote
import streamlit as st

def generate_api_url(product_model, gender="MALE", page=1, display_size=16):
    """生成API请求URL"""
    base_url = "https://api.arcteryx.co.kr/api/products/search"
    processed_model = product_model.replace(" ", "+")
    encoded_model = quote(processed_model)

    params = {
        "page": page,
        "display_size": display_size,
        "is_filter": 0,
        "search_keyword": encoded_model,
        "sort": "NEWDESC"
    }

    # 只在gender不是"BACKPACK"时添加f_gender[]参数
    if gender != "BACKPACK":
        params["f_gender[]"] = gender

    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{base_url}?{query_string}"

@st.cache_data(ttl=3600)
def extract_product_ids_from_api(api_url):
    """从API响应中提取产品ID（支持缓存）"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://arcteryx.co.kr/"
        }

        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("success") and "data" in data:
            product_ids = [str(product["product_id"]) for product in data["data"]["rows"]]
            return product_ids
        else:
            return []

    except Exception as e:
        print(f"API请求失败: {e}")
        return []