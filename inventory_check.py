import requests
import json
# 确保新函数可以被其他模块导入
__all__ = [
    'get_store_region', 'map_region_to_key', 'simplify_store_name',
    'translate_store_name', 'get_stock_status', 'query_stock_by_product_id',
    'get_inventory_matrix_transposed', 'calculate_stock_status_distribution',
    'calculate_region_heatmap', 'calculate_product_depth_stats',
    'calculate_enhanced_inventory_stats',
    'calculate_key_store_analysis'

]

# 店铺名称翻译字典
store_translation = {
    "아크테릭스 롯데백화점 본점": "始祖鸟乐天百货总店",
    "아크테릭스 롯데백화점 평촌极": "始祖鸟乐天百货平村店",
    "아크테릭스 플래그십 스토어 강남": "始祖鸟旗舰店江南",
    "아크테릭스 플래그십 스토어 대구수성": "始祖鸟旗舰店大邱寿城",
    "아크테릭스 도봉산점": "始祖鸟道峰山店",
    "아크테릭스 봉무점": "始祖鸟奉武店",
    "아크테릭스 부산점": "始祖鸟釜山店",
    "아크테릭스 여주프리미엄빌리지점": "始祖鸟骊州Premium Village店",
    "아크테릭스 일산점": "始祖鸟一山店",
    "아크테릭스 종로점": "始祖鸟钟路店",
    "아크테릭스 롯데프리미엄아울렛 의왕점": "始祖鸟乐天Premium Outlet义王店",
    "아크테릭스 롯데프리미엄아울렛 동부산점": "始祖鸟乐天Premium Outlet东釜山店",
    "아크테릭스 롯데极프리미엄아울렛 이천점": "始祖鸟乐天Premium Outlet利川店",
    "아크테릭스 신세계사이먼 프리미엄 아울렛 파주점": "始祖鸟新世界Simon Premium Outlet坡州店",
    "아크테릭스 신세계사이먼 프리미엄 아울렛 제주점": "始祖鸟新世界Simon Premium Outlet济州店",
    "아极테릭스 현대프리미엄아울렛 김포점": "始祖鸟现代Premium Outlet金浦店",
    "아크테릭스 현대프리미엄아울렛 송도점": "始祖鸟现代Premium Outlet松岛店",
    "아크테릭스 현대프리미엄아울렛 대전점": "始祖鸟现代Premium Outlet大田店",
    "아크테릭스 신세계사이먼 프리미엄 아울렛 시흥점": "始祖鸟新世界Simon Premium Outlet始兴店",
    "아크테릭스 현대프리미엄아울렛 SPACE 1": "始祖鸟现代Premium Outlet SPACE 1",
    "아크테릭스 신세계사이먼 프리미엄 아울렛 부산점": "始祖鸟新世界Simon Premium Outlet釜山店",
    "아크테릭스 롯데프리미엄아울렛 파주점": "始祖鸟乐天Premium Outlet坡州店",
    "아크테릭스 플래그십 스토어 롯데월드몰": "始祖鸟旗舰店乐天世界购物中心",
    "아크테릭스 스타필드 코엑스몰점": "始祖鸟Starfield COEX购物中心店",
    "아크테릭스 롯데백화점 동탄점": "始祖鸟乐天百货东滩店",
    "아크테릭스 대구신세계": "始祖鸟大邱新世界",
    "아크테릭스 롯데백화점 대전점": "始祖鸟乐极百货大田店",
    "아크테릭스 롯데백화점 노원점": "始祖鸟乐天百货芦原店",
    "아크테릭스 현대백화점 판교점": "始祖鸟现代百货板桥店",
    "아크테릭스 광주신세계": "始祖鸟光州新世界",
    "아크테릭스 롯데백화점 수원점": "始祖鸟乐天百货水原店",
    "아크테릭스 롯데백화점 광복점": "始祖鸟乐天百货光复店",
    "아크테릭스 신세계백화점 센텀시티": "始祖鸟新世界百货Centum City店",
    "아크테릭스 롯데백화점 울산점": "始祖鸟乐天百货蔚山店",
    "아크테릭스 신세계백화점 본점": "始祖鸟新世界百货总店",
    "아크테릭스 신세계백화점 강남점": "始祖鸟新世界百货江南店",
    "아크테릭스 롯데백화점 부산본점": "始祖鸟乐天百货釜山总店",
    "아크테릭스 롯데백화점 전주점": "始祖鸟乐天百货全州店",
    "아크테릭스 더현대 서울": "始祖鸟The Hyundai首尔",
    "아크테릭스 롯데백화점 영등포점": "始祖鸟乐天百货永登浦店",
    "아크테릭스 현대백화점 목동极": "始祖鸟现代百货木洞店",
    "아크테릭스 대전신세계 Art&Science": "始祖鸟大田新世界Art&Science",
    "아크테릭스 롯데백화점 잠실점": "始祖鸟乐天百货蚕室店",
    "아크테릭스 신세계 사우스시티": "始祖鸟新世界South City",
    "아크테릭스 현대백화점 울산점": "始祖鸟现代百货蔚山店",
    "아크테릭스 현대백화점 충청점": "始祖鸟现代百货忠清店",
    "아크테릭스 무등산점": "始祖鸟无等山店",
    "아크테릭스 덕소삼패점": "始祖鸟德沼三牌店",
    "아크테릭스 중구점": "始祖鸟中区店",
    "아크테릭스 진주점": "始祖鸟晋州店",
    "아크테릭스 안산점": "始祖鸟安山店",
    "아크테릭스 롯데백화점 인천점": "始祖鸟乐天百货仁川店",
    "아크테릭스 현대프리미엄아울렛 김포점": "始祖鸟现代Premium Outlet金浦店",
    "아크테릭스 롯데백화점 평촌점": "始祖鸟乐天百货平村店",
    "아크테릭스 현대백화점 목동점": "始祖鸟现代百货木洞店",
    "아크테릭스 롯데프리미엄아울렛 이천점": "始祖鸟乐天Premium Outlet利川店"
}

