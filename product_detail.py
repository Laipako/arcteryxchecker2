import requests
import re
from lxml import html
from cache_manager import product_cache  # 新增导入
import streamlit as st

@st.cache_data(ttl=3600)
def fetch_html_from_url(url):
    """从URL获取HTML内容（支持缓存）"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        html_content = response.text
        return html_content

    except Exception as e:
        print(f"URL请求失败: {e}")
        return None


@st.cache_data(ttl=3600)
def extract_product_details(detail_url):
    """提取产品详情页的描述、年份信息和准确型号（支持缓存）"""
    try:
        html_content = fetch_html_from_url(detail_url)
        if not html_content:
            return None

        # 使用正则表达式提取年份款式信息
        year_match = re.search(r'\\"season\\":\\"(\d+\/\w+)\\"', html_content)
        year_info = year_match.group(1) if year_match else "未找到年份信息"

        # 提取产品描述
        tree = html.fromstring(html_content)
        description_elements = tree.xpath('//*[@id="content-wrap"]/div[2]/div[2]/div/div[1]/div/div[2]/p/text()')
        description = " ".join(desc.strip() for desc in description_elements if desc.strip())
        description = re.sub(r'\s+', ' ', description).strip()

        # 提取准确型号（Beta SL Jacket）
        exact_model_elements = tree.xpath('//*[@id="content-wrap"]/div[3]/p[1]/text()')
        exact_model = exact_model_elements[0].strip() if exact_model_elements else "未找到型号信息"

        result = {
            "description": description,
            "year_info": year_info,
            "exact_model": exact_model
        }

        return result

    except Exception as e:
        print(f"详情页解析失败: {e}")
        return None


def extract_options(html_content, xpath):
    """从HTML中提取选项"""
    try:
        tree = html.fromstring(html_content)
        elements = tree.xpath(xpath)
        if elements:
            text = elements[0].text_content().strip()
            for sep in [',', '，', ' ', '、', '/']:
                if sep in text:
                    return [opt.strip() for opt in text.split(sep) if opt.strip()]
            return [text] if text else []
        return []
    except Exception:
        return []


@st.cache_data(ttl=3600)
def get_product_variants(detail_url):
    """获取产品的颜色和尺码选项（支持缓存）"""
    try:
        html_content = fetch_html_from_url(detail_url)
        if not html_content:
            return None, None

        # 初始化变量（修复Unresolved reference错误）
        color_options = []
        size_options = []

        # 修改后的正则表达式（支持#/##前缀）
        try:
            color_matches = re.findall(
                r'\\"id\\":(\d+),\\"parent_ids\\":\[0\],\\"sale_state\\":\\".+?\\",\\"value\\":\\"(.+?)\\",\\"adjust_price\\":0,\\"color_chips\\":\[\\"(.+?)\\"\]',
                html_content
            )
            color_options = [
                {
                    "id": match[0],
                    "name": match[1],
                    "hex": match[2]
                }
                for match in color_matches
            ]
        except Exception as e:
            print(f"颜色提取失败: {e}")
            # 回退到旧方案
            color_xpath = '//*[@id="content-wrap"]/div[5]/div/div[2]/div[2]'
            color_text_elements = html.fromstring(html_content).xpath(color_xpath)
            if color_text_elements:
                color_text = color_text_elements[0].text_content()
                color_options = [{"name": c.strip()} for c in color_text.split(',') if c.strip()]

        # 尺码选项提取（修复：确保变量正确初始化）
        try:
            size_xpath = '//*[@id="content-wrap"]/div[5]/div/div[3]/div[2]'
            size_options = extract_options(html_content, size_xpath)
        except Exception as e:
            print(f"尺码提取失败: {e}")
            size_options = []  # 确保有默认值

        return color_options, size_options

    except Exception as e:
        print(f"产品变体获取失败: {e}")
        return [], []  # 返回空列表而不是None


@st.cache_data(ttl=3600)
def get_sku_info(detail_url, color_value, size_value):
    """获取特定颜色和尺码的SKU信息（支持缓存）"""
    try:
        html_content = fetch_html_from_url(detail_url)
        if not html_content:
            return None

        # 查找颜色ID
        escaped_color = re.escape(color_value)
        pattern_color = fr'\\"id\\":(\d+),\\"parent_ids\\":\[0\],\\"sale_state\\":\\"\w+\\",\\"value\\":\\"{escaped_color}\\"'
        match_color = re.search(pattern_color, html_content, re.DOTALL)

        if not match_color:
            pattern_color2 = fr'"id":(\d+),"parent_ids":\[0\],"sale_state":"\w+","value":"{escaped_color}"'
            match_color = re.search(pattern_color2, html_content, re.DOTALL)
            if not match_color:
                return None

        color_id = match_color.group(1)

        # 查找尺码信息
        escaped_size = re.escape(size_value)
        pattern_sku = fr'\\"id\\":(\d+),\\"parent_ids\\":\[0,{color_id}\],\\"sale_state\\":\\"\w+\\",\\"value\\":\\"{escaped_size}\\",\\"adjust_price\\":(\d+),\\"sell_price\\":(\d+),\\"is_orderable\\":\w+,\\"stock\\":(\d+),\\"images\\":\[\]'
        match_sku = re.search(pattern_sku, html_content, re.DOTALL)

        if not match_sku:
            pattern_sku2 = fr'"id":(\d+),"parent_ids":\[0,{color_id}\],"sale_state":"\w+","value":"{escaped_size}","adjust_price":(\d+),"sell_price":(\d+),"is_orderable":\w+,"stock":(\d+),"images":\[\]'
            match_sku = re.search(pattern_sku2, html_content, re.DOTALL)

        if match_sku:
            result = {
                "sku_id": match_sku.group(1),
                "adjust_price": match_sku.group(2),
                "sell_price": match_sku.group(3),
                "stock": match_sku.group(4)
            }

            return result

        return None

    except Exception as e:
        print(f"SKU信息提取失败: {e}")
        return None


# 新增：缓存管理函数
def clear_product_detail_cache():
    """清除产品详情相关缓存"""
    cache_keys = [key for key in st.session_state.keys()
                  if key.startswith(('html_', 'product_details_', 'product_variants_', 'sku_info_'))]
    for key in cache_keys:
        del st.session_state[key]