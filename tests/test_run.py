import json
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl
from zoneinfo import ZoneInfo

import httpx

from ai_briefing.cli import main as cli_main
from ai_briefing.runner import run

BEIJING = ZoneInfo("Asia/Shanghai")

ENTRIES = [
    {
        "source": "TechCrunch",
        "title": "Seattle Times and Newsday sue OpenAI over training data",
        "summary": "Two newspapers allege copyrighted news text was used to train models.",
        "url": "https://techcrunch.com/example-seattle-times",
        "published": "2026-09-06",
    },
    {
        "source": "The Verge",
        "title": "OpenAI says German wiki material was involved in an internal incident",
        "summary": "The company disclosed that wiki content was pulled into an internal accident review.",
        "url": "https://www.theverge.com/example-wiki-incident",
        "published": "2026-09-06",
    },
    {
        "source": "OpenAI News",
        "title": "OpenAI partners with Ukrainian newsrooms",
        "summary": "A collaboration announcement with news organizations in Ukraine.",
        "url": "https://openai.com/news/example-ukraine",
        "published": "2026-09-07",
    },
    {
        "source": "DeepMind",
        "title": "WeatherNext 3",
        "summary": "Update to DeepMind's weather model line.",
        "url": "https://deepmind.google/blog/example-weathernext",
        "published": "2026-09-03",
    },
    {
        "source": "36氪",
        "title": "某地产项目开盘去化率创新高",
        "summary": "与 AI/科技无关的快讯。",
        "url": "https://www.36kr.com/example-real-estate",
        "published": "2026-09-07",
    },
]

EXTRACT_JSON = {
    "card_title": "AI早报｜诉讼、模型事故、官方便携，同日挤在一起",
    "lead": "今天不是发布会日，是规则和事故日。美国两家地方报把 OpenAI 告上法庭；OpenAI 自己承认德国维基出现过一次 incident。公司侧只有一篇合作稿和一篇气象模型更新，声音比新闻小。",
    "items": [
        {
            "headline": "西雅图时报与 Newsday 起诉 OpenAI",
            "why": "指控围绕训练语料是否覆盖受版权保护的新闻文本。若法院接受「模型训练 = 复制」，后面一段时间的授权谈判会比模型参数更值钱。",
            "source": "TechCrunch",
            "url": "https://techcrunch.com/example-seattle-times",
            "published": "2026-09-06",
        },
        {
            "headline": "OpenAI 披露德国维基材料被错误纳入一次内部事故",
            "why": "它自己先说出来，说明「训练数据从哪来」已经从媒体质疑变成公司必须记账的事项。",
            "source": "The Verge",
            "url": "https://www.theverge.com/example-wiki-incident",
            "published": "2026-09-06",
        },
        {
            "headline": "OpenAI 与乌克兰新闻机构签合作",
            "why": "产品没变，叙事在变：从「我们用了新闻」转到「我们跟新闻业合作」。和上面两则诉讼放在同一天，对照意义大于合作本身。",
            "source": "OpenAI News",
            "url": "https://openai.com/news/example-ukraine",
            "published": "2026-09-07",
        },
        {
            "headline": "DeepMind 更新 WeatherNext 3",
            "why": "气象模型是少数能直接接到政府与产业合同的 AI 产品线，比聊天模型更接近「行业」。",
            "source": "DeepMind",
            "url": "https://deepmind.google/blog/example-weathernext",
            "published": "2026-09-03",
        },
    ],
    "closing": "国内快讯今天没有单独能抬起来的 AI 政策或大额融资。",
}