# 硬编码的店铺-区域映射表（直接复制 store_region_mapping.txt 的内容）
STORE_REGION_MAPPING = {
    "始祖鸟乐天百货总店": "首尔城区",
    "始祖鸟乐天百货平村店": "京畿道地区",
    "始祖鸟旗舰店江南": "首尔城区",
    "始祖鸟旗舰店大邱寿城": "大邱",
    "始祖鸟道峰山店": "京畿道地区",
    "始祖鸟釜山店": "釜山",
    "始祖鸟骊骊州Premium Village店": "京畿道地区",
    "始祖鸟一山店": "京畿道地区",
    "始祖鸟钟路店": "首尔城区",
    "始祖鸟乐天Premium Outlet义王店": "京畿道地区",
    "始祖鸟乐天Premium Outlet东釜山店": "釜山",
    "始祖鸟新世界Simon Premium Outlet坡州店": "京畿道地区",
    "始祖鸟新世界Simon Premium Outlet济州店": "京畿道地区",
    "始祖鸟现代Premium Outlet金浦店": "京畿道地区",
    "始祖鸟现代Premium Outlet松岛店": "京畿道地区",
    "始祖鸟现代Premium Outlet大田店": "京畿道地区",
    "始祖鸟新世界Simon Premium Outlet始兴店": "京畿道地区",
    "始祖鸟现代Premium Outlet SPACE 1": "京畿道地区",
    "始祖鸟新世界Simon Premium Outlet釜山店": "釜山",
    "始祖鸟乐天Premium Outlet坡州店": "京畿道地区",
    "始祖鸟旗舰店乐天世界购物中心": "首尔城区",
    "始祖鸟Starfield COEX购物中心店": "首尔城区",
    "始祖鸟乐天百货东滩店": "京畿道地区",
    "始祖鸟大邱新世界": "大邱",
    "始祖鸟乐极百货大田店": "京畿道地区",
    "始祖鸟乐天百货芦原店": "京畿道地区",
    "始祖鸟现代百货板桥店": "京畿道地区",
    "始祖鸟乐天百货水原店": "京畿道地区",
    "始祖鸟乐天百货光复店": "釜山",
    "始祖鸟新世界百货Centum City店": "釜山",
    "始祖鸟新世界百货总店": "首尔城区",
    "始祖鸟新世界百货江南店": "首尔城区",
    "始祖鸟乐天百货釜山总店": "釜山",
    "始祖鸟The Hyundai首尔": "首尔城区",
    "始祖鸟乐天百货永登浦店": "首尔城区",
    "始祖鸟现代百货木洞店": "首尔城区",
    "始祖鸟乐天百货蚕室店": "首尔城区",
    "始祖鸟新世界South City": "京畿道地区",
    "始祖鸟德沼三牌店": "京畿道地区",
    "始祖鸟安山店": "京畿道地区",
    "始祖鸟乐天百货仁川店": "京畿道地区",
    "始祖鸟现代Premium Outlet金浦店": "首尔城区",
    "始祖鸟乐天百货平村店": "京畿道地区",
    "始祖鸟现代百货木洞店": "首尔城区",
    "始祖鸟乐天Premium Outlet利川店": "京畿道地区"
}

