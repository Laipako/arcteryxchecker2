import requests
import json
from datetime import datetime, timedelta
import streamlit as st


def get_exchange_rate():
    """
    获取韩元兑人民币汇率（银联优惠汇率接口）
    返回格式：10000 KRW = XX.XX CNY
    每次都从API获取最新数据，不使用缓存
    """
    try:
        url = "https://marketing.unionpayintl.com/h5Rate/rate/getRateInfoByCountryCode?insCode=101710156&channelCode=&countryCode=410&language=zh&currCode=410"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 提取汇率数据
        if data.get('responseCode') == '00' and data.get('data'):
            rate_data = data['data'][0]
            conv_rate_notice = rate_data.get('convRateNotice', [])
            
            if conv_rate_notice:
                # 获取一级优享汇率（第一个）
                discount_rate_str = conv_rate_notice[0].get('discountConvRate', '0')
                discount_rate = float(discount_rate_str)
                
                # 乘以10000得到最终汇率
                final_rate = discount_rate * 10000
                final_rate = round(final_rate, 2)
                
                # 格式化日期和时间
                current_time = datetime.now()
                display_time = current_time.strftime("%Y年%m月%d日 %H:%M")
                
                result = f"{display_time}，10000韩元={final_rate}人民币"
                
                return result
        
        return ""
    
    except Exception as e:
        print(f"汇率获取失败: {e}")
        return ""