from datetime import time
import random
import os

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import Image, Reply
from astrbot.api.star import Context, Star, register
from mammoth.results import success
from sqlalchemy.testing.provision import create_db
from sqlmodel import Session, select

from .pojo import User
from .service import UserService, DailyProblemService, PicService, CFDataService, CFProfileCardService
from .utils.html_render import render_template_to_image
from .utils.cf_query_parser import parse_random_args
from .database import engine, init_db


# @register 装饰器必须在类定义之前，且参数完整
@register("wut_acm_plugin", "dzs mty lc", "三条区开发的wut推题波特", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.user_service = UserService()
        self.daily_problem_service = DailyProblemService()
        self.pic_service = PicService()
        self.cf_data_service = CFDataService()
        self.cf_profile_card_service = CFProfileCardService(os.path.dirname(os.path.abspath(__file__)))
        self.info_template = self._load_info_template("template.html")
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

    @filter.command("rank")
    async def rank(self, event: AstrMessageEvent):
        qq = event.get_sender_id()
        result = await self.user_service.get_rankist()
        result_str = "积分榜\n"
        for user in result:
            result_str += f"{user.codeforces_name}: {user.rating}\n"
        yield event.plain_result(f"{result_str}")

    @filter.command("daily change")
    async def daily_change(self, event: AstrMessageEvent):
        qq = event.get_sender_id()
        result = await self.daily_problem_service.daily_change(qq)
        yield event.plain_result(f"{result}")

    @filter.command("info")
    async def info(self, event: AstrMessageEvent):
        args = event.get_message_str().split()
        text_only = len(args) >= 2 and args[1] == "-t"
        qq = event.get_sender_id()
        success, result = await self.user_service.get_user_info(qq)
        if not success:
            yield event.plain_result(result)
            return
        if text_only:
            response = (
                f"CF用户: {result['cf_name']}\n"
                f"CF Rating: {result['cf_rating']}\n"
                f"当前积分: {result['scores']}\n"
                f"CF 做题数量: {result['solved_count']}"
            )
            yield event.plain_result(response)
            return
        template_data = {
            "qq_name": event.get_sender_name(),
            "cf_name": result["cf_name"],
            "solved": result["solved_count"],
            "score": result["scores"],
        }
        try:
            image_path = await render_template_to_image(
                self.info_template,
                template_data,
                width=600,
                height=400,
                full_page=True,
                image_type="png",
            )
            yield event.image_result(image_path)
        except Exception:
            response = (
                f"CF用户: {result['cf_name']}\n"
                f"CF Rating: {result['cf_rating']}\n"
                f"当前积分: {result['scores']}\n"
                f"CF 做题数量: {result['solved_count']}"
            )
            yield event.plain_result(f"图片渲染失败，已返回文本信息:\n{response}")


    @filter.command("pic help")
    async def pic_help(self, event: AstrMessageEvent):
        '''这里就是该指令的帮助说明，将会被 /help 或类似指令显示。'''
        yield event.plain_result(
            "/pic <pic_name> 发送指定图片\n"
            "/pic -list [pic_name] 查看图片列表\n"
            "/add_pic <pic_name> <pic> [-n | -no-suffix] 添加图片(回复图片也可)"
        )
    @filter.command("help")
    async def help(self, event: AstrMessageEvent):
        '''这里就是该指令的帮助说明，将会被 /help 或类似指令显示。'''
        yield event.plain_result(
            "这是秽土重生的盗版法老王，有以下几个简单功能\n"
            "/pic help 查看pic具体功能\n"
            "/cf help 查看cf具体功能\n"
            "/register <codeforces_name> "
            "绑定你的qq账号和codeforces账号\n"
            "/register finish 绑定完成\n"
            "/daily problem 查看每日一题\n"
            "/daily finish 完成每日一题\n"
            "/rank 查看每日一题积分榜(前十)\n"
            "/info 查看当前用户信息(图片卡片)\n"
            "/info -t 查看当前用户信息(文本)\n"
        )

    @filter.command("pic")
    async def send_pic(self, event: AstrMessageEvent):
        args = event.get_message_str().split()
        if len(args) < 2:
            yield event.plain_result("用法: /pic <pic_name> | /pic list [pic_name]")
            return
        if args[1] == "help":
            return

        if args[1] == "list":
            if len(args) >= 3:
                result = await self.pic_service.get_pic_list_by_prefix(args[2])
            else:
                result = await self.pic_service.get_pic_list()
            yield event.plain_result(result)
            return

        pic_name = args[1]
        status, payload = await self.pic_service.get_pic_path(pic_name)
        if status == "image":
            yield event.image_result(payload)
        elif status == "conflict":
            conflict_list = "\n".join(payload)
            yield event.plain_result(f"存在冲突，请指名图片名:\n{conflict_list}")
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

    # @filter.command("cf")
    # async def cf_root(self, event: AstrMessageEvent):
    #     if event.message_str.strip() not in {"/cf", "cf"}:
    #         return
    #     yield event.plain_result(
    #         "Usage: /cf help\n"
    #         "Usage: /cf random [rating] [tag]\n"
    #         "Usage: /cf contests [count]\n"
    #         "Usage: /cf info <handle>"
    #     )

    @filter.command_group("cf")
    def cf_group(self):
        """CF command group"""

    @cf_group.command("random")
    async def cf_random(self, event: AstrMessageEvent):
        text = event.message_str.strip()
        rating_low, rating_high, tags = parse_random_args(text)
        problems, err = await self.cf_data_service.load_problemset()
        if err:
            yield event.plain_result(f"Fetch problemset failed: {err}")
            return

        filtered = []
        for p in problems:
            contest_id = p.get("contestId")
            index = p.get("index")
            if contest_id is None or not index:
                continue

            rating = p.get("rating")
            if rating_low is not None:
                if rating is None or rating < rating_low or rating > rating_high:
                    continue

            p_tags = {str(t).lower() for t in p.get("tags", [])}
            if tags and not set(tags).issubset(p_tags):
                continue

            filtered.append(p)

        if not filtered:
            yield event.plain_result("No problem found under current filters.")
            return

        chosen = random.choice(filtered)
        link = f"https://codeforces.com/problemset/problem/{chosen['contestId']}/{chosen['index']}"
        yield event.plain_result(link)

    @cf_group.command("contests")
    async def cf_contests(self, event: AstrMessageEvent, count: str = ""):
        n = 8
        if count.strip().isdigit():
            n = max(1, min(20, int(count.strip())))

        contests, err = await self.cf_data_service.load_upcoming_contests()
        if err:
            yield event.plain_result(f"Fetch contests failed: {err}")
            return
        if not contests:
            yield event.plain_result("No upcoming contests found.")
            return

        lines = ["Upcoming contests:"]
        for idx, c in enumerate(contests[:n], start=1):
            start_local = self.cf_data_service.fmt_ts(c["start_ts"])
            lines.append(f"{idx}. [{c['site']}] {c['name']} | {start_local} | {c['url']}")
        yield event.plain_result("\n".join(lines))

    @cf_group.command("info")
    async def cf_info(self, event: AstrMessageEvent, handle: str = ""):
        handle = handle.strip()
        if not handle:
            yield event.plain_result("Usage: /cf info <handle>")
            return

        profile, solved_count, err = await self.cf_data_service.fetch_profile_bundle(handle)
        if err:
            yield event.plain_result(f"Fetch user info failed: {err}")
            return

        card_path, render_err = await self.cf_profile_card_service.render_profile_card(profile, solved_count)
        if render_err:
            yield event.plain_result(f"Render card failed: {render_err}")
            return

        try:
            yield event.image_result(card_path)
        finally:
            self._safe_remove_file(card_path)

    @cf_group.command("help")
    async def cf_help(self, event: AstrMessageEvent, topic: str = ""):
        t = topic.strip().lower()
        if t in {"tags", "tag"}:
            problems, err = await self.cf_data_service.load_problemset()
            if err:
                yield event.plain_result(f"获取标签失败：{err}")
                return
            tags = sorted(
                {
                    str(tag).strip().lower()
                    for p in problems
                    for tag in p.get("tags", [])
                    if str(tag).strip()
                }
            )
            if not tags:
                yield event.plain_result("未找到可用标签。")
                return
            yield event.plain_result(f"可用标签（共 {len(tags)} 个）：\n" + ", ".join(tags))
            return

        yield event.plain_result(
            "CF 功能说明：\n"
            "/cf random\n"
            "随机一道题。\n"
            "/cf random <rating>\n"
            "按指定难度随机，例如：/cf random 1600\n"
            "/cf random <low-high>\n"
            "按难度区间随机，例如：/cf random 1200-1600\n"
            "/cf random tag=<tag>\n"
            "按标签随机，例如：/cf random tag=binary search\n"
            "/cf random rating=<low-high> tag=<tag1,tag2>\n"
            "组合筛选（标签为同时包含），例如：/cf random rating=1400-1800 tag=dp,greedy\n"
            "/cf help tags\n"
            "查看所有可用标签。\n"
            "/cf contests [count]\n"
            "查看近期比赛（Codeforces / AtCoder / Nowcoder），count 默认 8、最大 20。\n"
            "/cf info <handle>\n"
            "生成该用户的 Codeforces 资料卡片。\n"
            "\n"
            "示例：\n"
            "/cf random\n"
            "/cf random 1600\n"
            "/cf random tag=binary search\n"
            "/cf contests 12\n"
            "/cf info tourist"
        )

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

    def _safe_remove_file(self, path: str | None) -> None:
        if not path:
            return
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    def _load_info_template(self, template_path: str) -> str:
        template_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "asserts",
            template_path,
        )
        with open(template_path, "r", encoding="utf-8") as file:
            return file.read()
