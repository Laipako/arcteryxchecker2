import streamlit as st

def check_password():
    """检查密码是否正确"""
    def password_entered():
        # 从 Streamlit secrets 读取密码
        correct_password = st.secrets.get("APP_PASSWORD", "")
        
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "密码", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "密码", type="password", on_change=password_entered, key="password"
        )
        st.error("😕😕 密码不正确")
        return False
    else:
        return True
