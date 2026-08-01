from typing import Protocol

from app.modules.ai.schemas import AICompletion


class AIProvider(Protocol):
    async def complete_json(self, system_prompt: str, user_prompt: str) -> AICompletion: ...
