from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_FEEDS_PATH = Path("config/feeds.yaml")


@dataclass(frozen=True)
class Feed:
    """系统可以配置的 RSS/Atom 源。"""

    source_id: str
    name: str
    url: str


def load_feeds(path: str | Path | None = None) -> tuple[Feed, ...]:
    """从 YAML 读取信息源。缺少文件、字段不合法或列表为空时抛出 ValueError。"""
    config_path = Path(path) if path is not None else DEFAULT_FEEDS_PATH
    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    raw_feeds = loaded.get("feeds", [])
    feeds: list[Feed] = []
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for raw in raw_feeds:
        source_id = str(raw.get("id") or raw.get("source_id") or "").strip()
        name = str(raw.get("name") or "").strip()
        url = str(raw.get("url") or "").strip()
        seen_ids.add(source_id)
        seen_urls.add(url)
        feeds.append(Feed(source_id=source_id, name=name, url=url))
    return tuple(feeds)

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
