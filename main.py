from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Plain
from astrbot.api import AstrBotConfig
from pysbd import Segmenter
import provider

class SplitMsgPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.ctx = context
        self.config = config
        self.words_count_threshold = self.config.get("words_count_threshold", 15)
        self.enable = self.config.get("enable", True)
        self.cn_segmenter = Segmenter(language="zh", clean=False)
        self.en_segmenter = Segmenter(language="en", clean=False)

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        result = event.get_result()
        if result is None:
            return
        if len(result.chain) > 0:
            if event.get_platform_name() not in [
                "qq_official",
                "weixin_official_account",
                "dingtalk",
            ] and result.is_llm_result() and self.enable:
                new_chain = []
                for comp in result.chain:
                    if isinstance(comp, Plain):
                        if len(comp.text) < self.words_count_threshold:
                            # 不分段回复
                            new_chain.append(comp)
                            continue
                        if not comp.text.isascii():
                            split_response = self.cn_segmenter.segment(comp.text)
                        else:
                            split_response = self.en_segmenter.segment(comp.text)
                        new_chain.extend([Plain(text) for text in split_response if text.strip()])
                    else:
                        new_chain.append(comp)
                result.chain = new_chain
                event.set_result(result)

    # async def terminate(self):
    #     """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
