# pojo/user.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class UserProblem(SQLModel, table=True):

    __tablename__ = "user_problem"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(nullable=False)
    problem_id: int = Field(nullable=False)
    created_time: datetime = Field(
        default_factory=datetime.now
    )

    def __repr__(self) -> str:
        return f"<UserProblem(user_id={self.contest_id}, problem_id={self.problem_name})>"