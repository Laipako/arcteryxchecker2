import time
import streamlit as st
from discount_config import DISCOUNT_CONFIG
import pandas as pd
from product_search import generate_api_url, extract_product_ids_from_api
from product_detail import extract_product_details, get_product_variants, get_sku_info
from favorites_manager import load_favorites, add_to_favorites, remove_from_favorites
from utils import standardize_model_name
from favorites_manager import add_to_favorites
# 确保导入以下函数
from inventory_check import (
    query_stock_by_product_id,
    translate_store_name,
    get_stock_status,
    calculate_enhanced_inventory_stats,
    calculate_product_depth_stats,
    calculate_key_store_analysis,
    safe_batch_query,
    STORE_REGION_MAPPING
)
import re
# 新增filter_utils的导入
from filter_utils import apply_filters_and_sort, convert_to_excel
from exchange_rate import get_exchange_rate  # 新增导入
# 在 main.py 的导入语句之后，main() 函数之前添加：
from cache_manager import product_cache
from product_detail import extract_product_details, get_product_variants
# 新增购买计划相关导入
from purchase_plan_manager import add_to_plan, check_product_in_plan, load_plans
from plan_display import show_purchase_plan_tab
from cache_ui import show_cache_management_tab
def format_string(s):
    """格式化字符串用于URL构造"""
    if not s:
        return ""
    # 替换所有非字母数字字符为连字符
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s)
    # 重新组合
    return s


def format_color(s):
    """格式化颜色名称，罗马数字全大写，其他单词首字母大写"""
    if not s:
        return ""

    # 替换所有非字母数字字符为连字符
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s)

    # 定义罗马数字模式（常见的罗马数字）
    roman_numerals = {'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'}

    # 分割单词并处理
    words = s.split('-')
    formatted_words = []

    for word in words:
        if not word:
            continue

        # 检查是否为罗马数字（全大写且在预定义列表中）
        if word.upper() in roman_numerals:
            formatted_words.append(word.upper())  # 罗马数字保持全大写
        else:
            # 其他单词：首字母大写，其余小写
            formatted_words.append(word.capitalize())

    # 重新组合
    return '-'.join(formatted_words)
def get_current_step():
    """获取当前步骤"""
    if "step_history" not in st.session_state:
        st.session_state.step_history = ["start"]
    return st.session_state.step_history[-1]

def go_to_step(step_name):
    """跳转到指定步骤"""
    if "step_history" not in st.session_state:
        st.session_state.step_history = ["start"]
    st.session_state.step_history.append(step_name)
    st.rerun()

def go_back():
    """回退到上一步"""
    if len(st.session_state.step_history) > 1:
        st.session_state.step_history.pop()
        st.rerun()
