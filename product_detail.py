import requests
import re
from lxml import html
from cache_manager import product_cache  # 新增导入
import streamlit as st
import json # Added for extract_variant_json_from_html
from bs4 import BeautifulSoup # Added for extract_variant_json_from_html

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


def parse_hex_list(hex_string):
    """从HEX字符串解析出HEX值列表（支持单色和混合色）"""
    if not hex_string:
        return []
    
    # 如果已经是列表，直接处理
    if isinstance(hex_string, list):
        # 处理列表中的各种格式
        result = []
        for item in hex_string:
            if item:  # 非空检查
                if isinstance(item, str):
                    item = item.strip()
                    if item.startswith('#'):
                        result.append(item)
                else:
                    # 尝试转换为字符串
                    item_str = str(item).strip()
                    if item_str.startswith('#'):
                        result.append(item_str)
        print(f"[DEBUG parse_hex_list] 输入是列表: {hex_string} => 输出: {result}")
        return result
    
    # 处理字符串格式的HEX值
    if isinstance(hex_string, str):
        # 先移除所有转义的引号（来自正则提取）
        hex_string = hex_string.replace('\\"', '"').replace('\\', '')
        # 然后移除所有引号
        hex_string = hex_string.replace('"', '').replace("'", '')
        
        # 处理多个HEX值用逗号或其他分隔符分隔的情况
        hex_values = [h.strip() for h in hex_string.split(',') if h.strip() and h.strip().startswith('#')]
        result = hex_values if hex_values else ([hex_string] if hex_string.startswith('#') else [])
        print(f"[DEBUG parse_hex_list] 输入是字符串: {hex_string} => 输出: {result}")
        return result
    
    print(f"[DEBUG parse_hex_list] 未知类型 {type(hex_string)}: {hex_string}")
    return []


