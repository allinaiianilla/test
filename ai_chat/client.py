from openai import OpenAI
import httpx

from config import *

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    http_client=httpx.Client(
        trust_env=False,
        timeout=300
    )
)


def chat(messages):
    """
    返回：

    (answer, is_stream)

    answer 为最终完整字符串
    is_stream 表示是否成功使用了 Streaming
    """

    answer = ""

    try:

        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            stream=True,
        )

        print("\nAI> ", end="", flush=True)

        for chunk in completion:

            # 兼容很多 OpenAI Compatible API
            if not hasattr(chunk, "choices"):
                continue

            if not chunk.choices:
                continue

            choice = chunk.choices[0]

            if not hasattr(choice, "delta"):
                continue

            delta = choice.delta

            if delta is None:
                continue

            content = delta.content

            if content is None:
                continue

            print(content, end="", flush=True)

            answer += content

        print()

        return answer, True

    except Exception:

        # 自动回退普通模式
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            stream=False,
        )

        answer = response.choices[0].message.content

        return answer, False