VARIANT_A = """# AI 科技早报 · 9 月 7 日

今天不是发布会日，是规则和事故日。美国两家地方报把 OpenAI 告上法庭；OpenAI 自己承认德国维基出现过一次 incident。公司侧只有一篇合作稿和一篇气象模型更新，声音比新闻小。

**西雅图时报与 Newsday 起诉 OpenAI。** 指控围绕训练语料是否覆盖受版权保护的新闻文本。若法院接受「模型训练 = 复制」，后面一段时间的授权谈判会比模型参数更值钱。
来源：TechCrunch · [原文](https://techcrunch.com/example-seattle-times)

**OpenAI 披露德国维基材料被错误纳入一次内部事故。** 它自己先说出来，说明「训练数据从哪来」已经从媒体质疑变成公司必须记账的事项。
来源：The Verge · [原文](https://www.theverge.com/example-wiki-incident)

**OpenAI 与乌克兰新闻机构签合作。** 产品没变，叙事在变：从「我们用了新闻」转到「我们跟新闻业合作」。和上面两则诉讼放在同一天，对照意义大于合作本身。
来源：OpenAI News · [原文](https://openai.com/news/example-ukraine)

**DeepMind 更新 WeatherNext 3。** 气象模型是少数能直接接到政府与产业合同的 AI 产品线，比聊天模型更接近「行业」。
来源：DeepMind · [原文](https://deepmind.google/blog/example-weathernext)

国内快讯今天没有单独能抬起来的 AI 政策或大额融资。
"""


FEED_URLS = (
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.36kr.com/feed-newsflash",
    "https://openai.com/news/rss.xml",
    "https://deepmind.google/blog/rss.xml",
    "https://blog.google/innovation-and-ai/technology/ai/rss/",
    "https://www.technologyreview.com/feed/",
    "https://github.com/google-gemini/gemini-cli/releases.atom",
    "https://github.com/openai/codex/releases.atom",
    "https://github.com/anthropics/claude-code/releases.atom",
)

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "feeds.yaml"

IN_WINDOW = {
    "techcrunch": {
        "title": "Seattle Times and Newsday sue OpenAI over training data",
        "summary": "Two newspapers allege copyrighted news text was used to train models.",
        "url": "https://techcrunch.com/example-seattle-times",
        "pubDate": "Sun, 06 Sep 2026 16:30:00 GMT",
    },
    "verge": {
        "title": "OpenAI says German wiki material was involved in an internal incident",
        "summary": "The company disclosed that wiki content was pulled into an internal accident review.",
        "url": "https://www.theverge.com/example-wiki-incident",
        "published": "2026-09-07T08:00:00Z",
    },
    "36kr": {
        "title": "某地产项目开盘去化率创新高",
        "summary": "与 AI/科技无关的快讯。",
        "url": "https://www.36kr.com/example-real-estate",
        "pubDate": "Mon, 07 Sep 2026 09:00:00 +0800",
    },
    "openai": {
        "title": "OpenAI partners with Ukrainian newsrooms",
        "summary": "A collaboration announcement with news organizations in Ukraine.",
        "url": "https://openai.com/news/example-ukraine",
        "pubDate": "Mon, 07 Sep 2026 10:00:00 +0800",
    },
    "deepmind": {
        "title": "WeatherNext 3 same-day note",
        "summary": "A same-day update to DeepMind's weather model line.",
        "url": "https://deepmind.google/blog/example-weathernext-same-day",
        "pubDate": "Mon, 07 Sep 2026 11:00:00 +0800",
    },
}

OUT_OF_WINDOW = {
    "techcrunch_utc_still_sep6_beijing": {
        "title": "A TechCrunch story from the previous Beijing day",
        "summary": "Published 15:30 GMT on Sep 6, which is still Sep 6 in Beijing.",
        "url": "https://techcrunch.com/example-previous-day",
        "pubDate": "Sun, 06 Sep 2026 15:30:00 GMT",
    },
    "openai_history": {
        "title": "Introducing the OpenAI API",
        "summary": "A 2015 announcement that must not enter extraction.",
        "url": "https://openai.com/news/example-2015-api",
        "pubDate": "Thu, 11 Jun 2015 12:00:00 GMT",
    },
}


def _rss(channel_title: str, items: list[dict[str, str]]) -> str:
    parts = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<rss version="2.0"><channel>',
        f"<title>{channel_title}</title>",
    ]
    for item in items:
        parts.append(
            "<item>"
            f"<title>{item['title']}</title>"
            f"<link>{item['url']}</link>"
            f"<description>{item['summary']}</description>"
            f"<pubDate>{item['pubDate']}</pubDate>"
            "</item>"
        )
    parts.append("</channel></rss>")
    return "".join(parts)


