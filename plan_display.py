import streamlit as st

try:
    from purchase_plan_manager import (
        get_plans_grouped_by_store,
        calculate_store_total_price,
        remove_product_from_plan,
        remove_store_from_plan,
        calculate_store_domestic_total
    )
except Exception as e:
    error_msg = f"Warning: Failed to import purchase_plan_manager: {e}"
    print(error_msg)
    # 提供备用空函数
    def get_plans_grouped_by_store(): return {}
    def calculate_store_total_price(products): return 0
    def remove_product_from_plan(plan_id): return False
    def remove_store_from_plan(store_name): return False
    def calculate_store_domestic_total(products): return (0, False)


def show_purchase_plan_tab():
    """显示购买计划标签页"""
    st.header("购买计划")
    
    # 初始化session_state
    if "plan_refreshed" not in st.session_state:
        st.session_state.plan_refreshed = False
    
    # 初始化试算相关状态
    if "show_plan_calculation_config" not in st.session_state:
        st.session_state.show_plan_calculation_config = {}
    if "plan_calculation_result" not in st.session_state:
        st.session_state.plan_calculation_result = {}
    
    # 获取购买计划数据
    plans_by_store = get_plans_grouped_by_store()
    
    if not plans_by_store:
        st.info("暂无购买计划")
        return
    
    # 遍历每个店铺
    for store_name in plans_by_store.keys():
        products = plans_by_store[store_name]
        total_price = calculate_store_total_price(products)
        
        # 店铺标题区域
        st.subheader(f"{store_name}")
        
        # 创建容器用于产品列表
        with st.container(border=True):
            # 显示每个产品
            for idx, product in enumerate(products):
                col1, col2, col3, col4 = st.columns([3, 1, 0.8, 0.8], gap="small")
                
                with col1:
                    # 产品信息
                    product_display = f"{product['exact_model'] or product['product_model']} {product['color']} {product['size']}"
                    st.write(product_display)
                
                with col2:
                    # 价格
                    price_display = f"{product['price_krw']:,}韩元"
                    st.write(price_display)
                
                with col3:
                    # 删除按钮
                    if st.button("删除", key=f"delete_product_{product['id']}", help="删除该产品"):
                        if remove_product_from_plan(product['id']):
                            st.success("已删除")
                            # 清除所有计划缓存，使收藏列表能正确刷新
                            keys_to_delete = [k for k in st.session_state.keys() if k.startswith("plan_check_")]
                            for key in keys_to_delete:
                                del st.session_state[key]
                            st.rerun()
                
                with col4:
                    st.empty()  # 占位符保持对齐
            
            # 分割线
            st.divider()
            
            # 税前总价
            col1, col2, col3 = st.columns([3, 1, 0.8], gap="small")
            with col1:
                st.write("**税前总价**")
            with col2:
                st.write(f"**{total_price:,}韩元**")
            with col3:
                st.empty()
        
        # 删除店铺和试算按钮区域
        col1, col2, col3, col4 = st.columns([3, 1, 1, 0.8], gap="small")
        
        with col2:
            # 试算按钮
            if st.button("试算", key=f"calc_plan_{store_name}"):
                st.session_state.show_plan_calculation_config[store_name] = True
                st.session_state.plan_calculation_result[store_name] = None
                st.rerun()
        
        with col3:
            # 删除店铺按钮
            if st.button("删除店铺", key=f"delete_store_{store_name}"):
                # 显示确认对话框
                if st.session_state.get(f"confirm_delete_{store_name}", False):
                    if remove_store_from_plan(store_name):
                        st.success(f"已删除 {store_name} 及其所有产品")
                        st.session_state[f"confirm_delete_{store_name}"] = False
                        # 清除所有计划缓存，使收藏列表能正确刷新
                        keys_to_delete = [k for k in st.session_state.keys() if k.startswith("plan_check_")]
                        for key in keys_to_delete:
                            del st.session_state[key]
                        st.rerun()
                else:
                    st.session_state[f"confirm_delete_{store_name}"] = True
                    st.rerun()
        
        # 显示删除确认
        if st.session_state.get(f"confirm_delete_{store_name}", False):
            with col1:
                st.warning(f"确认删除 {store_name} 下的所有产品吗？")
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("确认删除", key=f"confirm_delete_btn_{store_name}"):
                    if remove_store_from_plan(store_name):
                        st.success(f"已删除 {store_name} 及其所有产品")
                        st.session_state[f"confirm_delete_{store_name}"] = False
                        # 清除所有计划缓存，使收藏列表能正确刷新
                        keys_to_delete = [k for k in st.session_state.keys() if k.startswith("plan_check_")]
                        for key in keys_to_delete:
                            del st.session_state[key]
                        st.rerun()
            with col_cancel:
                if st.button("取消", key=f"cancel_delete_btn_{store_name}"):
                    st.session_state[f"confirm_delete_{store_name}"] = False
                    st.rerun()
        
        # 显示试算配置窗口
        if st.session_state.show_plan_calculation_config.get(store_name, False):
            show_store_calculation_config(store_name, products)
            continue
        
        # 显示试算结果
        if st.session_state.plan_calculation_result.get(store_name):
            with st.expander(f"{store_name} 试算结果", expanded=True):
                col_close, _ = st.columns([1, 3])
                with col_close:
                    if st.button(f"关闭试算", key=f"close_calc_{store_name}"):
                        st.session_state.plan_calculation_result[store_name] = None
                        st.rerun()
                
                display_store_calculation_results(store_name, products, st.session_state.plan_calculation_result[store_name])
        
        st.write("")  # 间距


