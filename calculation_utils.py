import streamlit as st
import re


def convert_krw_to_cny(krw_amount):
    """
    将韩元金额转换为人民币金额
    复用主页面显示的汇率数据
    """
    try:
        # 从主页面获取汇率信息
        if 'exchange_rate_info' in st.session_state:
            rate_str = st.session_state.exchange_rate_info
            # 从字符串中提取汇率值（如从"10000韩元=50.34人民币"提取50.34）
            match = re.search(r'10000韩元=(\d+\.?\d*)人民币', rate_str)
            if match:
                rate_per_10000 = float(match.group(1))
                cny_amount = (krw_amount / 10000) * rate_per_10000
                return int(cny_amount)  # 取整显示
    except:
        pass

    # 汇率获取失败时返回0（前端会只显示韩元）
    return 0


# 退税级进表（韩国标准）
REFUND_RATE_TABLE = [
    (15000, 1000),
    (30000, 2000),
    (50000, 3000),
    (75000, 5000),
    (100000, 7000),
    (125000, 8000),
    (150000, 9000),
    (175000, 10000),
    (200000, 12000),
    (225000, 13000),
    (250000, 15000),
    (275000, 17000),
    (300000, 19000),
    (325000, 21000),
    (350000, 23000),
    (375000, 25000),
    (400000, 27000),
    (425000, 28000),
    (450000, 30000),
    (475000, 32000),
    (500000, 35000),
    (550000, 37000),
    (600000, 41000),
    (650000, 45000),
    (700000, 50000),
    (750000, 53000),
    (800000, 57000),
    (850000, 60000),
    (900000, 65000),
    (950000, 68000),
    (1000000, 75000),
    (1100000, 80000),
    (1200000, 90000),
    (1300000, 95000),
    (1400000, 105000),
    (1500000, 110000),
    (1600000, 115000),
    (1700000, 127000),
    (1800000, 135000),
    (1900000, 140000),
    (float('inf'), 140000),  # 超过1900000保持140000
]


def calculate_tax_refund(krw_amount):
    """
    计算退税额 - 基于韩国退税级进表
    根据消费金额查表获取对应的退税额
    """
    if krw_amount < 15000:
        return 0
    
    # 查表获取退税额 - 从低到高查找满足条件的最高阈值
    refund_amount = 0
    for threshold, amount in REFUND_RATE_TABLE:
        if krw_amount >= threshold:
            refund_amount = amount
        else:
            break
    
    return refund_amount


def calculate_detailed_price(total_krw, selected_discounts):
    """详细价格计算"""
    # 第1步：计算税前优惠
    pre_tax_discount = 0
    for discount in selected_discounts:
        if discount['type'] == 'pre_tax_percent':
            pre_tax_discount += total_krw * discount['rate']
        elif discount['type'] == 'pre_tax_fixed':
            if total_krw >= discount['threshold']:
                pre_tax_discount += discount['amount']
        elif discount['type'] == 'pre_tax_capped':
            if total_krw >= discount['threshold']:
                discount_amount = total_krw * discount['rate']
                pre_tax_discount += min(discount_amount, discount['cap'])

    # 第2步：计算税前优惠后价格
    after_pre_tax = total_krw - pre_tax_discount

    # 第3步：根据税前优惠后的价格查看税后优惠（阶梯赠券和积分）
    gift_coupon = 0
    points_reward = 0
    for discount in selected_discounts:
        if discount['type'] == 'post_tax_tiered':
            for tier in reversed(discount['tiers']):  # 从高到低检查
                if after_pre_tax >= tier['threshold']:
                    gift_coupon = tier['amount']
                    break
        elif discount['type'] == 'post_tax_tiered_points':
            for tier in reversed(discount['tiers']):  # 从高到低检查
                if after_pre_tax >= tier['threshold']:
                    points_reward = tier['amount']
                    break

    # 第4步：计算退税额
    tax_refund = calculate_tax_refund(after_pre_tax)

    # 第5步：计算税后价格
    after_tax = after_pre_tax - tax_refund

    # 第6步：计算最终实付（商品券和积分都计入）
    total_post_tax_benefit = gift_coupon + points_reward
    final_payment = after_tax - total_post_tax_benefit

    return {
        'total_krw': total_krw,
        'pre_tax_discount': pre_tax_discount,
        'after_pre_tax': after_pre_tax,
        'tax_refund': tax_refund,
        'after_tax': after_tax,
        'gift_coupon': gift_coupon,
        'points_reward': points_reward,
        'final_payment': final_payment,
        'selected_discounts': [d['name'] for d in selected_discounts]
    }
