from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path

DB_PATH = Path("data/plugins/wut_acm_plugin/cf_bot.db")

engine = create_engine(f"sqlite:///{DB_PATH}")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 只有数据库不存在才创建
    if not DB_PATH.exists():
        SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)