def _atom(feed_title: str, entries: list[dict[str, str]]) -> str:
    parts = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"<title>{feed_title}</title>",
    ]
    for entry in entries:
        parts.append(
            "<entry>"
            f"<title>{entry['title']}</title>"
            f'<link href="{entry["url"]}"/>'
            f"<summary>{entry['summary']}</summary>"
            f"<published>{entry['published']}</published>"
            "</entry>"
        )
    parts.append("</feed>")
    return "".join(parts)


FIVE_FEED_BODIES = {
    FEED_URLS[0]: _rss(
        "TechCrunch AI",
        [IN_WINDOW["techcrunch"], OUT_OF_WINDOW["techcrunch_utc_still_sep6_beijing"]],
    ),
    FEED_URLS[1]: _atom("The Verge AI", [IN_WINDOW["verge"]]),
    FEED_URLS[2]: _rss("36氪快讯", [IN_WINDOW["36kr"]]),
    FEED_URLS[3]: _rss(
        "OpenAI News",
        [IN_WINDOW["openai"], OUT_OF_WINDOW["openai_history"]],
    ),
    FEED_URLS[4]: _rss("DeepMind Blog", [IN_WINDOW["deepmind"]]),
    FEED_URLS[5]: _rss("Google AI", []),
    FEED_URLS[6]: _rss("MIT Technology Review", []),
    FEED_URLS[7]: _atom("Gemini CLI Releases", []),
    FEED_URLS[8]: _atom("OpenAI Codex Releases", []),
    FEED_URLS[9]: _atom("Claude Code Releases", []),
}

CREDENTIALS = {
    "OPENAI_API_KEY": "sk-test",
    "OPENAI_BASE_URL": "https://api.openai.com/v1",
    "OPENAI_MODEL": "gpt-4o-mini",
    "SERVERCHAN_SENDKEY": "SCT_test_key",
}


def _extract_ok(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "choices": [
                {
                    "message": {
                        "content": json.dumps(EXTRACT_JSON, ensure_ascii=False)
                    }
                }
            ]
        },
    )


def _extract_ok_with_input_urls(request: httpx.Request) -> httpx.Response:
    user = json.loads(_fields(request)["messages"][1]["content"])
    allowed = {item["url"] for item in user["items"]}
    briefing = json.loads(json.dumps(EXTRACT_JSON))
    briefing["items"] = [item for item in briefing["items"] if item["url"] in allowed]
    return httpx.Response(
        200,
        json={
            "choices": [
                {
                    "message": {
                        "content": json.dumps(briefing, ensure_ascii=False)
                    }
                }
            ]
        },
    )


def _push_ok(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"code": 0})


def _fields(request: httpx.Request) -> dict:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return json.loads(request.content)
    return dict(parse_qsl(request.content.decode(), keep_blank_values=True))



def test_missing_openai_api_key_exits_without_briefing_or_push(tmp_path, capsys):
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        return httpx.Response(200)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    code = run(
        reports_dir=reports_dir,
        environ={
            "OPENAI_MODEL": "gpt-4o-mini",
            "SERVERCHAN_SENDKEY": "SCT_test_key",
        },
        http=http,
    )

    captured = capsys.readouterr()
    assert code != 0
    assert "缺少模型凭证" in captured.err
    assert list(reports_dir.iterdir()) == []
    assert recorded == []


def test_missing_openai_model_exits_without_briefing_or_push(tmp_path, capsys):
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        return httpx.Response(200)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    code = run(
        reports_dir=reports_dir,
        environ={
            "OPENAI_API_KEY": "sk-test",
            "SERVERCHAN_SENDKEY": "SCT_test_key",
        },
        http=http,
    )

    captured = capsys.readouterr()
    assert code != 0
    assert "缺少模型凭证" in captured.err
    assert list(reports_dir.iterdir()) == []
    assert recorded == []


