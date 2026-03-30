from datetime import datetime, time, date

from sqlmodel import Session, select, delete
from ..pojo import User, DailyProblem, UserProblem
from ..database import engine
from ..constant import StatusConstant
import time
from ..utils import CodeforcesUtils

class DailyProblemService:
    def __init__(self):
        self.codeforces_utils = CodeforcesUtils()

    async def get_daily_problem(self):

        with Session(engine) as session:

            statement = select(DailyProblem).where(DailyProblem.daily_date == date.today())
            daily_problem = session.exec(statement).first()
            if daily_problem is not None :
                return daily_problem.url
            daily_problem = DailyProblem()

            problem = await self.codeforces_utils.get_random_problem()

            contest_id = problem.get("contestId")
            daily_problem.contest_id = contest_id

            index = problem.get("index")
            daily_problem.problem_index = index

            name = problem.get("name")
            daily_problem.problem_name = name

            rating = problem.get("rating", 0)
            daily_problem.rating = rating

            tags_str = ", ".join(problem.get("tags", []))
            url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
            daily_problem.url = url

            daily_problem.daily_date = date.today()
            session.add(daily_problem)
            session.commit()

            return url

    async def daily_finish(self, qq: str):
        with Session(engine) as session:
            # 检查用户是否已绑定
            statement = select(User).where(User.qq == qq)
            user = session.exec(statement).first()
            statement = select(DailyProblem).where(DailyProblem.daily_date == date.today())
            daily_problem = session.exec(statement).first()




            if not user or user.register_status != StatusConstant.FINISH:
                return "你还未绑定账号，请绑定你的codeforces账号后再提交吧"

            problem_id = daily_problem.id
            user_id = user.id

            statement = select(UserProblem).where(
                UserProblem.problem_id == problem_id,
                UserProblem.user_id == user_id)

            user_problem = session.exec(statement).first()
            if user_problem is not None:
                return "你已经完成了今天的每日一题，明天再来吧"

            user_problem = UserProblem()

            success = await self.codeforces_utils.check_submission(
                user.codeforces_name,
                daily_problem.contest_id,
                daily_problem.problem_index,
                "OK",
                daily_problem.daily_date
            )
            if success:
                user.rating += daily_problem.rating

                user_problem.problem_id = daily_problem.id
                user_problem.user_id = user_id

                user_problem.created_time = datetime.now()
                session.add(user_problem)
                session.add(user)
                session.commit()
                return f"恭喜你完成了今天的每日一题, 获得{daily_problem.rating}积分, 你当前的积分为{user.rating}"
            else:
                return "未检测到有效提交"