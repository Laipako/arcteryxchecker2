import requests
import re
from datetime import datetime, timedelta
import streamlit as st

# 全局缓存，用于保存最后一次成功的汇率信息
_EXCHANGE_RATE_CACHE = None
_CACHE_TIMESTAMP = None
_CACHE_DURATION = 3600  # 1小时有效期

def get_exchange_rate():
    """
    获取实时汇率信息，包含缓存机制
    
    缓存策略：
    - 第一次成功获取后保存在内存中
    - 1小时内重复调用直接返回缓存值
    - 超过1小时或API失败时重新获取
    - 如果新获取失败但缓存仍有效，返回缓存值
    
    返回格式：
    {
        "rate": 49.63,  # float类型，精确到小数点后2位
        "source": "准确值"/"推测值",
        "display_text": "10000韩元=49.63人民币（准确值）"
    }
    """
    global _EXCHANGE_RATE_CACHE, _CACHE_TIMESTAMP
    
    current_time = datetime.now()
    
    # 检查缓存是否有效
    if (_EXCHANGE_RATE_CACHE is not None and 
        _CACHE_TIMESTAMP is not None and 
        (current_time - _CACHE_TIMESTAMP).total_seconds() < _CACHE_DURATION):
        return _EXCHANGE_RATE_CACHE
    
    try:
        # 尝试获取准确汇率
        accurate_rate = get_accurate_exchange_rate()
        
        if accurate_rate:
            rate_data = {
                "rate": accurate_rate["rate"],
                "source": accurate_rate["source"],
                "display_text": f"10000韩元={accurate_rate['rate']}人民币（{accurate_rate['source']}）"
            }
            # 保存到缓存
            _EXCHANGE_RATE_CACHE = rate_data
            _CACHE_TIMESTAMP = current_time
            return rate_data
        
        # 如果准确汇率获取失败，尝试推测值
        estimated_rate = get_estimated_exchange_rate()
        
        if estimated_rate:
            rate_data = {
                "rate": estimated_rate["rate"],
                "source": estimated_rate["source"],
                "display_text": f"10000韩元={estimated_rate['rate']}人民币（{estimated_rate['source']}）"
            }
            # 保存到缓存
            _EXCHANGE_RATE_CACHE = rate_data
            _CACHE_TIMESTAMP = current_time
            return rate_data
        
        # 两种方式都失败，但缓存仍有效时返回缓存
        if _EXCHANGE_RATE_CACHE is not None:
            return _EXCHANGE_RATE_CACHE
        
        # 如果都失败且无缓存，返回None
        return None
        
    except Exception as e:
        print(f"获取汇率异常: {e}")
        # 异常时优先返回有效缓存
        if _EXCHANGE_RATE_CACHE is not None:
            return _EXCHANGE_RATE_CACHE
        return None


def get_accurate_exchange_rate():
    """
    从Naver获取准确汇率信息
    """
    try:
        url = "https://search.naver.com/search.naver?query=1000+krw+cny"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)  # 增加超时保护
        response.encoding = "utf-8"
        
        # 从HTML中提取汇率
        match = re.search(r'class="sub_number">([0-9.]+)\s*(?:人民币)?', response.text)
        
        if match:
            rate_str = match.group(1)
            rate = float(rate_str)
            return {
                "rate": round(rate, 2),
                "source": "准确值"
            }
        
        return None
        
    except requests.Timeout:
        print("Naver汇率获取超时（5秒）")
        return None
    except Exception as e:
        print(f"Naver汇率获取失败: {e}")
        return None


def get_estimated_exchange_rate():
    """
    从Google搜索结果中获取推测汇率（备选方案）
    """
    try:
        url = "https://www.google.com/search?q=1000+krw+to+cny"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)  # 增加超时保护
        response.encoding = "utf-8"
        
        # 从Google结果中提取汇率（Google通常显示类似 "X CNY" 的结果）
        match = re.search(r'(?:≈|=)\s*([0-9.]+)\s*(?:CNY|人民币)', response.text)
        
        if match:
            rate_str = match.group(1)
            rate = float(rate_str)
            return {
                "rate": round(rate, 2),
                "source": "推测值"
            }
        
        return None
        
    except requests.Timeout:
        print("Google汇率获取超时（5秒）")
        return None
    except Exception as e:
        print(f"Google汇率获取失败: {e}")
        return None


def clear_exchange_rate_cache():
    """
    清空汇率缓存（手动刷新汇率时调用）
    """
    global _EXCHANGE_RATE_CACHE, _CACHE_TIMESTAMP
    _EXCHANGE_RATE_CACHE = None
    _CACHE_TIMESTAMP = None