def get_store_region(store_name):
    """根据店铺名称判断所属区域（严格依赖硬编码的映射表）"""
    return STORE_REGION_MAPPING.get(store_name)  # 不在映射表中的店铺返回 None

def map_region_to_key(region):
    """将店铺区域映射到区域分类键"""
    if region == "首尔城区":
        return "首尔圈"
    elif region == "京畿道地区":
        return "京畿道圈"
    elif region == "釜山":
        return "釜山圈"
    elif region == "大邱":
        return "大邱圈"
    return None

def simplify_store_name(store_name):
    """简化店铺名称（去掉'始祖鸟'前缀）"""
    if store_name.startswith("始祖鸟"):
        return store_name[3:]  # 去掉前3个字符
    return store_name
def translate_store_name(korean_name):
    """翻译店铺名称"""
    return store_translation.get(korean_name, korean_name)


def get_stock_status(stock):
    """获取库存状态"""
    if stock is None:
        return "❌❌ 无库存"
    try:
        stock_count = int(stock)
        if stock_count > 0:
            return f"✅ 有库存 ({stock_count}件)"
        else:
            return "❌❌ 无库存"
    except (ValueError, TypeError):
        return "❓❓ 库存信息异常"


def query_stock_by_product_id(product_id):
    """根据产品ID查询库存（保持原有函数不变，用于回退和单个查询）"""
    url = f"https://api.arcteryx.co.kr/api/stores?limit=0&page=1&local_code=&search_keyword=&x=&y=&product_option_id={product_id}&orderby=store_sort%7Casc"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            return data["data"]["rows"]
        else:
            return []

    except Exception as e:
        print(f"库存查询失败: {e}")
        return []


def get_inventory_matrix_transposed(favorites_list):
    """转置库存矩阵：店铺×产品（并发优化版）"""
    if not favorites_list:
        return {}

    # 提取所有SKU ID用于批量查询
    product_ids = [favorite['sku'] for favorite in favorites_list]

    print(f"开始处理 {len(product_ids)} 个产品的库存查询...")

    # 根据产品数量动态调整并发数（优化版：提高并发度）
    if len(product_ids) <= 3:
        max_workers = 2  # 产品少时使用较低并发
    elif len(product_ids) <= 10:
        max_workers = 4  # 中等数量使用中等并发
    else:
        max_workers = 8  # 产品多时使用更高并发

    # 使用并发查询
    batch_results = batch_query_stock_concurrent(
        product_ids,
        max_workers=max_workers,
        timeout_per_request=12  # 稍微延长超时时间
    )

    # 构建产品键映射
    product_key_mapping = {}
    for favorite in favorites_list:
        product_key = f"{favorite['product_model']} {favorite['color']} {favorite['size']}"
        product_key_mapping[favorite['sku']] = product_key

    # 转换数据格式
    inventory_data = {}
    for product_id, stores_data in batch_results.items():
        if not stores_data:
            continue

        product_key = product_key_mapping.get(product_id)
        if not product_key:
            continue

        # 处理每个店铺的库存数据
        for store_data in stores_data:
            store_name = translate_store_name(store_data.get("store_name", ""))
            if store_name not in inventory_data:
                inventory_data[store_name] = {}

            stock_count = store_data.get("usable_stock", 0)
            inventory_data[store_name][product_key] = stock_count

    print(f"库存矩阵构建完成: 共 {len(inventory_data)} 个店铺")
    return inventory_data