def show_store_calculation_config(store_name: str, products: list):
    """显示店铺购买计划的试算配置窗口"""
    from discount_config import DISCOUNT_CONFIG
    
    st.subheader(f"{store_name} 试算配置")
    
    # 显示选中的产品清单
    st.write("**产品清单:**")
    for i, product in enumerate(products, 1):
        st.write(f"{i}. {product['exact_model'] or product['product_model']} - {product['color']} - {product['size']} - {product['price_krw']:,}韩元")
    
    # 计算原始总价
    total_krw = sum(product['price_krw'] for product in products)
    st.write(f"**税前总价:** {total_krw:,}韩元")
    
    st.divider()
    
    # 商家选择（单选）
    st.write("**选择商家优惠:**")
    store_options = ["明洞乐天", "新世界", "韩国电话注册", "乐天/新世界奥莱", "现代百货"]
    selected_store = st.radio("商家选择", store_options, key=f"store_selection_{store_name}", label_visibility="collapsed")
    
    # 显示对应商家的优惠选项
    store_config = DISCOUNT_CONFIG[selected_store]
    st.write(f"*{store_config['description']}*")
    
    selected_discounts = []
    for option in store_config['options']:
        col1, col2 = st.columns([1, 4])
        with col1:
            selected = st.checkbox(option['name'], key=f"discount_plan_{store_name}_{option['name']}")
        with col2:
            with st.expander("规则说明"):
                st.write(option['rule'])
        
        if selected:
            selected_discounts.append(option)
    
    # 一键试算按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("开始试算", key=f"calculate_plan_{store_name}"):
            if not selected_discounts:
                st.warning("请至少选择一个优惠项目")
            else:
                # 计算最终结果
                from main import calculate_detailed_price
                result = calculate_detailed_price(total_krw, selected_discounts)
                st.session_state.plan_calculation_result[store_name] = result
                st.session_state.show_plan_calculation_config[store_name] = False
                st.rerun()
    
    with col2:
        if st.button("返回购买计划", key=f"back_to_plan_{store_name}"):
            st.session_state.show_plan_calculation_config[store_name] = False
            st.rerun()


