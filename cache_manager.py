import streamlit as st
import requests
from datetime import datetime, timedelta
import sys


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

    def should_refresh_cache(self, cache_key):
        """检查是否需要刷新缓存"""
        if cache_key not in st.session_state:
            return True
        
        cache_data = st.session_state[cache_key]
        if 'timestamp' not in cache_data:
            return True
        
        elapsed = datetime.now() - cache_data['timestamp']
        return elapsed.total_seconds() > (self.ttl_minutes * 60)

    def get_all_cache_items(self):
        """获取所有缓存项"""
        cache_items = []
        for key in st.session_state:
            if key.startswith('product_'):
                cache_data = st.session_state[key]
                if isinstance(cache_data, dict) and 'timestamp' in cache_data:
                    cache_items.append({
                        'key': key,
                        'product_id': cache_data.get('product_id', '未知'),
                        'timestamp': cache_data.get('timestamp', '未知'),
                        'size': self._get_object_size(cache_data)
                    })
        return cache_items

    def _get_object_size(self, obj):
        """获取对象大小（字节）"""
        return sys.getsizeof(obj)

    def get_total_cache_size(self):
        """获取总缓存大小（字节）"""
        total_size = 0
        for key in st.session_state:
            if key.startswith('product_'):
                total_size += sys.getsizeof(st.session_state[key])
        return total_size

    def clear_specific_cache(self, cache_key):
        """清除特定的缓存项"""
        if cache_key in st.session_state:
            del st.session_state[cache_key]
            return True
        return False

    def clear_all_cache(self):
        """清除所有缓存"""
        keys_to_delete = [key for key in st.session_state if key.startswith('product_')]
        for key in keys_to_delete:
            del st.session_state[key]
        return len(keys_to_delete)

    def get_cache_statistics(self):
        """获取缓存统计信息"""
        cache_items = self.get_all_cache_items()
        total_size = self.get_total_cache_size()
        
        return {
            'count': len(cache_items),
            'total_size': total_size,
            'items': cache_items,
            'ttl_minutes': self.ttl_minutes
        }


# 创建全局缓存实例
product_cache = ProductCache(ttl_minutes=30)  # 30分钟缓存时间