def calculate_stock_status_distribution(inventory_matrix):
    """计算库存状态分布"""
    stock_stats = {
        "高库存店铺": {"count": 0, "percentage": 0},
        "低库存店铺": {"count": 0, "percentage": 0},
        "无库存店铺": {"count": 0, "percentage": 0}
    }

    total_stores = len(inventory_matrix)
    if total_stores == 0:
        return stock_stats

    for store_data in inventory_matrix.values():
        has_stock = False
        low_stock = False

        for stock in store_data.values():
            if stock and str(stock).isdigit():
                stock_count = int(stock)
                if stock_count > 0:
                    has_stock = True
                    if 1 <= stock_count <= 2:
                        low_stock = True
                    break

        if has_stock:
            if low_stock:
                stock_stats["低库存店铺"]["count"] += 1
            else:
                stock_stats["高库存店铺"]["count"] += 1
        else:
            stock_stats["无库存店铺"]["count"] += 1

    # 计算百分比
    for key in stock_stats:
        stock_stats[key]["percentage"] = round((stock_stats[key]["count"] / total_stores) * 100, 2)

    return stock_stats


def calculate_region_heatmap(inventory_matrix):
    """计算区域库存热力图数据"""
    region_stats = {
        "首尔圈": {"count": 0, "percentage": 0, "inventory": 0},
        "京畿道圈": {"count": 0, "percentage": 0, "inventory": 0},
        "釜山圈": {"count": 0, "percentage": 0, "inventory": 0},
        "大邱圈": {"count": 0, "percentage": 0, "inventory": 0},
        "其他地区": {"count": 0, "percentage": 0, "inventory": 0}
    }

    total_stores = len(inventory_matrix)
    if total_stores == 0:
        return region_stats

    for store_name, store_data in inventory_matrix.items():
        # 获取店铺区域
        region = get_store_region(store_name)

        # 确定区域分类
        if region == "首尔城区":
            region_key = "首尔圈"
        elif region == "京畿道地区":
            region_key = "京畿道圈"
        elif region == "釜山":
            region_key = "釜山圈"
        elif region == "大邱":
            region_key = "大邱圈"
        else:
            region_key = "其他地区"

        # 统计店铺数量
        region_stats[region_key]["count"] += 1

        # 统计库存总量
        total_inventory = 0
        for stock in store_data.values():
            if stock and str(stock).isdigit():
                total_inventory += int(stock)
        region_stats[region_key]["inventory"] += total_inventory

    # 计算百分比
    for key in region_stats:
        if total_stores > 0:
            region_stats[key]["percentage"] = round((region_stats[key]["count"] / total_stores) * 100, 2)

    return region_stats