def test_valid_extract_json_writes_variant_a_briefing_then_pushes_wechat(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []
    files_at_push: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        if request.url.path.endswith("/chat/completions"):
            return _extract_ok(request)
        if request.url.host == "sctapi.ftqq.com":
            files_at_push.extend(sorted(p.name for p in reports_dir.iterdir()))
            return httpx.Response(200, json={"code": 0})
        return httpx.Response(404)

    http = httpx.Client(transport=httpx.MockTransport(handler))

    code = run(
        reports_dir=reports_dir,
        environ={
            "OPENAI_API_KEY": "sk-test",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4o-mini",
            "SERVERCHAN_SENDKEY": "SCT_test_key",
        },
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
        entries=ENTRIES,
    )

    assert code == 0
    markdown = (reports_dir / "2026-09-07.md").read_text(encoding="utf-8")
    sidecar = json.loads((reports_dir / "2026-09-07.json").read_text(encoding="utf-8"))
    assert markdown == VARIANT_A
    assert sidecar == EXTRACT_JSON
    assert "2026-09-07.md" in files_at_push
    assert "2026-09-07.json" in files_at_push

    pushes = [r for r in recorded if r.url.host == "sctapi.ftqq.com"]
    assert len(pushes) == 1
    assert str(pushes[0].url) == "https://sctapi.ftqq.com/SCT_test_key.send"
    assert pushes[0].method == "POST"
    body = _fields(pushes[0])
    assert body["title"] == EXTRACT_JSON["card_title"]
    assert "\n" not in body["title"]
    assert body["desp"] == VARIANT_A
    assert body["desp"] != json.dumps(EXTRACT_JSON, ensure_ascii=False)
    for url in (
        "https://techcrunch.com/example-seattle-times",
        "https://www.theverge.com/example-wiki-incident",
        "https://openai.com/news/example-ukraine",
        "https://deepmind.google/blog/example-weathernext",
    ):
        assert url in body["desp"]


def test_five_feeds_send_beijing_day_window_entries_to_extract(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_briefing.config.DEFAULT_FEEDS_PATH", DEFAULT_CONFIG)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        url = str(request.url)
        if url in FIVE_FEED_BODIES:
            return httpx.Response(200, text=FIVE_FEED_BODIES[url])
        if request.url.path.endswith("/chat/completions"):
            return _extract_ok_with_input_urls(request)
        if request.url.host == "sctapi.ftqq.com":
            return _push_ok(request)
        return httpx.Response(404)

    http = httpx.Client(transport=httpx.MockTransport(handler))

    code = run(
        reports_dir=reports_dir,
        environ=CREDENTIALS,
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
    )

    assert code == 0
    requested = [str(r.url) for r in recorded if r.method == "GET"]
    assert requested == list(FEED_URLS)
    assert all("qbitai" not in url for url in requested)
    assert all("https://36kr.com/" not in url for url in requested)

    extracts = [r for r in recorded if r.url.path.endswith("/chat/completions")]
    assert len(extracts) == 1
    user = json.loads(_fields(extracts[0])["messages"][1]["content"])
    assert user["report_date"] == "2026-09-07"
    assert [item["url"] for item in user["items"]] == [
        IN_WINDOW["techcrunch"]["url"],
        IN_WINDOW["verge"]["url"],
        IN_WINDOW["36kr"]["url"],
        IN_WINDOW["openai"]["url"],
        IN_WINDOW["deepmind"]["url"],
    ]
    assert user["items"][0]["source"] == "TechCrunch AI"
    assert user["items"][1]["source"] == "The Verge AI"
    assert user["items"][2]["source"] == "36氪快讯"
    assert user["items"][3]["source"] == "OpenAI News"
    assert user["items"][4]["source"] == "DeepMind Blog"
    assert all(item["published"] == "2026-09-07" for item in user["items"])
    assert OUT_OF_WINDOW["openai_history"]["url"] not in {
        item["url"] for item in user["items"]
    }
    assert OUT_OF_WINDOW["techcrunch_utc_still_sep6_beijing"]["url"] not in {
        item["url"] for item in user["items"]
    }


def test_feed_http_redirect_still_collects_window_entries(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_briefing.config.DEFAULT_FEEDS_PATH", DEFAULT_CONFIG)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []
    moved = FEED_URLS[0] + "moved/"

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        url = str(request.url)
        if url == FEED_URLS[0]:
            return httpx.Response(301, headers={"location": moved})
        if url == moved:
            return httpx.Response(200, text=FIVE_FEED_BODIES[FEED_URLS[0]])
        if url in FIVE_FEED_BODIES:
            return httpx.Response(200, text=FIVE_FEED_BODIES[url])
        if request.url.path.endswith("/chat/completions"):
            return _extract_ok_with_input_urls(request)
        if request.url.host == "sctapi.ftqq.com":
            return _push_ok(request)
        return httpx.Response(404)

    http = httpx.Client(transport=httpx.MockTransport(handler))

    code = run(
        reports_dir=reports_dir,
        environ=CREDENTIALS,
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
    )

    assert code == 0
    requested = [str(r.url) for r in recorded if r.method == "GET"]
    assert requested[0] == FEED_URLS[0]
    assert moved in requested
    extracts = [r for r in recorded if r.url.path.endswith("/chat/completions")]
    assert len(extracts) == 1
    user = json.loads(_fields(extracts[0])["messages"][1]["content"])
    assert IN_WINDOW["techcrunch"]["url"] in {item["url"] for item in user["items"]}


def test_one_feed_failure_still_extracts_remaining_and_pushes(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_briefing.config.DEFAULT_FEEDS_PATH", DEFAULT_CONFIG)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []
    files_at_push: list[str] = []
    dead = FEED_URLS[3]

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        url = str(request.url)
        if url == dead:
            return httpx.Response(500)
        if url in FIVE_FEED_BODIES:
            return httpx.Response(200, text=FIVE_FEED_BODIES[url])
        if request.url.path.endswith("/chat/completions"):
            return _extract_ok_with_input_urls(request)
        if request.url.host == "sctapi.ftqq.com":
            files_at_push.extend(sorted(p.name for p in reports_dir.iterdir()))
            return _push_ok(request)
        return httpx.Response(404)

    http = httpx.Client(transport=httpx.MockTransport(handler))

    code = run(
        reports_dir=reports_dir,
        environ=CREDENTIALS,
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
    )

    assert code == 0
    extracts = [r for r in recorded if r.url.path.endswith("/chat/completions")]
    assert len(extracts) == 1
    user = json.loads(_fields(extracts[0])["messages"][1]["content"])
    urls = [item["url"] for item in user["items"]]
    assert IN_WINDOW["openai"]["url"] not in urls
    assert urls == [
        IN_WINDOW["techcrunch"]["url"],
        IN_WINDOW["verge"]["url"],
        IN_WINDOW["36kr"]["url"],
        IN_WINDOW["deepmind"]["url"],
    ]
    assert (reports_dir / "2026-09-07.md").is_file()
    assert (reports_dir / "2026-09-07.json").is_file()
    assert "2026-09-07.md" in files_at_push
    pushes = [r for r in recorded if r.url.host == "sctapi.ftqq.com"]
    assert len(pushes) == 1


def test_all_feeds_fail_exits_without_extract_or_push(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("ai_briefing.config.DEFAULT_FEEDS_PATH", DEFAULT_CONFIG)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        if str(request.url) in FEED_URLS:
            return httpx.Response(500)
        return httpx.Response(200)

    http = httpx.Client(transport=httpx.MockTransport(handler))

    code = run(
        reports_dir=reports_dir,
        environ=CREDENTIALS,
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
    )

    captured = capsys.readouterr()
    assert code != 0
    assert "获取信息源失败" in captured.err
    assert list(reports_dir.iterdir()) == []
    assert [r for r in recorded if r.url.path.endswith("/chat/completions")] == []
    assert [r for r in recorded if r.url.host == "sctapi.ftqq.com"] == []
    assert {str(r.url) for r in recorded} == set(FEED_URLS)


def test_html_challenge_pages_count_as_all_feeds_failed(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("ai_briefing.config.DEFAULT_FEEDS_PATH", DEFAULT_CONFIG)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []
    challenge = (
        "<!DOCTYPE html><html><head><title>challenge</title></head>"
        "<body>captcha</body></html>"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        if str(request.url) in FEED_URLS:
            return httpx.Response(
                200, text=challenge, headers={"content-type": "text/html"}
            )
        return httpx.Response(200)

    http = httpx.Client(transport=httpx.MockTransport(handler))

    code = run(
        reports_dir=reports_dir,
        environ=CREDENTIALS,
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
    )

    captured = capsys.readouterr()
    assert code != 0
    assert "获取信息源失败" in captured.err
    assert list(reports_dir.iterdir()) == []
    assert [r for r in recorded if r.url.path.endswith("/chat/completions")] == []
    assert [r for r in recorded if r.url.host == "sctapi.ftqq.com"] == []


def test_invalid_feeds_yaml_exits_without_fetch(tmp_path, capsys, monkeypatch):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    config_file = tmp_path / "feeds.yaml"
    config_file.write_text("feeds: []\n", encoding="utf-8")
    monkeypatch.setattr("ai_briefing.config.DEFAULT_FEEDS_PATH", config_file)
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        return httpx.Response(200)

    http = httpx.Client(transport=httpx.MockTransport(handler))

    code = run(
        reports_dir=reports_dir,
        environ=CREDENTIALS,
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
    )

    captured = capsys.readouterr()
    assert code != 0
    assert list(reports_dir.iterdir()) == []
    assert recorded == []


def test_invalid_extract_json_exits_without_briefing_or_push(tmp_path, capsys):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        if request.url.path.endswith("/chat/completions"):
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "not-json"}}]},
            )
        return httpx.Response(200, json={"code": 0})

    http = httpx.Client(transport=httpx.MockTransport(handler))

    code = run(
        reports_dir=reports_dir,
        environ=CREDENTIALS,
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
        entries=ENTRIES,
    )

    captured = capsys.readouterr()
    assert code != 0
    assert "提取内容失败" in captured.err
    assert "推送失败" not in captured.err
    assert list(reports_dir.iterdir()) == []
    assert [r for r in recorded if r.url.host == "sctapi.ftqq.com"] == []


def test_hallucinated_url_exits_without_briefing_or_push(tmp_path, capsys):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []
    forged = json.loads(json.dumps(EXTRACT_JSON))
    forged["items"][0]["url"] = "https://example.com/not-in-input"

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        if request.url.path.endswith("/chat/completions"):
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(forged, ensure_ascii=False)
                            }
                        }
                    ]
                },
            )
        return httpx.Response(200, json={"code": 0})

    http = httpx.Client(transport=httpx.MockTransport(handler))

    code = run(
        reports_dir=reports_dir,
        environ=CREDENTIALS,
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
        entries=ENTRIES,
    )

    captured = capsys.readouterr()
    assert code != 0
    assert "提取内容失败" in captured.err
    assert "推送失败" not in captured.err
    assert list(reports_dir.iterdir()) == []
    assert [r for r in recorded if r.url.host == "sctapi.ftqq.com"] == []