@st.cache_data(ttl=3600)
def extract_variant_json_from_html(html_content):
    """
    从HTML中提取产品变体的JSON数据
    JSON数据通常在script标签中，格式如：
    var variantData = {...}
    或在data属性中
    """
    try:
        # 方法1：查找script标签中的JSON数据（常见模式）
        # 查找包含variant或option数据的JSON对象
        json_patterns = [
            r'var\s+\w+\s*=\s*(\{.*?"options".*?\});',  # var xxx = {...};
            r'"options"\s*:\s*(\[.*?\]),',  # "options": [...],
            r'data-variant=\'(.*?)\'',  # data-variant attribute
            r'<script[^>]*>var\s+\w+\s*=\s*(\{.*?\});',  # script tag with var
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            if matches:
                for match in matches:
                    try:
                        # 尝试解析JSON
                        if isinstance(match, str):
                            # 修复JSON格式（移除转义符）
                            json_str = match.replace('\\"', '"').replace('\\/', '/')
                            # 如果不是有效的JSON对象/数组，跳过
                            if json_str.startswith('[') or json_str.startswith('{'):
                                data = json.loads(json_str)
                                if isinstance(data, (dict, list)):
                                    return data
                    except json.JSONDecodeError:
                        continue
        
        # 方法2：使用BeautifulSoup查找隐藏的script标签
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 查找所有script标签
        for script in soup.find_all('script'):
            script_content = script.string
            if script_content and ('variant' in script_content.lower() or 'option' in script_content.lower()):
                try:
                    # 尝试提取JSON部分
                    json_match = re.search(r'\{.*\}', script_content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0).replace('\\"', '"')
                        data = json.loads(json_str)
                        return data
                except:
                    continue
        
        return None
        
    except Exception as e:
        print(f"提取variant JSON失败: {e}")
        return None


@st.cache_data(ttl=3600)
def get_product_variants(detail_url):
    """获取产品的颜色和尺码选项（从JSON数据提取）"""
    try:
        html_content = fetch_html_from_url(detail_url)
        if not html_content:
            return None, None

        # 初始化变量
        color_options = []
        size_options = []

        # 首先尝试从HTML中提取完整的JSON数据
        variant_json = extract_variant_json_from_html(html_content)
        
        if variant_json:
            try:
                # 解析JSON中的options数据
                options = variant_json.get('options', []) if isinstance(variant_json, dict) else variant_json
                
                # 遍历options数组，color_id为0是颜色，color_id为1是尺码
                for option in options:
                    if isinstance(option, dict):
                        parent_ids = option.get('parent_ids', [])
                        value = option.get('value', '')
                        
                        # 颜色选项：parent_ids为[0]
                        if parent_ids == [0]:
                            hex_list = parse_hex_list(option.get('color_chips', []))
                            color_item = {
                                "id": option.get('id', ''),
                                "name": value,
                                "hex_list": hex_list,
                                "image_chip": option.get('image_chip', '')
                            }
                            print(f"[DEBUG COLOR] 颜色名称: {value}, color_chips原始: {option.get('color_chips', [])}, 解析后hex_list: {hex_list}")
                            color_options.append(color_item)
                        
                        # 尺码选项：parent_ids为[0, color_id]（任何color_id）
                        elif len(parent_ids) == 2 and parent_ids[0] == 0:
                            if value not in size_options:
                                size_options.append(value)
                
                if color_options and size_options:
                    return color_options, size_options
                    
            except Exception as e:
                print(f"JSON解析失败: {e}")

        # 回退方案：使用正则表达式直接从HTML中提取
        try:
            # 提取颜色选项（包括image_chip）
            # 改进正则：捕获整个color_chips数组中的所有HEX值
            color_matches = re.findall(
                r'\\"id\\":(\d+),\\"parent_ids\\":\[0\],\\"sale_state\\":\\".+?\\",\\"value\\":\\"(.+?)\\",\\"adjust_price\\":0,\\"color_chips\\":\[(.*?)\],\\"image_chip\\":\\"([^"]+)\\"',
                html_content
            )
            if color_matches:
                color_options = [
                    {
                        "id": match[0],
                        "name": match[1],
                        "hex_list": parse_hex_list(match[2]),  # 使用parse_hex_list处理
                        "image_chip": match[3]
                    }
                    for match in color_matches
                ]
            
            # 备用的正则表达式（处理不同格式）
            if not color_options:
                color_matches = re.findall(
                    r'"id":(\d+),"parent_ids":\[0\],"sale_state":"[^"]*","value":"([^"]+)"[^}]*"color_chips":\[(.*?)\][^}]*"image_chip":"([^"]+)"',
                    html_content
                )
                if color_matches:
                    color_options = [
                        {
                            "id": match[0],
                            "name": match[1],
                            "hex_list": parse_hex_list(match[2]),  # 使用parse_hex_list处理
                            "image_chip": match[3]
                        }
                        for match in color_matches
                    ]
            
            # 第三个备用正则（提取颜色HEX值，格式：颜色名称对应的HEX或HEX列表）
            if not color_options:
                # 查找所有单独的颜色芯片HEX值
                hex_matches = re.findall(
                    r'\\"color_chips\\":\[(.*?)\]',
                    html_content
                )

                # 同时提取颜色名称
                if hex_matches:
                    color_name_matches = re.findall(
                        r'\\"value\\":\\"([^"]+?)\\",\\"adjust_price\\":\d+,\\"color_chips\\":\[',
                        html_content
                    )
                    if color_name_matches:
                        # 配对HEX和颜色名称
                        color_options = [
                            {
                                "id": f"color_{i}",
                                "name": color_name_matches[i] if i < len(color_name_matches) else f"Color {i}",
                                "hex_list": parse_hex_list(hex_matches[i]),
                                "image_chip": ""
                            }
                            for i in range(min(len(hex_matches), len(color_name_matches)))
                        ]
        except Exception as e:
            print(f"颜色正则提取失败: {e}")

        # 尺码选项提取
        try:
            size_matches = re.findall(
                r'\\"parent_ids\\":\[0,\d+\],\\"sale_state\\":\\"\w+\\",\\"value\\":\\"([^"]+?)\\",\\"adjust_price\\":',
                html_content
            )
            if size_matches:
                seen = set()
                size_options = []
                for size in size_matches:
                    if size not in seen:
                        seen.add(size)
                        size_options.append(size)
        except Exception as e:
            print(f"尺码提取失败: {e}")

        return color_options, size_options

    except Exception as e:
        print(f"产品变体获取失败: {e}")
        return [], []


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