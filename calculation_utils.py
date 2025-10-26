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


def calculate_tax_refund(krw_amount):
    """
    计算退税额 - 基于韩国退税政策
    标准退税率为10%，但有最低消费要求
    """
    # 韩国退税的最低消费额
    MIN_PURCHASE_KRW = 40000
    
    if krw_amount < MIN_PURCHASE_KRW:
        return 0
    
    # 基础退税率为10%
    base_refund = krw_amount * 0.10
    
    # 实际退税通常考虑手续费等因素，这里简化为9%
    actual_refund = krw_amount * 0.09
    
    return int(actual_refund)


def calculate_detailed_price(total_krw, selected_discounts):
    """详细价格计算"""
    # 计算税前优惠
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

    # 计算税前优惠后价格
    after_pre_tax = total_krw - pre_tax_discount

    # 计算退税额
    tax_refund = calculate_tax_refund(after_pre_tax)

    # 计算税后价格
    after_tax = after_pre_tax - tax_refund

    # 计算税后商品券和积分
    gift_coupon = 0
    points_reward = 0
    for discount in selected_discounts:
        if discount['type'] == 'post_tax_tiered':
            for tier in reversed(discount['tiers']):  # 从高到低检查
                if after_tax >= tier['threshold']:
                    gift_coupon = tier['amount']
                    break
        elif discount['type'] == 'post_tax_tiered_points':
            for tier in reversed(discount['tiers']):  # 从高到低检查
                if after_tax >= tier['threshold']:
                    points_reward = tier['amount']
                    break

    # 计算最终实付（商品券和积分都计入）
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