def test_serverchan_http_failure_keeps_briefing_and_exits(tmp_path, capsys):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        if request.url.path.endswith("/chat/completions"):
            return _extract_ok(request)
        if request.url.host == "sctapi.ftqq.com":
            return httpx.Response(500, text="server error")
        return httpx.Response(404)

    http = httpx.Client(transport=httpx.MockTransport(handler))

    code = run(
        reports_dir=reports_dir,
        environ=CREDENTIALS,
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
        entries=ENTRIES,
    )

    captured = capsys.readouterr()
    assert code != 0
    assert "推送失败" in captured.err
    assert "提取内容失败" not in captured.err
    assert (reports_dir / "2026-09-07.md").read_text(encoding="utf-8") == VARIANT_A
    assert json.loads((reports_dir / "2026-09-07.json").read_text(encoding="utf-8")) == EXTRACT_JSON
    assert [r for r in recorded if r.url.host == "sctapi.ftqq.com"]


def test_placeholder_sendkey_keeps_briefing_and_exits(tmp_path, capsys):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        if request.url.path.endswith("/chat/completions"):
            return _extract_ok(request)
        if request.url.host == "sctapi.ftqq.com":
            return _push_ok(request)
        return httpx.Response(404)

    http = httpx.Client(transport=httpx.MockTransport(handler))

    code = run(
        reports_dir=reports_dir,
        environ={**CREDENTIALS, "SERVERCHAN_SENDKEY": "SCT_REPLACE_ME"},
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
        entries=ENTRIES,
    )

    captured = capsys.readouterr()
    assert code != 0
    assert "推送失败" in captured.err
    assert "提取内容失败" not in captured.err
    assert (reports_dir / "2026-09-07.md").read_text(encoding="utf-8") == VARIANT_A
    assert json.loads((reports_dir / "2026-09-07.json").read_text(encoding="utf-8")) == EXTRACT_JSON
    assert [r for r in recorded if r.url.host == "sctapi.ftqq.com"] == []


