from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


@dataclass(frozen=True)
class Feed:
    """系统可以配置的 RSS/Atom 源。"""

    name: str
    url: str


FEEDS: tuple[Feed, ...] = (
    Feed("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    Feed(
        "The Verge AI",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    ),
    Feed("36氪快讯", "https://www.36kr.com/feed-newsflash"),
    Feed("OpenAI News", "https://openai.com/news/rss.xml"),
    Feed("DeepMind Blog", "https://deepmind.google/blog/rss.xml"),
)


@dataclass(frozen=True)
class Settings:
    """模型接口与微信推送所需的配置。"""

    openai_api_key: str
    openai_base_url: str
    openai_model: str
    serverchan_sendkey: str


def load_settings(environ: Mapping[str, str]) -> Settings | None:
    """从环境变量构造 Settings。缺少 API 密钥或模型名时返回 None。"""
    key = (environ.get("OPENAI_API_KEY") or "").strip()
    model = (environ.get("OPENAI_MODEL") or "").strip()
    if not key or not model:
        return None
    base_url = (environ.get("OPENAI_BASE_URL") or "").strip() or DEFAULT_OPENAI_BASE_URL
    sendkey = (environ.get("SERVERCHAN_SENDKEY") or "").strip()
    return Settings(
        openai_api_key=key,
        openai_base_url=base_url,
        openai_model=model,
        serverchan_sendkey=sendkey,
    )
