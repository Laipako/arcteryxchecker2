import streamlit as st
import requests
from datetime import datetime, timedelta


class ProductCache:
    def __init__(self, ttl_minutes=30):
        self.ttl_minutes = ttl_minutes

    def fetch_and_cache_product_info(self, product_id, detail_url):
        """获取并缓存产品信息（不依赖具体解析函数）"""
        cache_key = f"product_{product_id}"

        # 检查缓存
        if not self.should_refresh_cache(cache_key):
            return st.session_state[cache_key]['data']

        # 获取HTML内容（不依赖product_detail的函数）
        html_content = self.fetch_html_from_url(detail_url)
        if not html_content:
            return None

        # 将HTML内容缓存，让product_detail.py来解析
        cache_data = {
            'html_content': html_content,
            'detail_url': detail_url,
            'timestamp': datetime.now(),
            'product_id': product_id
        }

        st.session_state[cache_key] = cache_data
        return cache_data

    def fetch_html_from_url(self, url):
        """独立的HTML获取函数"""
        import requests
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"HTML获取失败: {e}")
            return None



# 创建全局缓存实例
product_cache = ProductCache(ttl_minutes=30)  # 30分钟缓存时间