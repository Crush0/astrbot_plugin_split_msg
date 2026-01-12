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
            api_key = provider_config.get("embedding_api_key"),
            base_url = provider_config.get("embedding_base_url", "https://ark.cn-beijing.volces.com/api/v3"),
            timeout = provider_config.get("timeout", 20),
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