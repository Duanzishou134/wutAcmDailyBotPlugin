# pojo/user.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class User(SQLModel, table=True):
    """Codeforces 机器人用户表"""

    __tablename__ = "cf_users"  # 自定义表名，避免与核心表冲突

    __table_args__ = {"extend_existing": True}


    # ===== 主键 =====
    id: Optional[int] = Field(default=None, primary_key=True, description="自增主键")

    # ===== 基础信息 =====
    qq: str = Field(
        max_length=32,
        unique=True,
        index=True,
        description="QQ号"
    )

    # ===== 积分系统 =====
    score: int = Field(
        default=0,
        description="用户总积分"
    )

    # ===== 权限管理 =====
    is_admin: bool = Field(
        default=False,
        description="是否为管理员"
    )

    # ===== Codeforces 绑定信息 =====
    codeforces_name: str = Field(
        max_length=64,
        default="",
        description="Codeforces 用户名"
    )

    codeforces_id: str = Field(
        max_length=32,
        default="",
        unique=True,
        nullable=True,
        description="Codeforces 用户ID（数字ID）"
    )

    # ===== 时间字段 =====
    created_time: datetime = Field(
        default_factory=datetime.now,
        description="用户注册时间"
    )


    def __repr__(self) -> str:
        return f"<User(qq={self.qq}, codeforces_name={self.cf_name}, score={self.score})>"