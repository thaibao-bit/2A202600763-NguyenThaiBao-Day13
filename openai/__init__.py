from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def _load_dotenv():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key and not os.getenv(key):
                os.environ[key] = value.strip().strip('"').strip("'")
    except OSError:
        return


def _load_real_openai():
    current_pkg = Path(__file__).resolve().parent
    workspace_root = current_pkg.parent
    search_paths = []
    for entry in sys.path:
        if not entry:
            continue
        try:
            path = Path(entry).resolve()
        except OSError:
            continue
        if path == workspace_root or path == current_pkg:
            continue
        search_paths.append(str(path))
    spec = importlib.machinery.PathFinder.find_spec("openai", search_paths)
    if not spec or not spec.origin:
        return None
    real_init = Path(spec.origin).resolve()
    if real_init == Path(__file__).resolve():
        return None
    real_spec = importlib.util.spec_from_file_location(
        "_real_openai",
        str(real_init),
        submodule_search_locations=[str(real_init.parent)],
    )
    if not real_spec or not real_spec.loader:
        return None
    module = importlib.util.module_from_spec(real_spec)
    sys.modules[real_spec.name] = module
    real_spec.loader.exec_module(module)
    return module


_REAL_OPENAI = None
_load_dotenv()
if not os.getenv("LOCAL_BASE_URL"):
    _REAL_OPENAI = _load_real_openai()
    if _REAL_OPENAI is not None:
        exported = getattr(_REAL_OPENAI, "__all__", None)
        if exported:
            globals().update({name: getattr(_REAL_OPENAI, name) for name in exported})
            __all__ = list(exported)
        else:
            for name in dir(_REAL_OPENAI):
                if not name.startswith("__"):
                    globals()[name] = getattr(_REAL_OPENAI, name)
            __all__ = [name for name in globals() if not name.startswith("_")]


if _REAL_OPENAI is None:
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


    def _is_local_ollama(endpoint):
        return (
            endpoint.startswith("http://localhost:11434/")
            or endpoint.startswith("http://127.0.0.1:11434/")
            or endpoint.startswith("http://host.docker.internal:11434/")
        )


    def _start_ollama_if_needed(endpoint):
        if not _is_local_ollama(endpoint):
            return False
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        except OSError:
            return False
        tags_url = endpoint.split("/v1/", 1)[0].rstrip("/") + "/api/tags"
        for _ in range(20):
            try:
                with urllib.request.urlopen(tags_url, timeout=2):
                    return True
            except Exception:
                time.sleep(0.5)
        return False


    class _ChatCompletions:
        def __init__(self, client: "OpenAI"):
            self._client = client

        def _post_with_system_python(self, endpoint, headers, payload):
            helper = Path(__file__).resolve().parent / "_https_post.py"
            request = json.dumps({
                "endpoint": endpoint,
                "headers": headers,
                "payload": payload,
                "timeout": self._client.timeout,
            })
            proc = subprocess.run(
                ["python", str(helper)],
                input=request.encode("utf-8"),
                capture_output=True,
                text=False,
                encoding=None,
                timeout=self._client.timeout + 10,
            )
            if proc.returncode != 0:
                stderr = proc.stderr.decode("utf-8", errors="replace").strip()
                stdout = proc.stdout.decode("utf-8", errors="replace").strip()
                raise RuntimeError(stderr or stdout or "HTTPS helper failed")
            return json.loads(proc.stdout.decode("utf-8"))

        def create(self, **kwargs):
            payload = dict(kwargs)
            if "max_completion_tokens" in payload and "max_tokens" not in payload:
                payload["max_tokens"] = payload.pop("max_completion_tokens")
            data = json.dumps(payload).encode("utf-8")
            endpoint = self._client.base_url.rstrip("/")
            if not endpoint.endswith("/chat/completions"):
                endpoint += "/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._client.api_key}",
            }
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=self._client.timeout) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
            except Exception as exc:
                if _start_ollama_if_needed(endpoint):
                    with urllib.request.urlopen(req, timeout=self._client.timeout) as resp:
                        body = json.loads(resp.read().decode("utf-8"))
                elif not endpoint.startswith("https://"):
                    raise
                else:
                    body = self._post_with_system_python(endpoint, headers, payload)
            return _to_obj(body)


    class _Chat:
        def __init__(self, client: "OpenAI"):
            self.completions = _ChatCompletions(client)


    class OpenAI:
        def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float | None = None, **_kwargs):
            self.api_key = api_key or os.getenv("OPENAI_API_KEY") or "ollama"
            if base_url:
                self.base_url = base_url
            elif os.getenv("LOCAL_BASE_URL"):
                self.base_url = os.getenv("LOCAL_BASE_URL")
            else:
                self.base_url = "https://api.openai.com/v1"
            self.timeout = timeout or 120
            self.chat = _Chat(self)


    __all__ = ["OpenAI"]
