import streamlit as st
from cache_manager import product_cache
from datetime import datetime


def format_size(bytes_size):
    """将字节转换为可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def show_cache_management_tab():
    """显示缓存管理标签页"""
    st.subheader("🗑️ 缓存管理")
    
    # 显示数据库连接信息
    st.write("**数据库连接状态：**")
    try:
        from supabase_client import get_supabase
        client = get_supabase()
        if client:
            st.success("✅ Supabase 连接正常")
        else:
            st.error("❌ Supabase 连接失败")
    except Exception as e:
        st.error(f"❌ Supabase 连接异常: {str(e)}")
    
    st.divider()
    
    # 获取缓存统计信息
    stats = product_cache.get_cache_statistics()
    
    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("缓存项数", stats['count'], "项")
    
    with col2:
        st.metric("总缓存大小", format_size(stats['total_size']))
    
    with col3:
        st.metric("缓存时效", f"{stats['ttl_minutes']} 分钟")
    
    with col4:
        expired_count = count_expired_items(stats['items'])
        st.metric("过期项数", expired_count, "项")
    
    st.divider()
    
    # 缓存详情表格
    if stats['count'] > 0:
        st.write("**缓存详情：**")
        
        cache_items = stats['items']
        
        # 创建表格数据
        table_data = []
        for item in cache_items:
            is_expired = is_cache_expired(item['timestamp'], stats['ttl_minutes'])
            status = "⏰ 已过期" if is_expired else "✅ 有效"
            
            table_data.append({
                "产品ID": item['product_id'],
                "缓存键": item['key'],
                "大小": format_size(item['size']),
                "创建时间": item['timestamp'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(item['timestamp'], datetime) else str(item['timestamp']),
                "状态": status
            })
        
        # 显示表格
        st.dataframe(table_data, use_container_width=True)
    else:
        st.info("📭 暂无缓存数据")
    
    st.divider()
    
    # 清除缓存按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 清除过期缓存", use_container_width=True):
            removed_count = clear_expired_cache(stats['items'])
            st.success(f"✅ 已清除 {removed_count} 项过期缓存")
            st.rerun()
    
    with col2:
        if st.button("🗑️ 清除全部缓存", use_container_width=True):
            removed_count = product_cache.clear_all_cache()
            st.success(f"✅ 已清除全部缓存（{removed_count} 项）")
            st.rerun()
    
    with col3:
        if st.button("🔄 刷新统计", use_container_width=True):
            st.rerun()


def is_cache_expired(timestamp, ttl_minutes):
    """检查缓存是否已过期"""
    if not isinstance(timestamp, datetime):
        return True
    
    elapsed = datetime.now() - timestamp
    return elapsed.total_seconds() > (ttl_minutes * 60)


def count_expired_items(cache_items):
    """计算过期项数"""
    from cache_manager import product_cache
    ttl_minutes = product_cache.ttl_minutes
    expired_count = sum(1 for item in cache_items if is_cache_expired(item['timestamp'], ttl_minutes))
    return expired_count


def clear_expired_cache(cache_items):
    """清除所有过期缓存"""
    from cache_manager import product_cache
    ttl_minutes = product_cache.ttl_minutes
    removed_count = 0
    
    for item in cache_items:
        if is_cache_expired(item['timestamp'], ttl_minutes):
            if product_cache.clear_specific_cache(item['key']):
                removed_count += 1
    
    return removed_count
