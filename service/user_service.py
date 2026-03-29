from sqlmodel import select
from ..database import get_session
from ..pojo import User


def register(qq: str):
    """创建用户"""

    with get_session() as session:
        # 判断是否存在
        statement = select(User).where(User.qq == qq)
        result = session.exec(statement).first()

        if result:
            return "用户已存在"

        user = User(
            qq=qq,
            score=0
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return "注册成功"