from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register


# @register 装饰器必须在类定义之前，且参数完整
@register("my_first_plugin", "你的名字", "一个简单的问候插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 指令必须使用 @filter.command 装饰器
    @filter.command("hello")
    async def hello_world(self, event: AstrMessageEvent):
        sender_name = event.get_sender_name()
        yield event.plain_result(f"Hello, {sender_name}!")