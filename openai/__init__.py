from __future__ import annotations

import json
import os
import urllib.request


class _Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __getattr__(self, _name):
        return None


def _to_obj(value):
    if isinstance(value, dict):
        return _Obj(**{k: _to_obj(v) for k, v in value.items()})
    if isinstance(value, list):
        return [_to_obj(v) for v in value]
    return value


class _ChatCompletions:
    def __init__(self, client: "OpenAI"):
        self._client = client

    def create(self, **kwargs):
        payload = dict(kwargs)
        if "max_completion_tokens" in payload and "max_tokens" not in payload:
            payload["max_tokens"] = payload.pop("max_completion_tokens")
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._client.base_url.rstrip("/") + "/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._client.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self._client.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return _to_obj(body)


class _Chat:
    def __init__(self, client: "OpenAI"):
        self.completions = _ChatCompletions(client)


class OpenAI:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float | None = None, **_kwargs):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or "ollama"
        self.base_url = base_url or os.getenv("LOCAL_BASE_URL") or "http://localhost:11434/v1"
        self.timeout = timeout or 120
        self.chat = _Chat(self)
