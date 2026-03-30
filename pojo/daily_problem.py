# pojo/user.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date


class DailyProblem(SQLModel, table=True):

    __tablename__ = "daily_problem"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    contest_id: int = Field(default=None, nullable=True)

    problem_index: str = Field(
        max_length=10,
        default="",
        nullable=True
    )

    problem_name: str = Field(
        max_length=32,
        default="",
        nullable=True
    )

    url: str = Field(
        max_length=100,
        default="",
        nullable=True
    )

    rating: int = Field(default=0)

    daily_date: date = Field(
        default_factory=date.today
    )

    def __repr__(self) -> str:
        return f"<DailyProblem(contest_id={self.contest_id}, problem_name={self.problem_name}, score={self.score})>"