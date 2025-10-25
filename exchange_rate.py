import requests
import json
from datetime import datetime, timedelta
import streamlit as st


def get_accurate_exchange_rate():
    """
    从银联优惠汇率接口获取韩元兑人民币准确汇率
    返回格式：{"rate": 49.63, "source": "准确值", "timestamp": "2025-10-25 14:30"}
    使用30分钟缓存
    """
    # 初始化会话状态中的缓存
    if "accurate_rate_cache" not in st.session_state:
        st.session_state.accurate_rate_cache = {
            "data": None,
            "timestamp": None
        }
    
    cache = st.session_state.accurate_rate_cache
    now = datetime.now()
    
    # 检查缓存是否有效（30分钟内）
    if cache["data"] is not None and cache["timestamp"] is not None:
        cache_time = datetime.fromisoformat(cache["timestamp"])
        if (now - cache_time).total_seconds() < 1800:  # 30分钟 = 1800秒
            return cache["data"]
    
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
                
                # 缓存结果
                cache["data"] = result
                cache["timestamp"] = now.isoformat()
                
                return result
    
    except Exception as e:
        print(f"准确汇率获取失败: {e}")
    
    # 获取失败返回None
    return None


def get_estimated_exchange_rate():
    """
    获取韩元兑人民币推测汇率（原有逻辑）
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
    获取韩元兑人民币汇率（双方案）
    优先返回准确值，失败则降级到推测值
    返回格式：{
        "rate": 49.63,
        "source": "准确值",
        "display_text": "10000韩元=49.63人民币（准确值）"
    }
    """
    # 优先尝试获取准确值
    accurate_rate = get_accurate_exchange_rate()
    if accurate_rate:
        display_text = f"10000韩元={accurate_rate['rate']}人民币（{accurate_rate['source']}）"
        return {
            "rate": accurate_rate["rate"],
            "source": accurate_rate["source"],
            "display_text": display_text
        }
    
    # 降级到推测值
    estimated_rate = get_estimated_exchange_rate()
    if estimated_rate:
        display_text = f"10000韩元={estimated_rate['rate']}人民币（{estimated_rate['source']}）"
        return {
            "rate": estimated_rate["rate"],
            "source": estimated_rate["source"],
            "display_text": display_text
        }
    
    # 都失败则返回空
    return None