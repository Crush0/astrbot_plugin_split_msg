from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Plain
from astrbot.api import AstrBotConfig
from pysbd import Segmenter
from astrbot.core.provider.entities import ProviderType
from astrbot.core.provider.register import register_provider_adapter
from astrbot.core.provider.provider import EmbeddingProvider
from volcenginesdkarkruntime import AsyncArk


@register_provider_adapter(
    "volcengine_embedding",
    "火山引擎 API Embedding 提供商适配器",
    provider_type=ProviderType.EMBEDDING,
)
class VolcengineEmbeddingProviderAdapter(EmbeddingProvider):
    def __init__(self, provider_config: dict, provider_settings: dict):
        super().__init__(provider_config, provider_settings)
        self.provider_config = provider_config
        self.provider_settings = provider_settings
        self.client = AsyncArk(
            api_key=provider_config.get("embedding_api_key"),
            base_url=provider_config.get("embedding_base_url", "https://ark.cn-beijing.volces.com/api/v3"),
            timeout=provider_config.get("timeout", 20),
        )
        self.model_name = provider_config.get("embedding_model_name", "doubao-embedding-vision-250615")

    async def get_embedding(self, text: str) -> list[float]:
        response = await self.client.multimodal_embeddings.create(
            model=self.model_name,
            input=[
                {
                    "type": "text",
                    "text": text,
                }
            ],
        )
        return response.data[0].embedding

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        responses = await self.client.multimodal_embeddings.create(
            model=self.model_name,
            input=[
                {
                    "type": "text",
                    "text": text,
                }
                for text in texts
            ],
        )
        return [response.embedding for response in responses.data]

    def get_dim(self) -> int:
        """获取向量的维度"""
        return self.provider_config.get("embedding_dimensions", 2048)

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
