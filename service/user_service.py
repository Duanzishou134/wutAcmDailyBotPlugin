
from datetime import datetime

from sqlmodel import Session, select, delete, desc
from ..pojo import User
from ..database import engine
from ..constant import StatusConstant
import time
from ..utils import CodeforcesUtils


class UserService:
    def __init__(self):
        self.codeforces_utils = CodeforcesUtils()


    def register_start(self, qq: str, codeforces_name: str) -> bool:
        """开始验证流程"""
        with Session(engine) as session:
            # 检查用户是否已绑定
            statement = select(User).where(User.qq == qq)
            user = session.exec(statement).first()

            if user and user.register_status == StatusConstant.FINISH:
                return False  # 已绑定


            if not user:
                user = User(qq=qq)
            # 设置验证信息
            # logger.info(f"{qq}")
            user.codeforces_name = codeforces_name
            user.register_start_time = int(time.time())
            user.register_status = StatusConstant.IN_REGISTERING
            user.created_time = datetime.now()

            session.add(user)
            session.commit()
            print("向数据库中插入数据")
            return True

    async def register_finish(self, qq: str) -> tuple[bool, str]:
        """完成验证并绑定账号"""
        with Session(engine) as session:
            statement = select(User).where(User.qq == qq)
            user = session.exec(statement).first()

            if not user:
                return False, "你还未开始注册账号，请输入/register <your_codeforces_name>"

            if user.register_status == StatusConstant.FINISH:
                return False, "你已注册账号"

            # 检查是否超时(2分钟)
            current_time = int(time.time())
            if current_time - user.register_start_time > 120:
                statement = delete(User).where(User.qq == qq)
                session.exec(statement)
                session.commit()
                return False, "验证超时(2分钟)"

            # 异步检查CF提交
            success = await self.codeforces_utils.check_ce_submission(user.codeforces_name, user.register_start_time)
            if success:
                user.register_status = StatusConstant.FINISH
                user.created_time = datetime.now()
                session.add(user)
                session.commit()
                return True, f'欢迎你{user.codeforces_name}'
            return False, '好像出了点小错误, 请检查你提交的是否是CE代码'

    async def get_rankist(self):
        with Session(engine) as session:

            statement = select(User).where(User.register_status == StatusConstant.FINISH).order_by(desc(User.rating)).limit(10)
            users = session.exec(statement).all()
            return users

    async def get_user_info(self, qq: str) -> tuple[bool, dict | str]:
        with Session(engine) as session:
            statement = select(User).where(User.qq == qq)
            user = session.exec(statement).first()
            if not user or user.register_status != StatusConstant.FINISH:
                return False, "暂未注册"

        cf_info = await self.codeforces_utils.get_user_info(user.codeforces_name)
        cf_rating = "未评级"
        if cf_info is not None:
            cf_rating = cf_info.get("rating", "未评级")
        else:
            cf_rating = "未获取"

        solved_count = await self.codeforces_utils.get_solved_count(user.codeforces_name)
        if solved_count is None:
            solved_count = "未获取"

        return True, {
            "cf_name": user.codeforces_name,
            "cf_rating": cf_rating,
            "scores": user.rating,
            "solved_count": solved_count,
        }



