from app.llm.base import BaseLLM


class OllamaClient(BaseLLM):

    async def generate(
        self,
        system: str,
        prompt: str,
    ) -> str:

        raise NotImplementedError