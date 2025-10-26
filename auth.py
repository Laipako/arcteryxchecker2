import streamlit as st
from supabase_client import get_supabase

def show_auth_ui():
    """显示认证界面"""
    st.title("🏔️ 始祖鸟查货系统 - 登录")
    
    # 检查是否已有有效的会话
    supabase = get_supabase()
    if supabase:
        try:
            session = supabase.auth.get_session()
            if session and session.user:
                st.success(f"✅ 已登录用户: {session.user.email}")
                st.session_state.authenticated = True
                st.session_state.user_id = session.user.id
                return True
        except Exception as e:
            print(f"会话检查失败: {e}")
    
    st.info("请输入临时密钥进行认证")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        temp_key = st.text_input("临时认证密钥", type="password", help="输入认证密钥继续")
    
    with col2:
        if st.button("登录", use_container_width=True):
            # 简单的密钥验证（开发环境用）
            if verify_temp_key(temp_key):
                st.session_state.authenticated = True
                st.session_state.temp_user_id = temp_key  # 使用密钥作为用户ID
                st.success("✅ 认证成功！")
                st.rerun()
            else:
                st.error("❌ 认证密钥无效")
    
    return False

def verify_temp_key(key):
    """验证临时密钥"""
    # 对于开发环境，任何非空密钥都可以使用
    # 生产环境应该对接真实的认证系统
    return len(key) > 0

def check_authentication():
    """检查用户是否已认证"""
    # 首先检查Supabase会话
    supabase = get_supabase()
    if supabase:
        try:
            session = supabase.auth.get_session()
            if session and session.user:
                st.session_state.authenticated = True
                st.session_state.user_id = session.user.id
                return True
        except Exception as e:
            print(f"Supabase会话检查失败: {e}")
    
    # 检查临时认证状态
    if st.session_state.get("authenticated", False):
        return True
    
    return False

def logout():
    """登出用户"""
    supabase = get_supabase()
    if supabase:
        try:
            supabase.auth.sign_out()
        except Exception as e:
            print(f"登出失败: {e}")
    
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.temp_user_id = None
