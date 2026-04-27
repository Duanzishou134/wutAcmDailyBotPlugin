from datetime import datetime, time, date
from typing import Optional, Dict
from sqlmodel import Session, select, delete
from ..pojo import User, DailyProblem, UserProblem
from ..database import engine
from ..constant import StatusConstant
import time
from ..utils import CodeforcesUtils

class DailyProblemService:
    def __init__(self):
        self.codeforces_utils = CodeforcesUtils()

    # ---------- 内部方法 ----------

    def _create_daily(self, problem: Dict, daily_date: date) -> DailyProblem:
        """将 API 返回的题目构造成 DailyProblem 对象"""
        daily = DailyProblem()
        daily.contest_id = problem["contestId"]
        daily.problem_index = problem["index"]
        daily.problem_name = problem["name"]
        daily.rating = problem.get("rating", 0)
        daily.url = f"https://codeforces.com/problemset/problem/{daily.contest_id}/{daily.problem_index}"
        daily.daily_date = daily_date
        return daily
    
    def _get_today_problems(self, session: Session, today: date):
        """获取今天的所有 DailyProblem，返回 (easy, hard) 两个对象或 None"""
        stmt = select(DailyProblem).where(DailyProblem.daily_date == today)
        all_today = session.exec(stmt).all()
        easy = next((p for p in all_today if p.rating <= 1800), None)
        hard = next((p for p in all_today if p.rating > 1800), None)
        return easy, hard
    
    async def _do_finish(self, qq: str, daily: DailyProblem, session: Session) -> str:
        """
        核心完成逻辑（需要 session 已在外部开启）。
        校验用户、判重、去 CF 查提交、计算积分并记录。
        返回操作结果提示信息。
        """
        today = date.today()

        # 1. 检查用户绑定
        user = session.exec(select(User).where(User.qq == qq)).first()
        if not user or user.register_status != StatusConstant.FINISH:
            return "请先绑定 Codeforces 账号"

        # 2. 是否已完成过该题（防重复）
        already = session.exec(
            select(UserProblem).where(
                UserProblem.problem_id == daily.id,
                UserProblem.user_id == user.id
            )
        ).first()
        if already:
            return "你已经完成过这道题了"

        # 3. 去 Codeforces 查验是否真的有 AC 提交
        success = await self.codeforces_utils.check_submission(
            user.codeforces_name,
            daily.contest_id,
            daily.problem_index,
            "OK",
            daily.daily_date
        )
        if not success:
            return "未检测到有效提交"

        # 4. 计算当天已获得的最大积分（从已完成的同天题目中）
        #    找出该用户今天完成的所有其他题目（不含当前要提交的）
        other_records = session.exec(
            select(UserProblem).where(
                UserProblem.user_id == user.id,
                UserProblem.problem_id != daily.id
            )
        ).all()

        previous_max = 0
        if other_records:
            other_ids = [r.problem_id for r in other_records]
            other_dailies = session.exec(
                select(DailyProblem).where(
                    DailyProblem.id.in_(other_ids),
                    DailyProblem.daily_date == today
                )
            ).all()
            if other_dailies:
                previous_max = max(d.rating for d in other_dailies)

        new_rating = daily.rating
        max_rating = max(previous_max, new_rating)
        delta = max_rating - previous_max

        # 5. 增加积分（可能为 0）
        user.rating += delta

        # 6. 记录完成
        record = UserProblem(
            problem_id=daily.id,
            user_id=user.id,
            created_time=datetime.now()
        )
        session.add(record)
        session.add(user)
        session.commit()

        # 7. 返回提示
        if delta == 0:
            return f"恭喜你完成了今天的每日一题，今天已获得更高分题目，不加积分，你当前的积分为 {user.rating}"
        else:
            return f"恭喜你完成了今天的每日一题, 获得{delta} 积分，你当前的积分为 {user.rating}"

    # ---------- 获取今日双题 ----------
    async def get_daily_problems(self) -> Dict[str, Dict]:
        """返回今日两道题的信息字典，包含 id, url, rating, name"""
        today = date.today()
        with Session(engine) as session:
            easy, hard = self._get_today_problems(session, today)

            if not easy:
                problem = await self.codeforces_utils.get_random_problem(max_rating=1800)
                if problem:
                    easy = self._create_daily(problem, today)
                    session.add(easy)
                    session.flush()  # 获取 id

            if not hard:
                problem = await self.codeforces_utils.get_random_problem(min_rating=1801)
                if problem:
                    hard = self._create_daily(problem, today)
                    session.add(hard)
                    session.flush()

            session.commit()

            return {
                "easy": {
                    "id": easy.id if easy else None,
                    "url": easy.url if easy else None,
                    "rating": easy.rating if easy else None,
                    "name": easy.problem_name if easy else None,
                },
                "hard": {
                    "id": hard.id if hard else None,
                    "url": hard.url if hard else None,
                    "rating": hard.rating if hard else None,
                    "name": hard.problem_name if hard else None,
                }
            }

    async def daily_finish_by_difficulty(self, qq: str, difficulty: str) -> str:
        """
        用户提交每日一题，只需传入难度。
        difficulty: "easy" 或 "hard"。
        """
        difficulty = difficulty.lower()
        if difficulty not in ("easy", "hard"):
            return "请指定 easy 或 hard"

        today = date.today()
        with Session(engine) as session:
            # 查找当天对应难度的题目
            if difficulty == "easy":
                daily = session.exec(
                    select(DailyProblem).where(
                        DailyProblem.daily_date == today,
                        DailyProblem.rating <= 1800
                    )
                ).first()
            else:  # hard
                daily = session.exec(
                    select(DailyProblem).where(
                        DailyProblem.daily_date == today,
                        DailyProblem.rating > 1800
                    )
                ).first()

            if not daily:
                return "今日该难度的题目还未生成，请稍后再试"

            return await self._do_finish(qq, daily, session)

    async def daily_change(self, qq: str):
        """直接更换今日所有每日一题，并清理当天用户完成记录（重置进度）"""
        today = date.today()
        with Session(engine) as session:
            # 获取今天已有的题目 ID
            old_ids = session.exec(
                select(DailyProblem.id).where(DailyProblem.daily_date == today)
            ).all()

            if old_ids:
                # 清理用户今天的完成记录
                session.exec(delete(UserProblem).where(UserProblem.problem_id.in_(old_ids)))
                # 删除旧题目
                session.exec(delete(DailyProblem).where(DailyProblem.daily_date == today))

            # 重新生成两道
            easy = await self.codeforces_utils.get_random_problem(max_rating=1800)
            hard = await self.codeforces_utils.get_random_problem(min_rating=1801)

            urls = []
            if easy:
                e = self._create_daily(easy, today)
                session.add(e)
                urls.append(f"easy: {e.url}")
            if hard:
                h = self._create_daily(hard, today)
                session.add(h)
                urls.append(f"hard: {h.url}")

            session.commit()
            return "已更换今日每日一题:\n" + "\n".join(urls)
