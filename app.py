#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ArcTeryx Checker - Streamlit应用入口
用于Streamlit Cloud部署
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import main
    
    if __name__ == "__main__":
        main()
except ImportError as e:
    import streamlit as st
    st.error(f"❌ 导入失败: {e}\n\n请确保所有依赖已正确安装。")
    st.stop()
except Exception as e:
    import streamlit as st
    st.error(f"❌ 应用启动失败: {e}")
    import traceback
    st.write(traceback.format_exc())
    st.stop()