def calculate_product_depth_stats(favorites_list, inventory_matrix):
    """计算产品深度库存统计（包含店铺详情）"""
    product_stats = {}

    for favorite in favorites_list:
        product_key = f"{favorite['product_model']} {favorite['color']} {favorite['size']}"

        product_stats[product_key] = {
            "total_inventory": 0,
            "stores_with_stock": 0,
            "region_distribution": {
                "首尔圈": {"total": 0, "stores": []},
                "京畿道圈": {"total": 0, "stores": []},
                "釜山圈": {"total": 0, "stores": []},
                "大邱圈": {"total": 0, "stores": []}
            }
        }

        # 统计每个店铺的库存
        for store_name, products in inventory_matrix.items():
            if product_key in products:
                stock = products[product_key]
                if stock and str(stock).isdigit():
                    stock_count = int(stock)
                    if stock_count > 0:
                        # 更新总统计
                        product_stats[product_key]["total_inventory"] += stock_count
                        product_stats[product_key]["stores_with_stock"] += 1

                        # 确定区域
                        region = get_store_region(store_name)
                        region_key = map_region_to_key(region)

                        if region_key:
                            # 简化店铺名称
                            simplified_name = simplify_store_name(store_name)

                            # 添加店铺详情
                            product_stats[product_key]["region_distribution"][region_key]["total"] += stock_count
                            product_stats[product_key]["region_distribution"][region_key]["stores"].append({
                                "store_name": simplified_name,
                                "stock": stock_count
                            })

        # 对每个区域的店铺按库存量降序排序
        for region_key in product_stats[product_key]["region_distribution"]:
            product_stats[product_key]["region_distribution"][region_key]["stores"].sort(
                key=lambda x: x["stock"], reverse=True
            )

    return product_stats


def calculate_key_store_analysis(favorites_list, inventory_matrix):
    """计算重点关注店铺库存分析"""
    # 重点关注店铺列表
    key_stores = [
        "始祖鸟新世界百货总店", "始祖鸟新世界百货江南店", "始祖鸟新世界百货Centum City店",
        "始祖鸟乐天百货总店", "始祖鸟旗舰店江南", "始祖鸟釜山店",
        "始祖鸟骊州Premium Village店", "始祖鸟The Hyundai首尔", "始祖鸟旗舰店大邱寿城",
        "始祖鸟现代百货板桥店", "始祖鸟钟路店"
    ]

    result = {}

    # 为每个重点关注店铺创建产品库存列表
    for store_name in key_stores:
        if store_name in inventory_matrix:
            store_products = []

            # 遍历所有收藏产品
            for favorite in favorites_list:
                product_key = f"{favorite['product_model']} {favorite['color']} {favorite['size']}"

                if product_key in inventory_matrix[store_name]:
                    stock = inventory_matrix[store_name][product_key]
                    if stock and str(stock).isdigit():
                        stock_count = int(stock)
                        if stock_count > 0:
                            # 有库存：显示数量
                            display_text = f"{product_key}({stock_count}件)"
                        else:
                            # 无库存：显示"无"
                            display_text = f"{product_key}(无)"
                    else:
                        # 库存信息异常或无库存
                        display_text = f"{product_key}(无)"
                else:
                    # 店铺中没有该产品的记录
                    display_text = f"{product_key}(无)"

                store_products.append({
                    "product_key": product_key,
                    "display_text": display_text,
                    "stock_count": int(stock) if stock and str(stock).isdigit() else 0
                })

            # 按库存量降序排序
            store_products.sort(key=lambda x: x["stock_count"], reverse=True)
            result[store_name] = store_products
        else:
            # 如果店铺不在库存矩阵中，创建空列表
            result[store_name] = []

    return result
def calculate_enhanced_inventory_stats(inventory_matrix):
    """计算增强版库存统计（替换原有的calculate_inventory_stats）"""
    return {
        "stock_status": calculate_stock_status_distribution(inventory_matrix),
        "region_heatmap": calculate_region_heatmap(inventory_matrix)
    }


import concurrent.futures
import time
from typing import List, Dict, Any


