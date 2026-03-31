# database.py
from sqlmodel import SQLModel, create_engine
from .pojo import User, DailyProblem, UserProblem
from sqlalchemy import inspect
import os

DATABASE_URL = "sqlite:///data/plugins/wut_acm_plugin/cf_bot.db"
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """创建表（如果不存在）"""
    SQLModel.metadata.create_all(engine)

# 你也可以保留直接调用，但建议在插件初始化时调用一次
init_db()