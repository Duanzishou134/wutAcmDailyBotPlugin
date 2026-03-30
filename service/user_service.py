import logging
from datetime import datetime

from sqlmodel import Session, select, delete
from ..pojo import User
from ..database import engine
from ..constant import StatusConstant
import time
import asyncio
from .codeforces_service import CodeforcesService
logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.codeforces_service = CodeforcesService()


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
                return False, "你还未开始账号，请输入/register <your_codeforces_name>"

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
            success = await self.codeforces_service.check_ce_submission(user.codeforces_name, user.register_start_time)
            if success:
                user.register_status = StatusConstant.FINISH
                session.add(user)
                session.commit()
                return True, f'欢迎你{user.codeforces_name}'
            return False, '好像出了点小错误, 请检测你提交的是否是CE代码'
