from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Plain
from pysbd import Segmenter
@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.cn_segmenter = Segmenter(language="zh", clean=False)
        self.en_segmenter = Segmenter(language="en", clean=False)

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        msgs = event.get_messages()
        result = []
        for msg in msgs:
            if isinstance(msg, Plain):
                result.extend([MessageChain([Plain(text)]) for text in self.cn_segmenter.segment(msg.text)])
            else:
                result.append(msg)
        for i in result:
            await event.send(i)
        event.stop_event()

    # async def terminate(self):
    #     """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
