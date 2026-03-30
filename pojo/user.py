# pojo/user.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class User(SQLModel, table=True):

    __tablename__ = "cf_users"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    qq: str = Field(
        max_length=32,
        unique=True,
        index=True
    )

    rating: int = Field(default=0)

    is_admin: bool = Field(default=False)

    codeforces_name: str = Field(
        max_length=64,
        default=""
    )

    codeforces_id: str = Field(
        max_length=32,
        default="",
        nullable=True
    )

    # ===== CF验证 =====

    register_start_time: Optional[int] = Field(
        default=None
    )

    created_time: datetime = Field(
        default_factory=datetime.now
    )

    # 注册状态 0: 正在注册中  1:已完成注册
    register_status: int = Field(default=0)



    def __repr__(self) -> str:
        return f"<User(qq={self.qq}, codeforces_name={self.codeforces_name}, score={self.score})>"