import httpx

from app.modules.ai.schemas import AICompletion, AIProviderError


class DeepSeekProvider:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def complete_json(self, system_prompt: str, user_prompt: str) -> AICompletion:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "max_tokens": 1200,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AIProviderError("timeout", "DeepSeek request timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise AIProviderError(
                "http_error", f"DeepSeek returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise AIProviderError("network_error", "DeepSeek network request failed") from exc

        try:
            body = response.json()
            choice = body["choices"][0]
            content = choice["message"]["content"]
            usage = body.get("usage", {})
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise AIProviderError("invalid_response", "DeepSeek response shape is invalid") from exc
        if not isinstance(content, str) or not content.strip():
            raise AIProviderError("empty_response", "DeepSeek returned empty content")
        return AICompletion(
            content=content,
            provider="deepseek",
            model=body.get("model", self.model),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            finish_reason=choice.get("finish_reason"),
        )
