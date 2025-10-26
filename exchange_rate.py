import requests
import json
from datetime import datetime, timedelta
import streamlit as st

# 全局缓存，用于保存最后一次成功的汇率信息
_EXCHANGE_RATE_CACHE = None
_CACHE_TIMESTAMP = None
_CACHE_DURATION = 3600  # 1小时有效期


def get_accurate_exchange_rate():
    """
    从银联优惠汇率接口获取韩元兑人民币准确汇率
    返回格式：{"rate": 49.63, "source": "准确值", "timestamp": "2025-10-25 14:30"}
    禁止缓存，每次都获取最新汇率
    """
    now = datetime.now()
    
    # 请求银联API获取准确汇率
    try:
        url = "https://marketing.unionpayintl.com/h5Rate/rate/getRateInfoByCountryCode"
        params = {
            "insCode": "101710156",
            "channelCode": "",
            "countryCode": "410",
            "language": "zh",
            "currCode": "410"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 检查是否有数据
        if data.get("responseCode") == "00" and data.get("data"):
            rate_data = data.get("data", [])[0]
            
            # 提取一级优享汇率（levelInd=1）
            conv_rate_notice = rate_data.get("convRateNotice", [])
            if conv_rate_notice:
                # 获取第一个（levelInd=1）的汇率
                discount_rate = float(conv_rate_notice[0].get("discountConvRate", 0))
                
                # 乘以10000得到显示值
                display_rate = discount_rate * 10000
                display_rate = round(display_rate, 2)
                
                result = {
                    "rate": display_rate,
                    "source": "准确值",
                    "timestamp": now.isoformat()
                }
                
                return result
    
    except Exception as e:
        print(f"准确汇率获取失败: {e}")
    
    # 获取失败返回None
    return None


def get_estimated_exchange_rate():
    """
    获取韩元兑人民币推测汇率（银联历史汇率数据）
    返回格式：{"rate": 49.58, "source": "推测值", "date": "2025年10月25日"}
    """
    # 获取当前日期和前一天的日期
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    date_list = [
        today.strftime("%Y%m%d"),
        yesterday.strftime("%Y%m%d")
    ]

    for date_str in date_list:
        try:
            url = f"https://www.unionpayintl.com/upload/jfimg/{date_str}.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 使用正确的键名 exchangeRateJson
            for rate in data.get('exchangeRateJson', []):
                if rate.get('transCur') == 'KRW' and rate.get('baseCur') == 'CNY':
                    krw_to_cny = float(rate.get('rateData', 0))

                    # 计算推测汇率（原逻辑：减去0.05的推导）
                    normal_rate = 10000 * krw_to_cny
                    discount_rate = normal_rate - 0.05
                    discount_rate = round(discount_rate, 2)

                    # 格式化日期
                    display_date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y年%m月%d日")
                    
                    result = {
                        "rate": discount_rate,
                        "source": "推测值",
                        "date": display_date
                    }
                    
                    return result

        except Exception as e:
            print(f"推测汇率获取失败 {date_str}: {e}")
            continue

    return None


def get_exchange_rate():
    """
    获取韩元兑人民币汇率（包含缓存机制）
    
    缓存策略：
    - 第一次成功获取后保存在内存中
    - 1小时内重复调用直接返回缓存值
    - 超过1小时或API失败时重新获取
    - 如果新获取失败但缓存仍有效，返回缓存值
    
    流程：
    1. 检查缓存是否有效 → 有效则直接返回
    2. 优先尝试获取准确值（银联API） → 成功则缓存并返回
    3. 降级到推测值（银联历史数据） → 成功则缓存并返回
    4. 若新获取都失败但缓存仍有效 → 返回缓存值
    5. 若都失败且无缓存 → 返回None
    
    返回格式：{
        "rate": 49.63,
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
        print(f"✅ 返回缓存汇率: {_EXCHANGE_RATE_CACHE['display_text']}")
        return _EXCHANGE_RATE_CACHE
    
    try:
        # 优先尝试获取准确值
        accurate_rate = get_accurate_exchange_rate()
        if accurate_rate:
            display_text = f"10000韩元={accurate_rate['rate']}人民币（{accurate_rate['source']}）"
            rate_data = {
                "rate": accurate_rate["rate"],
                "source": accurate_rate["source"],
                "display_text": display_text
            }
            # 保存到缓存
            _EXCHANGE_RATE_CACHE = rate_data
            _CACHE_TIMESTAMP = current_time
            print(f"✅ 汇率获取成功（准确值）: {display_text}")
            return rate_data
        
        print("⚠️  银联准确值获取失败，尝试推测值...")
        
        # 降级到推测值
        estimated_rate = get_estimated_exchange_rate()
        if estimated_rate:
            display_text = f"10000韩元={estimated_rate['rate']}人民币（{estimated_rate['source']}）"
            rate_data = {
                "rate": estimated_rate["rate"],
                "source": estimated_rate["source"],
                "display_text": display_text
            }
            # 保存到缓存
            _EXCHANGE_RATE_CACHE = rate_data
            _CACHE_TIMESTAMP = current_time
            print(f"✅ 汇率获取成功（推测值）: {display_text}")
            return rate_data
        
        # 准确值和推测值都失败，但缓存仍有效时返回缓存
        if _EXCHANGE_RATE_CACHE is not None:
            print(f"⚠️  所有方式都失败，返回缓存值: {_EXCHANGE_RATE_CACHE['display_text']}")
            return _EXCHANGE_RATE_CACHE
        
        # 如果都失败且无缓存，返回None
        print("❌ 无法获取汇率信息，且无有效缓存")
        return None
        
    except Exception as e:
        print(f"获取汇率异常: {e}")
        import traceback
        traceback.print_exc()
        # 异常时优先返回有效缓存
        if _EXCHANGE_RATE_CACHE is not None:
            print(f"⚠️  异常捕获，返回缓存值: {_EXCHANGE_RATE_CACHE['display_text']}")
            return _EXCHANGE_RATE_CACHE
        return None


def clear_exchange_rate_cache():
    """
    清空汇率缓存（手动刷新汇率时调用）
    """
    global _EXCHANGE_RATE_CACHE, _CACHE_TIMESTAMP
    _EXCHANGE_RATE_CACHE = None
    _CACHE_TIMESTAMP = None
    print("✅ 汇率缓存已清空")