# 页面配置
st.set_page_config(
    page_title="始祖鸟查货系统",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def display_product_image(image_url, alt_text="产品图片"):
    """显示产品图片（自适应尺寸，无放大功能）"""
    # 占位图URL（使用Streamlit内置的占位图）
    placeholder_image = "https://via.placeholder.com/300x300/cccccc/969696?text=图片加载失败"

    if image_url:
        try:
            # 直接显示图片，不固定尺寸，自适应宽度
            st.image(image_url, caption=alt_text, use_container_width=True)
        except Exception as e:
            # 如果图片加载失败，显示占位图
            st.image(placeholder_image, caption="图片加载失败", use_container_width=True)
    else:
        # 没有图片URL时显示占位图
        st.image(placeholder_image, caption="图片暂不可用", use_container_width=True)
def show_product_query_tab():
    """显示产品查询标签页"""
    st.header("🔍 产品查询")

    # 产品型号输入
    product_model = st.text_input("请输入产品型号（如：beta sl）", key="product_model")
    # 新增：性别选择控件
    gender = st.radio(
        "选择性别",
        ["男款", "女款"],
        index=0,  # 默认选择男款
        key="gender_select",
        horizontal=True  # 水平排列
    )

    # 将中文转换为API参数
    gender_map = {"男款": "MALE", "女款": "FEMALE"}
    selected_gender = gender_map[gender]
    if st.button("搜索产品", key="search_btn"):
        if not product_model.strip():
            st.error("请输入产品型号")
            return

        standardized_model = standardize_model_name(product_model)
        st.session_state.search_model = standardized_model
        st.session_state.selected_gender = selected_gender  # 保存性别选择

        # 生成API URL并获取产品ID
        api_url = generate_api_url(standardized_model, gender=selected_gender)
        product_ids = extract_product_ids_from_api(api_url)

        if not product_ids:
            st.error("未找到匹配的产品")
            return

        st.session_state.product_ids = product_ids
        go_to_step("select_product")

    # 根据当前步骤显示相应界面
    current_step = get_current_step()

    if current_step == "select_product":
        show_product_selection()
    elif current_step == "select_color":
        show_color_selection()
    elif current_step == "select_size":
        show_size_selection()
    elif current_step == "show_details":
        show_product_details()


def show_product_selection():
    """显示产品选择界面（优化版）"""
    # 1. 优化：提前检查必要的session_state状态
    required_states = ['search_model', 'selected_gender', 'product_ids']
    missing_states = [state for state in required_states if state not in st.session_state]

    if missing_states:
        st.error(f"系统状态异常，缺少: {', '.join(missing_states)}")
        if st.button("← 返回搜索", key="back_to_search_error"):
            go_back()
        return

    # 2. 显示界面标题和搜索条件（保留原有功能）
    st.subheader("找到以下产品，请选择：")

    # 优化：使用更清晰的变量名
    gender_display = {"MALE": "男款", "FEMALE": "女款"}
    current_gender = gender_display.get(st.session_state.selected_gender, "男款")

    # 优化：使用更醒目的方式显示搜索条件
    st.markdown(f"""
    **搜索条件:** `{st.session_state.search_model}` - **{current_gender}**
    """)

    # 3. 回退按钮布局优化
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← 返回搜索", key="back_to_search"):
            go_back()

    # 4. 优化产品详情获取流程
    product_ids = st.session_state.product_ids
    product_details = []

    # 优化：添加加载状态指示器
    progress_bar = st.progress(0)
    status_text = st.empty()

    total_products = len(product_ids)

    for i, pid in enumerate(product_ids):
        # 更新进度状态
        progress = (i + 1) / total_products
        progress_bar.progress(progress)
        status_text.text(f"正在获取产品信息... ({i + 1}/{total_products})")

        detail_url = f"https://arcteryx.co.kr/products/view/{pid}?sc=100"

        # 优化：添加缓存机制（如果可用）
        cache_key = f"product_detail_{pid}"
        if cache_key in st.session_state:
            full_info = st.session_state[cache_key]
            details = full_info["details"]
        else:
            details = extract_product_details(detail_url)
            color_options, size_options = get_product_variants(detail_url)
            if details and color_options:
                # 存储完整的缓存信息
                full_info = {
                    "details": details,
                    "color_options": color_options,
                    "size_options": size_options,
                    "detail_url": detail_url
                }
                st.session_state[cache_key] = full_info
            else:
                full_info = None
        if details:
            product_details.append({
                "id": pid,
                "description": details["description"],
                "year_info": details["year_info"],
                "exact_model": details["exact_model"],
                "has_full_info": full_info is not None  # 标记是否有完整信息
            })

    # 清除进度指示器
    progress_bar.empty()
    status_text.empty()


    # 5. 优化产品显示逻辑
    if not product_details:
        st.warning("⚠️ 未能获取到产品详情信息")
        return

    # 优化：使用更清晰的布局显示产品
    for i, product in enumerate(product_details):
        # 优化：使用更紧凑的expand布局
        with st.expander(f"🎯🎯 产品 {i + 1}: {product['exact_model']}", expanded=(i == 0)):

            # 优化：使用列布局显示产品信息
            col_info, col_action = st.columns([3, 1])

            with col_info:
                # 保留原有显示格式，但优化布局
                st.markdown(f"**📋📋 型号:** {product['exact_model']}")
                st.markdown(f"**📅📅 年份款式:** {product['year_info']}")

                # 优化：限制描述文本长度，避免界面过长
                description = product['description']
                if len(description) > 150:
                    description = description[:150] + "..."
                st.markdown(f"**📝📝 描述:** {description}")

                # 新增：显示信息完整性状态
                if not product.get('has_full_info', True):
                    st.warning("⚠️ 该产品颜色/尺码信息可能不完整")

            with col_action:
                # 优化：按钮样式和布局
                if st.button("选择此产品", key=f"select_{i}", use_container_width=True):
                    st.session_state.selected_product_id = product["id"]
                    st.session_state.exact_model = product["exact_model"]
                    st.session_state.year_info = product["year_info"]

                    # 新增：存储完整缓存信息供后续步骤使用
                    cache_key = f"product_full_info_{product['id']}"
                    full_info = st.session_state.get(cache_key)

                    if full_info:
                        # 使用预缓存的完整信息
                        st.session_state.cached_product_info = full_info
                    else:
                        # 如果没有缓存，实时获取完整信息
                        detail_url = f"https://arcteryx.co.kr/products/view/{product['id']}?sc=100"
                        color_options, size_options = get_product_variants(detail_url)
                        details = extract_product_details(detail_url)

                        if color_options:
                            st.session_state.cached_product_info = {
                                "details": details,
                                "color_options": color_options,
                                "size_options": size_options,
                                "detail_url": detail_url
                            }
                        else:
                            st.error("无法获取产品颜色选项，请重新选择")
                            return

                    # 优化：添加成功反馈
                    st.success(f"✅ 已选择: {product['exact_model']}")

                    # 添加短暂延迟后跳转，让用户看到反馈
                    import time
                    time.sleep(0.5)
                    go_to_step("select_color")

                    # 防止多个按钮同时触发
                    st.rerun()

    # 6. 优化：添加底部导航提示
    st.markdown("---")
    st.caption("💡 提示: 点击产品上方的展开箭头查看详细信息，然后点击'选择此产品'按钮继续")



def show_color_selection():
    """显示带色块的颜色选择界面（修复版）"""
    st.subheader("颜色选择")

    # 1. 初始化选中状态
    if "selected_color" not in st.session_state:
        st.session_state.selected_color = ""

    # 2. 回退按钮
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← 返回产品选择", key="back_to_product"):
            go_back()

    # 3. 从缓存获取颜色选项
    cached_info = st.session_state.get('cached_product_info')
    if not cached_info:
        st.error("缓存信息丢失，请重新选择产品")
        return

    color_options = cached_info['color_options']
    size_options = cached_info['size_options']

    if not color_options:
        st.error("无法获取颜色选项")
        return

    st.session_state.color_options = color_options
    st.session_state.size_options = size_options

    # 4. 创建颜色名称列表用于radio控件
    color_names = [color["name"] for color in color_options]

    # 5. 创建两列布局：左侧radio选择，右侧色块显示
    col_left, col_right = st.columns([1, 6])

    with col_left:
        # 创建radio控件（独立于循环之外）
        selected_color_name = st.radio(
            "请选择颜色:",
            options=color_names,
            index=color_names.index(
                st.session_state.selected_color) if st.session_state.selected_color in color_names else 0,
            key="color_radio_main"
        )

        # 更新选中的颜色
        if selected_color_name != st.session_state.selected_color:
            st.session_state.selected_color = selected_color_name
            st.rerun()

    with col_right:
        st.markdown(
            """
            <div style="font-size: 12px; margin-bottom: 5px; font-weight: normal;">
                颜色预览
            </div>
            """,
            unsafe_allow_html=True
        )
        # 为每个颜色显示色块（在循环中）
        for color in color_options:
            # 获取颜色HEX值
            hex_color = color.get('hex', '#CCCCCC')

            # 显示色块和颜色名称（紧凑布局）
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin: 0.5px 0; padding: 1px 0;">
                    <div style="width: 24px; height: 24px; background-color: {hex_color}; 
                             border: 0.1px solid #ddd; border-radius: 4px; flex-shrink: 0;"></div>
                </div>
                """, unsafe_allow_html=True)

    # 6. 确认按钮
    if st.button("确认颜色", key="confirm_color"):
        if not st.session_state.selected_color:
            st.warning("请先选择颜色")
        else:
            go_to_step("select_size")


def show_size_selection():
    """显示尺码选择界面"""
    st.subheader("尺码选择")

    # 从缓存获取尺码选项
    cached_info = st.session_state.get('cached_product_info')
    if not cached_info:
        st.error("缓存信息丢失，请重新选择产品")
        return

    size_options = cached_info['size_options']

    if not size_options:
        st.error("无法获取尺码选项")
        return
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← 返回颜色选择", key="back_to_color"):
            go_back()
    selected_size = st.radio("请选择尺码:", st.session_state.size_options, key="size_radio")


    # 尺码选项和确认按钮之间留出间距
    st.write("")  # 空行增加间距
    # 确认按钮与回退按钮并排
    col1, col2 = st.columns(2)
    with col1:
        if st.button("确认尺码", key="confirm_size"):
            st.session_state.selected_size = selected_size
            go_to_step("show_details")


def show_product_details():
    """显示产品详情页面（使用缓存基本信息，实时查询价格库存）"""
    st.subheader("产品详情")

    # 回退按钮
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← 返回尺码选择", key="back_to_size"):
            go_back()

    # 从缓存获取基本信息
    cached_info = st.session_state.get('cached_product_info')
    if not cached_info:
        st.error("缓存信息丢失，请重新选择产品")
        return

    # 使用缓存的基本信息
    details = cached_info.get('details', {})
    detail_url = cached_info.get('detail_url', '')

    # 实时查询价格和库存信息（不使用缓存）
    sku_info = get_sku_info(detail_url, st.session_state.selected_color, st.session_state.selected_size)

    if not sku_info:
        st.error("无法获取产品SKU信息")
        return

    # 图片URL生成
    product_id = st.session_state.selected_product_id
    image_url = None
    if product_id:
        try:
            formatted_model = format_string(st.session_state.exact_model)
            formatted_color = format_color(st.session_state.selected_color)
            gender = st.session_state.selected_gender  # MALE 或 FEMALE

            if gender == "FEMALE":
                image_url = f"https://product.arcteryx.co.kr/images/products/{product_id}/{formatted_model}-W-{formatted_color}.jpg"
            else:
                image_url = f"https://product.arcteryx.co.kr/images/products/{product_id}/{formatted_model}-{formatted_color}.jpg"
        except Exception as e:
            print(f"图片URL生成失败: {e}")
            image_url = None

    st.session_state.product_image_url = image_url

    # 使用两列布局：图片在左，信息在右
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("产品图片")
        image_url = st.session_state.get('product_image_url')
        if image_url:
            try:
                st.image(image_url, caption=f"{st.session_state.exact_model} - {st.session_state.selected_color}",
                         use_container_width=True)
            except Exception as e:
                st.error("图片加载失败")
                st.info("🖼️ 图片暂不可用")
        else:
            st.info("📷 无产品图片")

    with col2:
        st.subheader("产品信息")

        # 安全获取并显示产品信息
        exact_model = st.session_state.get('exact_model', st.session_state.get('search_model', '未知型号'))
        st.write(f"**型号:** {exact_model}")

        year_info = st.session_state.get('year_info', '未获取年份信息')
        st.write(f"**年份款式:** {year_info}")

        st.write(f"**颜色:** {st.session_state.selected_color}")
        st.write(f"**尺码:** {st.session_state.selected_size}")
        st.write(f"**SKU:** {sku_info.get('sku_id', '未知')}")

        # 价格信息（实时查询）
        try:
            krw_price = int(sku_info.get('sell_price', 0))
            cny_price = convert_krw_to_cny(krw_price)
            st.write(f"**韩国售价:** {krw_price:,}韩元 / {cny_price:,}人民币")

            adjust_krw = int(sku_info.get('adjust_price', 0))
            adjust_cny = convert_krw_to_cny(adjust_krw)
            st.write(f"**调整售价:** {adjust_krw:,}韩元 / {adjust_cny:,}人民币")

            stock = sku_info.get('stock', 0)
            st.write(f"**库存:** {stock} 件")
        except Exception as e:
            st.error(f"价格信息获取失败: {e}")

        # 国内售价输入框
        china_price = st.number_input(
            "国内售价（人民币）",
            min_value=1,
            value=None,
            step=100,
            key="china_price_input",
            help="请输入产品的国内售价（人民币），必须大于0"
        )

        # 计算折扣率
        discount_rate = "暂无"
        if china_price and china_price > 0:
            try:
                krw_price = int(sku_info.get('sell_price', 0))
                cny_price = convert_krw_to_cny(krw_price)
                if cny_price > 0:
                    discount = int((cny_price / china_price) * 100)
                    discount_rate = f"{discount}%"
            except Exception:
                discount_rate = "计算失败"

        st.subheader("操作")

        # 查库存按钮（实时查询）
        if st.button("查询库存", key="check_inventory"):
            try:
                stores = query_stock_by_product_id(sku_info.get('sku_id', ''))
                if stores:
                    st.subheader("实时库存情况")
                    for store in stores:
                        store_name = translate_store_name(store.get("store_name", ""))
                        stock_status = get_stock_status(store.get("usable_stock", ""))
                        st.write(f"{store_name}: {stock_status}")
                else:
                    st.error("无法获取实时库存信息")
            except Exception as e:
                st.error(f"库存查询失败: {e}")

        # 加入收藏按钮
        if st.button("加入收藏", key="add_to_favorites"):
            try:
                product_info = {
                    "product_model": st.session_state.search_model,
                    "exact_model": details.get("exact_model", st.session_state.search_model),
                    "year_info": details.get("year_info", "未知年份"),
                    "color": st.session_state.selected_color,
                    "size": st.session_state.selected_size,
                    "price": sku_info.get('sell_price', '0'),
                    "korea_price_cny": convert_krw_to_cny(int(sku_info.get('sell_price', 0))),
                    "china_price_cny": china_price if china_price and china_price > 0 else None,
                    "discount_rate": discount_rate,
                    "sku": sku_info.get('sku_id', ''),
                    "image_url": st.session_state.product_image_url
                }

                success, message = add_to_favorites(product_info)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"添加到收藏失败: {e}")

def calculate_discount_rate(korea_price_cny, china_price_cny):
    """修复后的折扣计算函数"""
    print(f"调试信息 - 韩国价: {korea_price_cny} ({type(korea_price_cny)})")
    print(f"调试信息 - 国内价: {china_price_cny} ({type(china_price_cny)})")
    try:
        # 确保数据类型正确
        korea_price = float(korea_price_cny) if korea_price_cny else 0
        china_price = float(china_price_cny) if china_price_cny else 0

        # 验证数据有效性
        if china_price <= 0 or korea_price <= 0:
            return "暂无"

        # 计算折扣率
        discount = int((korea_price / china_price) * 100)
        return f"{discount}%"

    except (ValueError, TypeError, ZeroDivisionError):
        return "暂无"

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
            import re
            match = re.search(r'10000韩元=(\d+\.?\d*)人民币', rate_str)
            if match:
                rate_per_10000 = float(match.group(1))
                cny_amount = (krw_amount / 10000) * rate_per_10000
                return int(cny_amount)  # 取整显示
    except:
        pass

    # 汇率获取失败时返回0（前端会只显示韩元）
    return 0


def show_favorites_tab():
    """显示收藏产品标签页"""
    # 数据备份机制
    if "favorites_backup" not in st.session_state:
        st.session_state.favorites_backup = None

    # 在关键操作前备份数据
    try:
        favorites = load_favorites()
        st.session_state.favorites_backup = favorites.copy()  # 备份
    except:
        favorites = st.session_state.get("favorites_backup", [])
    # 初始化session_state（在函数内部）
    if "inventory_queried" not in st.session_state:
        st.session_state.inventory_queried = False
    if "inventory_matrix" not in st.session_state:
        st.session_state.inventory_matrix = None
    if "stock_filter" not in st.session_state:
        st.session_state.stock_filter = "全部"
    if "region_filter" not in st.session_state:
        st.session_state.region_filter = "全部"
    if "sort_option" not in st.session_state:
        st.session_state.sort_option = "默认"

    # 新增：初始化选中状态
    if "selected_favorites" not in st.session_state:
        st.session_state.selected_favorites = set()

    # 新增：统一初始化试算相关状态
    if "show_calculation_config" not in st.session_state:
        st.session_state.show_calculation_config = False
    if "selected_for_calculation" not in st.session_state:
        st.session_state.selected_for_calculation = []
    if "calculation_result" not in st.session_state:
        st.session_state.calculation_result = None

    st.header("⭐ 收藏产品")

    favorites = load_favorites()

    if not favorites:
        st.info("暂无收藏产品")
        return

    # 显示选中状态控制行
    st.subheader("收藏列表")

    # 显示收藏列表（每个产品前添加复选框）
    for i, favorite in enumerate(favorites):
        # 使用5列布局，第一列为复选框
        col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 1, 1])

        with col1:
            # 复选框 - 管理选中状态
            is_selected = i in st.session_state.selected_favorites
            new_selected = st.checkbox(
                "选择",
                value=is_selected,
                key=f"fav_checkbox_{i}",
                label_visibility="collapsed"  # 隐藏标签但保持可访问性
            )
            # 如果复选框状态发生变化，更新session_state
            if new_selected != is_selected:
                if new_selected:
                    st.session_state.selected_favorites.add(i)
                else:
                    st.session_state.selected_favorites.discard(i)
                st.rerun()

        with col2:
            # 修改显示格式，与产品详情页保持一致
            exact_model = favorite.get('exact_model', favorite.get('product_model', '未知型号'))
            year_info = favorite.get('year_info', '未知年份')
            st.write(f"*{exact_model} - {year_info}*")
            st.write(f"**颜色:** {favorite['color']} | **尺码:** {favorite['size']}")

            # 价格显示（韩元 + 人民币）
            krw_price = int(favorite['price'])
            cny_price = convert_krw_to_cny(krw_price)

            # 与产品详情页相同的价格显示格式
            st.write(f"**售价:** {krw_price}韩元 / {cny_price}人民币")
            # 新增：国内售价和折扣
            china_price = favorite.get('china_price_cny')
            discount_rate = favorite.get('discount_rate', "暂无")

            if china_price:
                st.write(f"**国内售价:** {china_price}人民币")
                st.write(f"**折扣:** {discount_rate}")
            else:
                st.write("**国内售价:** 暂无")
                st.write("**折扣:** 暂无")
            st.write(f"**SKU:** {favorite['sku']}")

        with col3:
            # 显示产品图片（可选功能）
            image_url = favorite.get('image_url')
            if image_url:
                try:
                    st.image(image_url, width=150)  # 适当缩小图片尺寸
                except:
                    # 图片加载失败时显示占位符
                    st.write("🖼️ 图片加载失败")
            else:
                # 没有图片URL时显示提示
                st.write("📷 无图片")

        # 操作按钮区域 - 上下两行
        with col4:
            # 删除按钮（需要确认）
            if st.button("删除", key=f"delete_{i}"):
                if st.session_state.get(f"confirm_delete_{i}", False):
                    success, message = remove_from_favorites(i)
                    if success:
                        st.success(message)
                        # 同时从选中状态中移除
                        st.session_state.selected_favorites.discard(i)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.session_state[f"confirm_delete_{i}"] = True
                    st.warning("确认删除？")

        with col5:
            # 单个产品查库存按钮
            if st.button("查库存", key=f"check_{i}"):
                stores = query_stock_by_product_id(favorite['sku'])
                if stores:
                    # 显示库存查询结果
                    st.subheader(f"{favorite['exact_model']} 库存情况")
                    for store in stores:
                        store_name = translate_store_name(store.get("store_name", ""))
                        stock_status = get_stock_status(store.get("usable_stock", ""))
                        st.write(f"{store_name}: {stock_status}")
                else:
                    st.error("无法获取库存信息")

        # 第二行：加入购买计划按钮
        col_plan1, col_plan2, col_plan3 = st.columns([1, 3, 3])
        with col_plan3:
            # 检查产品是否已在购买计划中
            is_in_plan, existing_store = check_product_in_plan(
                favorite['product_model'], 
                favorite['color'], 
                favorite['size']
            )
            
            if is_in_plan:
                st.info(f"✓ 已在 {existing_store} 的购买计划中")
            else:
                if st.button("加入购买计划", key=f"add_plan_{i}"):
                    st.session_state[f"show_store_selection_{i}"] = True
                
                # 显示店铺选择下拉框
                if st.session_state.get(f"show_store_selection_{i}", False):
                    store_list = sorted(STORE_REGION_MAPPING.keys())
                    selected_store = st.selectbox(
                        f"选择店铺",
                        store_list,
                        key=f"store_select_{i}"
                    )
                    
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("确认", key=f"confirm_add_plan_{i}"):
                            # 准备产品信息
                            product_info = {
                                "product_model": favorite['product_model'],
                                "exact_model": favorite.get('exact_model', ''),
                                "color": favorite['color'],
                                "size": favorite['size'],
                                "price_krw": int(favorite['price']),
                                "year_info": favorite.get('year_info', ''),
                                "domestic_price_cny": favorite.get('china_price_cny', None)
                            }
                            
                            if add_to_plan(selected_store, product_info):
                                st.session_state[f"show_store_selection_{i}"] = False
                                st.rerun()
                    
                    with col_cancel:
                        if st.button("取消", key=f"cancel_add_plan_{i}"):
                            st.session_state[f"show_store_selection_{i}"] = False
                            st.rerun()

        st.divider()

    # 初始化session_state
    if "show_calculation" not in st.session_state:
        st.session_state.show_calculation = False
    if "selected_for_calculation" not in st.session_state:
        st.session_state.selected_for_calculation = []
    # 一键查库存功能（只查询选中产品）
    st.subheader("批量操作")

    # 修改：将列数从3增加到4，为试算按钮留出空间
    col_batch_ops = st.columns([2, 1, 1, 1])  # 增加一列
    # 在 show_favorites_tab 函数中修改查询调用部分
    with col_batch_ops[0]:
        if st.button("一键查库存（选中产品）", key="batch_check_selected"):
            selected_indices = st.session_state.selected_favorites
            selected_favorites = [favorites[i] for i in selected_indices if i < len(favorites)]

            if not selected_favorites:
                st.warning("请先选择要查询的产品")
            else:
                # 显示查询进度
                progress_text = st.empty()
                progress_text.info("开始安全并发查询 " + str(len(selected_favorites)) + " 个产品...")

                # 使用安全的并发查询
                inventory_matrix = safe_batch_query(selected_favorites)

                if inventory_matrix:
                    st.session_state.inventory_queried = True
                    st.session_state.inventory_matrix = inventory_matrix
                    progress_text.success("查询完成！共获取 " + str(len(inventory_matrix)) + " 个店铺的库存数据")
                else:
                    st.error("库存查询失败，请检查网络连接或稍后重试")

                # 清除进度显示
                time.sleep(2)
                progress_text.empty()

    with col_batch_ops[1]:
        # 修复后的"查所有库存"按钮
        if st.button("查全部库存", key="batch_check_all"):
            if not favorites:
                st.warning("收藏列表为空")
            else:
                # 显示查询进度
                progress_text = st.empty()
                progress_text.info(f"开始查询所有 {len(favorites)} 个产品的库存...")

                # 实际执行查询（查询所有收藏产品）
                inventory_matrix = safe_batch_query(favorites)

                if inventory_matrix:
                    st.session_state.inventory_queried = True
                    st.session_state.inventory_matrix = inventory_matrix
                    progress_text.success(f"查询完成！共获取 {len(inventory_matrix)} 个店铺的库存数据")
                else:
                    st.error("库存查询失败，请检查网络连接或稍后重试")

                # 清除进度显示
                time.sleep(2)
                progress_text.empty()
                st.rerun()
    with col_batch_ops[2]:
        if st.session_state.inventory_queried and st.button("重新查询", key="requery"):
            st.session_state.inventory_queried = False
            st.session_state.inventory_matrix = None
            st.session_state.stock_filter = "全部"
            st.session_state.region_filter = "全部"
            st.session_state.sort_option = "默认"
            st.rerun()


    # 新增：显示试算配置窗口
    if st.session_state.show_calculation_config:
        show_calculation_config_window(st.session_state.selected_for_calculation)
        return  # 显示配置窗口时不再显示其他内容

    # 显示试算结果
    if st.session_state.calculation_result:
        with st.expander("💰 试算结果", expanded=True):
            col_close, _ = st.columns([1, 3])
            with col_close:
                if st.button("✕ 关闭试算", key="close_calculation_result"):
                    st.session_state.calculation_result = None
                    st.session_state.selected_for_calculation = []
                    st.rerun()

            display_calculation_results(
                st.session_state.selected_for_calculation,
                st.session_state.calculation_result
            )
    # 显示库存矩阵（基于session_state判断）
    if st.session_state.inventory_queried and st.session_state.inventory_matrix:
        # 显示查询范围信息
        selected_count = len(st.session_state.selected_favorites)
        if selected_count > 0:
            st.info(f"📊 当前显示 {selected_count} 个选中产品的库存矩阵")
        else:
            st.info("📊 当前显示所有产品的库存矩阵")

        st.subheader("库存矩阵")

        # 获取缓存的库存矩阵
        inventory_matrix = st.session_state.inventory_matrix

        if inventory_matrix:
            # 使用新的统计函数
            stats = calculate_enhanced_inventory_stats(inventory_matrix)

            # 显示实时库存状态分布
            st.subheader("📊 库存状态分布")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ 高库存店铺",
                          f"{stats['stock_status']['高库存店铺']['count']}家",
                          f"{stats['stock_status']['高库存店铺']['percentage']}%")
            with col2:
                st.metric("⚠️ 低库存店铺",
                          f"{stats['stock_status']['低库存店铺']['count']}家",
                          f"{stats['stock_status']['低库存店铺']['percentage']}%")
            with col3:
                st.metric("❌ 无库存店铺",
                          f"{stats['stock_status']['无库存店铺']['count']}家",
                          f"{stats['stock_status']['无库存店铺']['percentage']}%")

            # 显示区域库存热力图
            st.subheader("🗺️ 区域库存分布")
            for region, data in stats['region_heatmap'].items():
                st.write(f"**{region}**: {data['count']}家店铺 ({data['percentage']}%) - {data['inventory']}件库存")

            # 获取当前显示的产品列表（选中产品或全部产品）
            if selected_count > 0:
                display_favorites = [favorites[i] for i in st.session_state.selected_favorites if i < len(favorites)]
            else:
                display_favorites = favorites

            # 先显示重点关注店铺分析
            st.subheader("🏪🏪 重点关注店铺库存分析")

            # 计算重点关注店铺分析
            key_store_analysis = calculate_key_store_analysis(display_favorites, inventory_matrix)

            # 显示每个重点关注店铺的库存情况
            for store_name, products in key_store_analysis.items():
                if products:
                    # 创建两列布局：店铺名称在左，库存详情在右（可折叠）
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        # 店铺名称始终显示（不折叠）
                        st.write(f"**{store_name}**")

                    with col2:
                        # 库存详情可折叠
                        with st.expander(f"查看库存详情", expanded=False):
                            # 显示所有产品的库存状态
                            for product in products:
                                st.write(f"• {product['display_text']}")
                else:
                    # 如果店铺没有相关产品数据
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.write(f"**{store_name}**")
                    with col2:
                        st.write("该店铺无相关产品库存数据")

                st.divider()

            st.subheader("📦📦 产品库存深度分析")

            product_depth_stats = calculate_product_depth_stats(display_favorites, inventory_matrix)

            for product_key, stats in product_depth_stats.items():
                with st.expander(f"{product_key} 库存分析"):
                    # 基础统计
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("📦 总库存", f"{stats['total_inventory']}件")
                    with col2:
                        st.metric("🏪 有库存店铺", f"{stats['stores_with_stock']}家")

                    # 详细区域分布
                    st.write("📍 区域分布:")
                    for region, region_data in stats['region_distribution'].items():
                        if region_data['total'] > 0:
                            # 显示区域汇总
                            st.write(f"**{region}**: {region_data['total']}件")

                            # 显示具体店铺分布（缩进显示）
                            for store_info in region_data['stores']:
                                st.write(f"  - {store_info['store_name']}: {store_info['stock']}件")

            # 筛选区域
            st.subheader("筛选选项")
            filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 2, 2, 1])

            with filter_col1:
                stock_filter = st.selectbox(
                    "库存状态",
                    ["全部", "有库存", "无库存"],
                    index=["全部", "有库存", "无库存"].index(st.session_state.stock_filter),
                    key="stock_filter_select"
                )

            with filter_col2:
                region_filter = st.selectbox(
                    "店铺区域",
                    ["全部", "首尔城区", "京畿道地区", "釜山", "大邱"],
                    index=["全部", "首尔城区", "京畿道地区", "釜山", "大邱"].index(st.session_state.region_filter),
                    key="region_filter_select"
                )

            with filter_col3:
                sort_option = st.selectbox(
                    "排序方式",
                    ["默认", "库存总量降序", "库存总量升序"],
                    index=["默认", "库存总量降序", "库存总量升序"].index(st.session_state.sort_option),
                    key="sort_option_select"
                )

            with filter_col4:
                st.write("")  # 空行用于对齐
                if st.button("一键清除筛选", key="clear_filters"):
                    st.session_state.stock_filter = "全部"
                    st.session_state.region_filter = "全部"
                    st.session_state.sort_option = "默认"
                    st.rerun()

            # 更新session状态
            st.session_state.stock_filter = stock_filter
            st.session_state.region_filter = region_filter
            st.session_state.sort_option = sort_option

            # 应用筛选和排序
            filtered_matrix = apply_filters_and_sort(
                inventory_matrix, stock_filter, region_filter, sort_option
            )

            if filtered_matrix:
                # 转换为DataFrame显示
                df = pd.DataFrame.from_dict(filtered_matrix, orient='index')

                # 添加表格样式
                st.markdown("""
                <style>
                .dataframe {
                    font-size: 11px;
                }
                .dataframe th {
                    font-size: 11px;
                    white-space: nowrap;
                }
                .dataframe td {
                    font-size: 11px;
                    white-space: nowrap;
                }
                </style>
                """, unsafe_allow_html=True)

                st.dataframe(df, use_container_width=True, height=500)

                # Excel下载按钮 - 转换DataFrame为JSON字符串以支持缓存
                import json
                df_dict = df.to_dict(orient='index')
                df_json_str = json.dumps(df_dict, default=str)
                excel_data = convert_to_excel(df_json_str)
                st.download_button(
                    label="下载库存数据(Excel)",
                    data=excel_data,
                    file_name="inventory_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("没有找到符合筛选条件的店铺")
        else:
            st.error("无法生成库存矩阵")

        # 新增：试算结果显示（放在函数末尾）


# 在 main.py 中添加新函数
def show_calculation_config_window(selected_products):
    """显示试算配置窗口"""
    st.subheader("💰 试算配置")

    # 显示选中的产品清单
    st.write("**选中的产品清单:**")
    for i, product in enumerate(selected_products, 1):
        st.write(
            f"{i}. {product['exact_model']} - {product['color']} - {product['size']} - {int(product['price']):,}韩元")

    # 计算原始总价
    total_krw = sum(float(product['price']) for product in selected_products)
    st.write(f"**原始总价:** {total_krw:,.0f}韩元")

    st.divider()

    # 商家选择
    st.write("**选择商家优惠:**")
    store_options = ["明洞乐天", "新世界", "韩国电话注册", "乐天/新世界奥莱", "现代百货"]
    selected_store = st.radio("选择商家", store_options, key="store_selection")

    # 检测商家是否改变，如果改变则清除之前的优惠选择
    if "last_selected_store" not in st.session_state:
        st.session_state.last_selected_store = selected_store
    elif st.session_state.last_selected_store != selected_store:
        # 商家改变，清除所有discount checkbox的状态
        st.session_state.last_selected_store = selected_store
        # 遍历所有键，删除与discount相关的key
        keys_to_delete = [k for k in st.session_state.keys() if k.startswith("discount_")]
        for key in keys_to_delete:
            del st.session_state[key]
        st.rerun()

    # 显示优惠选项
    store_config = DISCOUNT_CONFIG[selected_store]
    st.write(f"*{store_config['description']}*")

    selected_discounts = []
    for option in store_config['options']:
        col1, col2 = st.columns([1, 4])
        with col1:
            selected = st.checkbox(option['name'], key=f"discount_{option['name']}_{len(selected_discounts)}")
        with col2:
            with st.expander("ℹ️ 规则说明"):
                st.write(option['rule'])

        if selected:
            selected_discounts.append(option)

    # 按钮布局
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 开始试算", key="calculate_final"):
            if not selected_discounts:
                st.warning("请至少选择一个优惠项目")
            else:
                # 计算最终结果
                result = calculate_detailed_price(total_krw, selected_discounts)
                st.session_state.calculation_result = result
                st.session_state.show_calculation_config = False
                st.rerun()

    with col2:
        if st.button("← 返回收藏列表", key="back_to_favorites"):
            st.session_state.show_calculation_config = False
            st.session_state.selected_for_calculation = []
            st.rerun()


# 新增详细计算函数
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
def batch_calculate(selected_products):
    """批量计算选中产品的总价和折扣"""
    try:
        # 计算韩元总价
        total_krw = sum(float(product['price']) for product in selected_products)

        # 计算退税（基于总价）
        tax_refund = calculate_tax_refund(total_krw)
        after_tax_krw = total_krw - tax_refund

        # 计算人民币价格（使用实时汇率）
        after_tax_cny = convert_krw_to_cny(after_tax_krw)

        # 检查国内售价完整性
        has_all_china_prices = True
        total_china_price = 0

        for product in selected_products:
            china_price = product.get('china_price_cny')
            if not china_price or float(china_price) <= 0:
                has_all_china_prices = False
                break
            total_china_price += float(china_price)

        # 计算折扣率
        if has_all_china_prices and total_china_price > 0:
            discount_rate = int((after_tax_cny / total_china_price) * 100)
        else:
            discount_rate = None

        return {
            'total_krw': total_krw,
            'tax_refund': tax_refund,
            'after_tax_krw': after_tax_krw,
            'after_tax_cny': after_tax_cny,
            'total_china_price': total_china_price if has_all_china_prices else None,
            'discount_rate': discount_rate,
            'has_all_china_prices': has_all_china_prices
        }

    except Exception as e:
        st.error(f"计算失败: {e}")
        return None


def calculate_tax_refund(total_amount):
    """根据韩国退税税率表计算退税额（基于总价）"""
    # 韩国退税税率表（基于总价）
    tax_brackets = [
        (15000, 29999, 1000),
        (30000, 49999, 2000),
        (50000, 74999, 3500),
        (75000, 99999, 5000),
        (100000, 124999, 6000),
        (125000, 149999, 7000),
        (150000, 199999, 10000),
        (200000, 249999, 13000),
        (250000, 299999, 15000),
        (300000, 399999, 20000),
        (400000, 499999, 25000),
        (500000, 599999, 30000),
        (600000, 699999, 35000),
        (700000, 799999, 40000),
        (800000, 899999, 45000),
        (900000, 999999, 50000),
        (1000000, 1249999, 55000),
        (1250000, 1499999, 60000),
        (1500000, 1999999, 70000),
        (2000000, 2499999, 80000),
        (2500000, 2999999, 90000),
        (3000000, 3999999, 100000),
        (4000000, 4999999, 120000),
        (5000000, 5999999, 140000),
        (6000000, 6999999, 170000),
        (7000000, 7999999, 200000),
        (8000000, 8999999, 230000),
        (9000000, 9999999, 260000),
        (10000000, 11499999, 300000),
        (11500000, 12999999, 340000),
        (13000000, 14999999, 380000),
        (15000000, 100000000, 480000)  # 最高退税额
    ]

    for min_amount, max_amount, refund in tax_brackets:
        if min_amount <= total_amount <= max_amount:
            return refund
    return 0


# 修改 display_calculation_results 函数
def display_calculation_results(selected_products, result):
    """显示试算结果"""
    if not result:
        st.error("试算失败，请重试")
        return

    st.subheader("📊 试算结果")

    # 关闭按钮
    if st.button("✕ 关闭试算", key="close_calculation"):
        st.session_state.show_calculation = False
        st.session_state.calculation_result = None
        st.rerun()

    # 显示选中的产品
    st.write("**选中的产品清单:**")
    for i, product in enumerate(selected_products, 1):
        st.write(f"{i}. {product['exact_model']} - {product['color']} - {product['size']}")

    st.divider()
    # 计算国内总价和折扣率
    total_china_price = 0
    has_all_china_prices = True

    for product in selected_products:
        china_price = product.get('china_price_cny')
        if not china_price or float(china_price) <= 0:
            has_all_china_prices = False
            break
        total_china_price += float(china_price)

    # 计算人民币价格
    cny_price = convert_krw_to_cny(result['final_payment'])

    # 计算折扣率
    discount_rate = None
    if has_all_china_prices and total_china_price > 0:
        discount_rate = int((cny_price / total_china_price) * 100)
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
            # 同时有商品券和积分（虽然按照需求不应该出现，但保险起见处理）
            st.metric("商品券优惠", f"-{result['gift_coupon']:,.0f}韩元")
            st.metric("积分赠送", f"-{result['points_reward']:,.0f}积分")
            total_benefit = result['gift_coupon'] + result['points_reward']
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
    # 显示国内总价和折扣信息
    st.divider()
    st.write("**国内价格对比:**")

    col3, col4 = st.columns(2)

    with col3:
        if has_all_china_prices:
            st.metric("国内总价", f"{total_china_price:,.0f}人民币")
        else:
            st.metric("国内总价", "信息不完整")

    with col4:
        if discount_rate:
            st.metric("折扣率", f"{discount_rate}%")
            st.write(f"计算公式: {cny_price:,.0f}/{total_china_price:,.0f} = {discount_rate}%")
        else:
            st.metric("折扣率", "无法计算")
            if not has_all_china_prices:
                st.warning("部分产品缺少国内售价信息")
    # 显示使用的优惠
    st.write("**使用的优惠:**")
    for discount in result['selected_discounts']:
        st.write(f"✅ {discount}")

    # # 人民币换算
    # cny_price = convert_krw_to_cny(result['final_payment'])
    # st.write(f"**人民币价格:** {cny_price:,.0f}元")
def main():
    # 获取汇率信息
    rate_info = get_exchange_rate()

    # 主标题和汇率信息在同一行
    st.title("🏔️ 始祖鸟查货系统")
    if rate_info:
        st.session_state.exchange_rate_info = rate_info  # 保存供其他模块使用
        # 使用醒目的方式显示
        st.success(f"💱 实时汇率: {rate_info}")
    else:
        st.warning("⚠️ 今日汇率信息暂不可用")
        st.session_state.exchange_rate_info = None

    # 初始化session_state（移到函数内部）
    if "step_history" not in st.session_state:
        st.session_state.step_history = ["start"]

    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 产品查询", "⭐ 收藏产品", "🛒 购买计划", "🗑️ 缓存管理"])

    with tab1:
        show_product_query_tab()

    with tab2:
        show_favorites_tab()
    
    with tab3:
        show_purchase_plan_tab()
    
    with tab4:
        show_cache_management_tab()


if __name__ == "__main__":
    # 初始化session_state
    # if "current_step" not in st.session_state:
    #     st.session_state.current_step = "start"

    main()