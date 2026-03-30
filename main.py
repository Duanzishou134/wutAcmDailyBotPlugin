from datetime import time

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from mammoth.results import success
from sqlalchemy.testing.provision import create_db
from sqlmodel import Session, select

from .pojo import User
from .service import CodeforcesService
from .service import UserService
from .database import engine, init_db


# @register 装饰器必须在类定义之前，且参数完整
@register("wut_acm_plugin", "dzs mty lc", "三条区开发的wut推题波特", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.codeforces_service = CodeforcesService()
        self.user_service = UserService()
        init_db()


    # 指令必须使用 @filter.command 装饰器
    @filter.command("hello")
    async def hello_world(self, event: AstrMessageEvent):
        sender_name = event.get_sender_name()
        yield event.plain_result(f"Hello, {sender_name}!")

    @filter.command("register")
    async def register_command(self, event: AstrMessageEvent):
        """处理 /register 命令"""
        args = event.get_message_str().split()
        if not args or len(args) != 2:
            yield event.plain_result("用法: /register <your_codeforces_name>")
            return

        cmd = args[1].lower()


        if cmd == "finish":
            # 完成验证
            yield event.plain_result(f"{event.get_sender_id()}")
            success, result = await self.user_service.register_finish(
                event.get_sender_id()
            )
            if not success:
                yield event.plain_result(f"{result}")
                return

            yield event.plain_result(f"注册成功, {result}")

        else:
            # 开始验证
            codeforces_name = cmd
            success = self.user_service.register_start(event.get_sender_id(), codeforces_name)
            if success:
                yield event.plain_result(
                    f"请 {codeforces_name} 在2分钟内\n"
                    f"前往 https://codeforces.com/contest/1/problem/A\n"
                    f"提交一份编译错误(CE)的代码\n"
                    f"然后输入 /register finish"
                )
            else:
                yield event.plain_result("你已经绑定过账号了")



