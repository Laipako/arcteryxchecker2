# supabase_client.py
import streamlit as st
from supabase import create_client, Client

class SupabaseManager:
    """Supabase 管理类"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseManager, cls).__new__(cls)
            cls._instance.init_client()
        return cls._instance

    def init_client(self):
        """初始化Supabase客户端"""
        try:
            # self.url = st.secrets["SUPABASE_URL"]
            self.url = 'https://kmsebovqoemcenedwfbi.supabase.co'
            # self.key = st.secrets["SUPABASE_KEY"]
            self.key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imttc2Vib3Zxb2VtY2VuZWR3ZmJpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2Nzk4NzMsImV4cCI6MjA3NjI1NTg3M30.PSzlSbwuoDBUyFoZUCXH3jG_V78wzf7YjDk4ynk43Qk'
            self.client: Client = create_client(self.url, self.key)
        except Exception as e:
            print(f"❌❌ Supabase 客户端初始化失败: {e}")
            self.client = None

    def get_client(self):
        """获取Supabase客户端"""
        if self.client:
            return self.client
        else:
            raise Exception("Supabase连接不可用")

# 创建全局Supabase管理器实例
supabase_manager = SupabaseManager()

# 导出函数和对象供其他模块使用
def get_supabase():
    """获取supabase客户端，安全处理异常"""
    try:
        return supabase_manager.get_client()
    except Exception as e:
        print(f"⚠️ Supabase 客户端不可用: {e}")
        return None

# 向后兼容：导出supabase对象
try:
    supabase = supabase_manager.get_client()
except Exception as e:
    supabase = None