def display_store_calculation_results(store_name: str, products: list, result):
    """
    显示店铺购买计划的试算结果（改进版）
    
    改进点：
    1. 在进行任何汇率转换前，确保汇率信息有效
    2. 使用三层尝试机制获取有效汇率
    3. 改进的错误提示和降级处理
    """
    from main import convert_krw_to_cny
    
    if not result:
        st.error("试算失败，请重试")
        return
    
    st.subheader("📊 试算结果")
    
    # ============ 第0步：主动确保汇率有效（预防性检查） ============
    # 这是关键的改进——不是等汇率转换失败才检查，而是主动预检查
    
    if 'exchange_rate_info' not in st.session_state or st.session_state.exchange_rate_info is None:
        # Session state中没有汇率，立即尝试获取
        from exchange_rate import get_exchange_rate
        rate_info = get_exchange_rate()
        if rate_info:
            st.session_state.exchange_rate_info = rate_info
            st.info(f"✅ 已更新汇率：{rate_info.get('display_text', '汇率已就绪')}")
        else:
            st.warning("⚠️ 暂无法获取汇率信息，人民币价格可能显示为 0")
    
    # 显示产品清单
    st.write("**产品清单:**")
    for i, product in enumerate(products, 1):
        st.write(f"{i}. {product['exact_model'] or product['product_model']} - {product['color']} - {product['size']}")
    
    st.divider()
    
    # ============ 第1步：进行汇率转换（现在汇率应该已就绪） ============
    cny_price = convert_krw_to_cny(result['final_payment'])
    
    # ============ 第2步：如果转换失败（返回0），进行补救 ============
    if cny_price == 0:
        st.warning("⚠️ 人民币转换失败，正在尝试重新获取汇率...")
        from exchange_rate import get_exchange_rate, clear_exchange_rate_cache
        
        # 清空缓存强制重新获取
        clear_exchange_rate_cache()
        rate_info = get_exchange_rate()
        
        if rate_info and isinstance(rate_info, dict):
            # 保存到session_state
            st.session_state.exchange_rate_info = rate_info
            # 重新尝试转换
            cny_price = convert_krw_to_cny(result['final_payment'])
            if cny_price > 0:
                st.success(f"✅ 汇率已更新：{rate_info.get('display_text', '转换成功')}")
            else:
                st.error("❌ 汇率信息获取成功但仍无法转换，请稍后重试")
        else:
            st.error("❌ 暂无法获取有效的汇率信息")
    
    # ============ 第3步：计算国内总价和折扣率 ============
    total_domestic_price, has_all_domestic_prices = calculate_store_domestic_total(products)
    discount_rate = None
    if has_all_domestic_prices and total_domestic_price > 0 and cny_price > 0:
        discount_rate = int((cny_price / total_domestic_price) * 100)
    
    # 显示计算步骤
    st.write("**详细计算过程:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("原始总价", f"{result['total_krw']:,.0f}韩元")
        st.metric("税前优惠", f"-{result['pre_tax_discount']:,.0f}韩元")
        st.metric("优惠后总价", f"{result['after_pre_tax']:,.0f}韩元")
        st.metric("退税额", f"-{result['tax_refund']:,.0f}韩元")
    
    with col2:
        st.metric("税后总价", f"{result['after_tax']:,.0f}韩元")
        
        # 显示商品券和积分的组合情况
        if result['gift_coupon'] > 0 and result['points_reward'] > 0:
            # 同时有商品券和积分
            st.metric("商品券优惠", f"-{result['gift_coupon']:,.0f}韩元")
            st.metric("积分赠送", f"-{result['points_reward']:,.0f}积分")
            st.metric("最终实付",
                      f"{result['final_payment']:,.0f}韩元/{cny_price:,.0f}人民币",
                      f"含{result['gift_coupon']:,.0f}韩元商品券和{result['points_reward']:,.0f}积分")
        elif result['gift_coupon'] > 0:
            # 只有商品券
            st.metric("商品券优惠", f"-{result['gift_coupon']:,.0f}韩元")
            st.metric("最终实付",
                      f"{result['final_payment']:,.0f}韩元/{cny_price:,.0f}人民币",
                      f"含{result['gift_coupon']:,.0f}韩元商品券")
        elif result['points_reward'] > 0:
            # 只有积分
            st.metric("积分赠送", f"-{result['points_reward']:,.0f}积分")
            st.metric("最终实付",
                      f"{result['final_payment']:,.0f}韩元/{cny_price:,.0f}人民币",
                      f"含{result['points_reward']:,.0f}积分")
        else:
            # 没有商品券也没有积分
            st.metric("商品券优惠", "0韩元")
            st.metric("积分赠送", "0积分")
            st.metric("最终实付", f"{result['final_payment']:,.0f}韩元/{cny_price:,.0f}人民币")
    
    # 显示国内价格对比和折扣率
    st.divider()
    st.write("**国内价格对比:**")
    if has_all_domestic_prices:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("国内总价", f"{total_domestic_price:,.0f}元")
        with col2:
            st.metric("最终实付", f"{cny_price:,.0f}元")
        with col3:
            if discount_rate is not None:
                st.metric("折扣率", f"{discount_rate}%", delta=f"{100-discount_rate}% 优惠")
    else:
        st.warning("⚠️ 部分产品缺少国内价格数据，无法计算折扣率")
    
    # 显示使用的优惠
    st.divider()
    st.write("**使用的优惠:**")
    for discount in result['selected_discounts']:
        st.write(f"✅ {discount}")