def batch_query_stock_concurrent(product_ids: List[str], max_workers: int = 3, timeout_per_request: int = 10) -> Dict[
    str, Any]:
    """
    并发批量查询库存（稳定可靠版本）

    Args:
        product_ids: 产品ID列表
        max_workers: 最大并发数（默认3，保守设置）
        timeout_per_request: 单个请求超时时间（秒）

    Returns:
        查询结果字典 {product_id: stock_data}
    """
    results = {}
    failed_queries = []

    # 参数验证
    if not product_ids:
        return {}

    if max_workers > 5:  # 安全限制，最大并发数不超过5
        max_workers = 5

    print(f"开始并发查询 {len(product_ids)} 个产品，并发数: {max_workers}")
    start_time = time.time()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有查询任务
            future_to_id = {
                executor.submit(query_stock_by_product_id, pid): pid
                for pid in product_ids
            }

            # 处理完成的任务
            for future in concurrent.futures.as_completed(future_to_id):
                product_id = future_to_id[future]
                try:
                    # 设置单个请求超时
                    stock_data = future.result(timeout=timeout_per_request)
                    if stock_data:
                        results[product_id] = stock_data
                        print(f"✓ 成功查询产品 {product_id}")
                    else:
                        failed_queries.append((product_id, "返回空数据"))
                        print(f"⚠ 产品 {product_id} 返回空数据")

                except concurrent.futures.TimeoutError:
                    failed_queries.append((product_id, "请求超时"))
                    print(f"⏰ 产品 {product_id} 查询超时")
                except Exception as e:
                    failed_queries.append((product_id, str(e)))
                    print(f"❌ 产品 {product_id} 查询失败: {e}")

    except Exception as e:
        print(f"并发查询执行器异常: {e}")
        # 回退到串行查询
        return fallback_serial_query(product_ids)

    # 统计信息
    end_time = time.time()
    duration = round(end_time - start_time, 2)
    success_rate = len(results) / len(product_ids) * 100 if product_ids else 0

    print(f"并发查询完成: 成功 {len(results)}/{len(product_ids)} "
          f"({success_rate:.1f}%), 耗时 {duration}秒")

    if failed_queries:
        print(f"失败查询: {failed_queries}")

    return results


def fallback_serial_query(product_ids: List[str]) -> Dict[str, Any]:
    """
    回退串行查询（当并发查询失败时使用）
    """
    print("回退到串行查询模式...")
    results = {}

    for i, pid in enumerate(product_ids, 1):
        try:
            # 添加延迟避免请求过快
            if i > 1:
                time.sleep(0.5)

            stock_data = query_stock_by_product_id(pid)
            if stock_data:
                results[pid] = stock_data
                print(f"串行查询进度: {i}/{len(product_ids)} - ✓ {pid}")
            else:
                print(f"串行查询进度: {i}/{len(product_ids)} - ⚠ {pid} (空数据)")

        except Exception as e:
            print(f"串行查询进度: {i}/{len(product_ids)} - ❌ {pid} (失败: {e})")

    return results


def safe_batch_query(favorites_list, max_workers=None):
    """
    安全的批量查询入口函数
    包含各种边界条件检查和保护措施
    """
    # 参数检查
    if not favorites_list:
        print("警告: 传入空收藏列表")
        return {}

    # 验证SKU格式
    valid_favorites = []
    for fav in favorites_list:
        sku = fav.get('sku', '').strip()
        if sku and sku.isdigit():  # 基本格式验证
            valid_favorites.append(fav)
        else:
            print("跳过无效SKU: " + fav.get('product_model', '未知') + " - SKU: " + str(sku))

    if not valid_favorites:
        print("错误: 没有有效的SKU可供查询")
        return {}

    # 限制最大查询数量（安全限制）
    MAX_QUERY_LIMIT = 50
    if len(valid_favorites) > MAX_QUERY_LIMIT:
        print("警告: 查询数量超过限制 " + str(MAX_QUERY_LIMIT) + "，进行截断")
        valid_favorites = valid_favorites[:MAX_QUERY_LIMIT]

    # 动态计算并发数（保守策略）
    if max_workers is None:
        if len(valid_favorites) <= 2:
            max_workers = 1
        elif len(valid_favorites) <= 8:
            max_workers = 2
        else:
            max_workers = 3

    print("安全查询配置: " + str(len(valid_favorites)) + "个产品, 并发数: " + str(max_workers))

    # 执行查询
    return get_inventory_matrix_transposed(valid_favorites)