def test_dry_run_writes_md_and_json_without_pushing(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        if request.url.path.endswith("/chat/completions"):
            return _extract_ok(request)
        if request.url.host == "sctapi.ftqq.com":
            return _push_ok(request)
        return httpx.Response(404)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    environ = {
        "OPENAI_API_KEY": CREDENTIALS["OPENAI_API_KEY"],
        "OPENAI_BASE_URL": CREDENTIALS["OPENAI_BASE_URL"],
        "OPENAI_MODEL": CREDENTIALS["OPENAI_MODEL"],
    }

    code = run(
        reports_dir=reports_dir,
        environ=environ,
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
        entries=ENTRIES,
        dry_run=True,
    )

    assert code == 0
    markdown = (reports_dir / "2026-09-07.md").read_text(encoding="utf-8")
    sidecar = json.loads((reports_dir / "2026-09-07.json").read_text(encoding="utf-8"))
    assert markdown == VARIANT_A
    assert sidecar == EXTRACT_JSON
    assert [r for r in recorded if r.url.host == "sctapi.ftqq.com"] == []
    assert [r for r in recorded if r.url.path.endswith("/chat/completions")]


def test_dry_run_skips_push_even_with_sendkey(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        if request.url.path.endswith("/chat/completions"):
            return _extract_ok(request)
        if request.url.host == "sctapi.ftqq.com":
            return _push_ok(request)
        return httpx.Response(404)

    http = httpx.Client(transport=httpx.MockTransport(handler))

    code = run(
        reports_dir=reports_dir,
        environ=CREDENTIALS,
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
        entries=ENTRIES,
        dry_run=True,
    )

    assert code == 0
    assert (reports_dir / "2026-09-07.md").read_text(encoding="utf-8") == VARIANT_A
    assert json.loads((reports_dir / "2026-09-07.json").read_text(encoding="utf-8")) == EXTRACT_JSON
    assert [r for r in recorded if r.url.host == "sctapi.ftqq.com"] == []


def test_cli_dry_run_passes_flag_to_runner(monkeypatch):
    seen: dict = {}

    def fake_run(*, http, dry_run=False, **_kwargs):
        seen["dry_run"] = dry_run
        seen["http"] = http
        return 0

    monkeypatch.setattr("ai_briefing.cli.run", fake_run)
    monkeypatch.setattr("ai_briefing.cli.load_dotenv", lambda: None)

    assert cli_main(["--dry-run"]) == 0
    assert seen["dry_run"] is True
    assert isinstance(seen["http"], httpx.Client)
    assert seen["http"].follow_redirects is True
    assert cli_main([]) == 0
    assert seen["dry_run"] is False


def test_missing_sendkey_writes_briefing_then_exits(tmp_path, capsys):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        if request.url.path.endswith("/chat/completions"):
            return _extract_ok(request)
        if request.url.host == "sctapi.ftqq.com":
            return _push_ok(request)
        return httpx.Response(404)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    environ = {
        "OPENAI_API_KEY": CREDENTIALS["OPENAI_API_KEY"],
        "OPENAI_BASE_URL": CREDENTIALS["OPENAI_BASE_URL"],
        "OPENAI_MODEL": CREDENTIALS["OPENAI_MODEL"],
    }

    code = run(
        reports_dir=reports_dir,
        environ=environ,
        http=http,
        now=datetime(2026, 9, 7, 8, 0, tzinfo=BEIJING),
        entries=ENTRIES,
    )

    captured = capsys.readouterr()
    assert code != 0
    assert "推送失败" in captured.err
    assert "提取内容失败" not in captured.err
    assert "缺少模型凭证" not in captured.err
    assert (reports_dir / "2026-09-07.md").read_text(encoding="utf-8") == VARIANT_A
    assert json.loads((reports_dir / "2026-09-07.json").read_text(encoding="utf-8")) == EXTRACT_JSON
    assert [r for r in recorded if r.url.host == "sctapi.ftqq.com"] == []
