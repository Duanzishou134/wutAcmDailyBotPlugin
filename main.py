from datetime import time

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import Image, Reply
from astrbot.api.star import Context, Star, register
from mammoth.results import success
from sqlalchemy.testing.provision import create_db
from sqlmodel import Session, select

from .pojo import User
from .service import UserService, DailyProblemService, PicService
from .database import engine, init_db


# @register 装饰器必须在类定义之前，且参数完整
@register("wut_acm_plugin", "dzs mty lc", "三条区开发的wut推题波特", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.user_service = UserService()
        self.daily_problem_service = DailyProblemService()
        self.pic_service = PicService()
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
            # yield event.plain_result(f"{event.get_sender_id()}")
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

    @filter.command("daily problem")
    async def daily_problem(self, event: AstrMessageEvent):
        daily_url = await self.daily_problem_service.get_daily_problem()
        yield event.plain_result(f"今天的每日一题是:{daily_url}")

    @filter.command("daily finish")
    async def daily_finish(self, event: AstrMessageEvent):
        qq = event.get_sender_id()
        result = await self.daily_problem_service.daily_finish(qq)
        yield event.plain_result(f"{result}")

    @filter.command("rankist")
    async def rank(self, event: AstrMessageEvent):
        qq = event.get_sender_id()
        result = await self.user_service.get_rankist()
        result_str = "积分榜\n"
        for user in result:
            result_str += f"{user.codeforces_name}: {user.rating}\n"
        yield event.plain_result(f"{result_str}")

    @filter.command("pic")
    async def send_pic(self, event: AstrMessageEvent, pic_name: str):
        if pic_name == "-list":
            result = await self.pic_service.get_pic_list()
            yield event.plain_result(result)
            return
            
        pic_path = await self.pic_service.get_pic_path(pic_name)
        if pic_path:
            yield event.image_result(pic_path)
        else:
            yield event.plain_result(f"图片 {pic_name} 不存在")

    @filter.command("add_pic")
    async def add_pic(self, event: AstrMessageEvent):
        args = event.get_message_str().split()
        if len(args) < 2:
            yield event.plain_result("用法: /add_pic <pic_name> <pic> [-n | -no-suffix]")
            return

        pic_name = args[1]
        flags = {arg for arg in args[2:] if arg.startswith("-")}
        no_suffix = "-n" in flags or "-no-suffix" in flags

        image = self._extract_image_from_event(event)
        if not image:
            yield event.plain_result("未检测到图片，请发送图片或通过回复图片消息使用 /add_pic <pic_name>。")
            return

        result = await self.pic_service.add_pic(pic_name, image, add_suffix=not no_suffix)
        yield event.plain_result(result)

    def _extract_image_from_event(self, event: AstrMessageEvent) -> Image | None:
        messages = event.get_messages()
        for comp in messages:
            if isinstance(comp, Image):
                return comp

        for comp in messages:
            if isinstance(comp, Reply) and comp.chain:
                for item in comp.chain:
                    if isinstance(item, Image):
                        return item
        return None
