from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

import httpx

from .config import Settings

SYSTEM_PROMPT = """你是一份只给读者自己看的中文 AI/科技行业早报编辑。根据用户消息里提供的当日条目，提取一篇叙事早报。

硬性规则：
- 只使用用户消息里的条目。不准编造新闻，不准添加条目里没有的事实、数字、链接。
- 不准输出原文摘要的翻译体堆砌；每条写「发生了什么 + 为什么对行业重要」。
- 选 5–8 条。丢掉明显不是 AI/科技产业的条目（娱乐、地产、个股行情）。同一事件多源只留一条，不够 5 条就如实少写。
- 不写「为什么适合你」，不喊口号，不分组小标题。
- `card_title` 单行、无换行，像服务号通知标题，点出当天主线。
- `url` 必须原样复制自输入，不准改写或编造。
- 只输出一个 JSON 对象，不要 markdown 围栏，不要解释。

JSON 形状：
{
  "card_title": "string",
  "lead": "string",
  "items": [
    {
      "headline": "string",
      "why": "string",
      "source": "string",
      "url": "string",
      "published": "string"
    }
  ],
  "closing": "string"
}

`lead`：一段话，说明今天是哪类日子、选了几条、缺了什么。
`why`：一小段，接在标题后面，不是标题的重复。
`closing`：可空字符串。用于「国内无单独信号」一类收束。
`source` 用输入里的来源名。`published` 用输入里的日期，没有则空字符串。
"""


def extract_content(
    http: httpx.Client,
    settings: Settings,
    report_date: date,
    entries: Sequence[Mapping[str, str]],
) -> dict[str, Any] | None:
    """根据报告日和条目请求模型，返回早报 JSON；失败返回 None。"""
    url = settings.openai_base_url.rstrip("/") + "/chat/completions"
    user_payload = {
        "report_date": report_date.isoformat(),
        "items": [
            {
                "source": item["source"],
                "title": item["title"],
                "summary": item["summary"],
                "url": item["url"],
                "published": item["published"],
            }
            for item in entries
        ],
    }
    try:
        response = http.post(
            url,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": json.dumps(user_payload, ensure_ascii=False),
                    },
                ],
            },
            timeout=180.0,
        )
        response.raise_for_status()
        payload = response.json()
        briefing = json.loads(payload["choices"][0]["message"]["content"])
        return _accepted_briefing(briefing, entries)
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return None


def _accepted_briefing(
    briefing: Any,
    entries: Sequence[Mapping[str, str]],
) -> dict[str, Any] | None:
    if not isinstance(briefing, dict):
        return None
    items = briefing.get("items")
    if not isinstance(items, list):
        return None
    allowed_urls = {item["url"] for item in entries}
    for item in items:
        if not isinstance(item, dict) or item.get("url") not in allowed_urls:
            return None
    return briefing
