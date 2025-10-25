#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试图片提取功能"""

from product_detail import extract_product_images, filter_images_by_color

def test_image_extraction():
    """测试图片提取"""
    test_url = 'https://arcteryx.co.kr/products/view/62399?sc=100'
    
    print("=" * 60)
    print("测试图片提取功能")
    print("=" * 60)
    print(f"\n🔍 测试URL: {test_url}\n")
    
    # 测试图片提取
    result = extract_product_images(test_url)
    
    if result:
        print("\n✓ 成功提取图片数据！")
        print(f"  - 主图: {result.get('main_image', '无')}")
        print(f"  - 总数: {len(result.get('images', []))} 张")
        
        if result.get('images'):
            print(f"\n  前3张图片URL:")
            for i, img in enumerate(result.get('images', [])[:3], 1):
                print(f"    {i}. {img}")
        
        # 测试颜色筛选
        print(f"\n🎨 测试颜色筛选（NIGHTSCAPE）:")
        filtered = filter_images_by_color(result.get('images', []), 'NIGHTSCAPE')
        print(f"  筛选后: {len(filtered)} 张图片")
        if filtered:
            print(f"  第一张: {filtered[0]}")
    else:
        print("\n✗ 图片提取失败或返回None")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_image_extraction()
