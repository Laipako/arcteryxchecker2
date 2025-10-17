# database.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import streamlit as st


class MongoDBManager:
    """MongoDB 管理类"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
            cls._instance.init_connection()
        return cls._instance

    def init_connection(self):
        """初始化数据库连接"""
        try:
            # 从 Streamlit secrets 获取连接字符串
            connection_string = st.secrets["MONGODB_URI"]
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            self.db = self.client['arcteryx_db']
            self.collection = self.db['favorites']

            # 测试连接
            self.client.admin.command('ping')

        except ConnectionFailure as e:
            print(f"❌ MongoDB 连接失败: {e}")
            self.client = None

    def get_collection(self):
        """获取集合对象"""
        if self.client:
            return self.collection
        else:
            raise Exception("数据库连接不可用")


# 创建全局数据库管理器实例
db_manager = MongoDBManager()