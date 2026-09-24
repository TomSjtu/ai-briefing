from __future__ import annotations

import json
import sys
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
- `item_time` 是信息源条目发布的北京时间，用它判断报道先后与事件进展，不要在早报中输出它。
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
  ]
}

`lead`：一段话，说明今天是哪类日子、选了几条、缺了什么。
`why`：一小段，接在标题后面，不是标题的重复。
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
                "item_time": item.get("item_time", ""),
            }
            for item in entries
        ],
    }
    print(
        f"[提取] 请求 {settings.openai_model}，当日条目 {len(entries)} 条",
        file=sys.stderr,
    )
    content: str | None = None
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
        content = payload["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            print(
                f"[提取] message.content 不是字符串：{type(content).__name__}",
                file=sys.stderr,
            )
            return None
        briefing = _loads_model_json(content)
        accepted = _accepted_briefing(briefing, entries)
        if accepted is not None:
            print(f"[提取] 完成，早报 {len(accepted['items'])} 条", file=sys.stderr)
        return accepted
    except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        print(f"[提取] 响应无法解析：{type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def _loads_model_json(raw: str) -> Any:
    """解析模型输出的 JSON。允许字符串内的裸换行等控制字符。"""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text, strict=False)


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
    briefing.pop("closing", None)
    return briefing
