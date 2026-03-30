# pojo/user.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class DailyProblem(SQLModel, table=True):

    __tablename__ = "daily_problem"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    contest_id: int = Field(default=None, nullable=True)

    problem_name: str = Field(
        max_length=32,
        default="",
        nullable=True
    )

    score: int = Field(default=0)

    created_time: datetime = Field(
        default_factory=datetime.now
    )

    def __repr__(self) -> str:
        return f"<DailyProblem(contest_id={self.contest_id}, problem_name={self.problem_name}, score={self.score})>"