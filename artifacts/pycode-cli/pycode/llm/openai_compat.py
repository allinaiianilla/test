"""
OpenAI 兼容 API 的 LLM 实现。

支持所有兼容 OpenAI Chat Completions API 的服务：
- OpenAI (gpt-4o, gpt-4o-mini, etc.)
- 智谱 GLM (https://open.bigmodel.cn)
- DeepSeek (https://api.deepseek.com)
- Ollama 本地模型 (http://localhost:11434/v1)
- 任何兼容 /v1/chat/completions 的 API

用法::

    from pycode.llm import OpenAICompatibleLLM

    llm = OpenAICompatibleLLM(
        api_key="sk-xxx",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini"
    )

    # 非流式
    reply = llm.chat([
        {"role": "user", "content": "写一个快速排序"}
    ])

    # 流式
    for chunk in llm.chat_stream([...]):
        print(chunk, end="")
"""

import json
import ssl
import urllib.request
import urllib.error
from typing import Iterator, Optional

from .base import BaseLLM, LLMError, LLMTimeoutError, LLMAuthError


# ============================================================
# 实现
# ============================================================
class OpenAICompatibleLLM(BaseLLM):
    """
    OpenAI Chat Completions API 兼容实现。

    使用标准库 urllib，零外部依赖。

    Args:
        api_key: API 密钥
        base_url: API 基础 URL，会自动拼接 /chat/completions
        model: 模型名称
        max_tokens: 最大输出 token 数
        temperature: 随机性 (0-2)，越低越确定
        timeout: 请求超时秒数
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: int = 60,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._timeout = timeout

        # 完整的 API endpoint
        self._endpoint = f"{self._base_url}/chat/completions"

    # ---- 公共接口 ----
    @property
    def model_name(self) -> str:
        return self._model

    def chat(self, messages: list[dict]) -> str:
        """
        发送消息并返回完整回复。

        Args:
            messages: [{"role": "user", "content": "..."}, ...]

        Returns:
            LLM 文本回复

        Raises:
            LLMAuthError: 认证失败
            LLMTimeoutError: 请求超时
            LLMError: 其他错误
        """
        payload = self._build_payload(messages, stream=False)
        response = self._send_request(payload)

        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise LLMError(f"意外响应格式: {response.get('error', str(e))}")

    def chat_stream(self, messages: list[dict]) -> Iterator[str]:
        """
        流式聊天，逐 token yield 文本片段。

        注意：标准库 urllib 对流式支持有限，
        这里用 SSE 手动解析。如果流式失败，自动降级为非流式。
        """
        payload = self._build_payload(messages, stream=True)
        try:
            yield from self._stream_request(payload)
        except Exception:
            # 降级：如果流式失败，用非流式返回
            yield self.chat(messages)

    # ---- 内部实现 ----
    def _build_payload(self, messages: list[dict], stream: bool) -> dict:
        """构建 API 请求体"""
        return {
            "model": self._model,
            "messages": messages,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "stream": stream,
        }

    def _send_request(self, payload: dict) -> dict:
        """发送 HTTP 请求并解析 JSON 响应"""
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        req = urllib.request.Request(
            self._endpoint,
            data=data,
            headers=headers,
            method="POST",
        )

        try:
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=self._timeout, context=ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 401:
                raise LLMAuthError(f"API Key 无效或已过期 ({body[:200]})")
            raise LLMError(f"HTTP {e.code}: {body[:300]}")
        except urllib.error.URLError as e:
            raise LLMError(f"网络错误: {e.reason}")
        except TimeoutError:
            raise LLMTimeoutError(f"请求超时 ({self._timeout}s)")

    def _stream_request(self, payload: dict) -> Iterator[str]:
        """流式请求的 SSE 解析"""
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "text/event-stream",
        }

        req = urllib.request.Request(
            self._endpoint,
            data=data,
            headers=headers,
            method="POST",
        )

        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=self._timeout, context=ctx) as resp:
            buffer = ""
            while True:
                chunk = resp.read(1024)
                if not chunk:
                    break
                chunk_text = chunk.decode("utf-8", errors="replace")
                buffer += chunk_text

                # 按行解析 SSE
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        return
                    try:
                        parsed = json.loads(data_str)
                        delta = parsed["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    def __repr__(self) -> str:
        return (f"OpenAICompatibleLLM(model={self._model}, "
                f"endpoint={self._base_url})")
