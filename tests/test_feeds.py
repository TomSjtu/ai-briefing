from datetime import date

from ai_briefing.config import Feed
from ai_briefing.feeds import SUMMARY_MAX_CHARS, _window_entries

REPORT_DAY = date(2026, 9, 7)
FEED = Feed(
    source_id="example",
    name="Example",
    url="https://example.com/feed",
)
PUB_DATE = "Sun, 06 Sep 2026 16:30:00 GMT"
ATOM_PUBLISHED = "2026-09-07T08:00:00Z"
ITEM_URL = "https://example.com/story"


def _rss(*, summary: str, content: str | None = None) -> bytes:
    encoded = ""
    if content is not None:
        encoded = f"<content:encoded><![CDATA[{content}]]></content:encoded>"
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">'
        "<channel><title>Example</title><item>"
        "<title>Example story</title>"
        f"<link>{ITEM_URL}</link>"
        f"<description>{summary}</description>"
        f"<pubDate>{PUB_DATE}</pubDate>"
        f"{encoded}"
        "</item></channel></rss>"
    ).encode()


def _atom(*, summary: str, content: str | None = None) -> bytes:
    body = ""
    if content is not None:
        body = f'<content type="html"><![CDATA[{content}]]></content>'
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        "<title>Example</title><entry>"
        "<title>Example story</title>"
        f'<link href="{ITEM_URL}"/>'
        f"<summary>{summary}</summary>"
        f"{body}"
        f"<published>{ATOM_PUBLISHED}</published>"
        "</entry></feed>"
    ).encode()


def _summaries(xml: bytes) -> list[str]:
    return [item["summary"] for item in _window_entries(FEED, xml, REPORT_DAY)]


def test_prefers_content_encoded_over_description():
    xml = _rss(
        summary="Two newspapers allege copyrighted news text was used to train models.",
        content=(
            "<p>The Seattle Times and Newsday filed a lawsuit alleging OpenAI used "
            "copyrighted news text to train models without a license.</p>"
        ),
    )
    assert _summaries(xml) == [
        "The Seattle Times and Newsday filed a lawsuit alleging OpenAI used "
        "copyrighted news text to train models without a license."
    ]


def test_prefers_atom_content_over_summary():
    xml = _atom(
        summary="A short teaser.",
        content="<p>The article body explains the incident in detail.</p>",
    )
    assert _summaries(xml) == ["The article body explains the incident in detail."]


def test_html_description_is_stripped_when_no_content():
    xml = _rss(
        summary=(
            "<p>Meta launched <strong>Muse</strong>, a system-level assistant "
            "that can read SMS and calendars.</p>"
        ),
    )
    assert _summaries(xml) == [
        "Meta launched Muse, a system-level assistant that can read SMS and calendars."
    ]


def test_plain_description_is_kept_when_no_content():
    xml = _rss(summary="A collaboration announcement with news organizations in Ukraine.")
    assert _summaries(xml) == [
        "A collaboration announcement with news organizations in Ukraine."
    ]


def test_long_content_encoded_is_truncated():
    xml = _rss(summary="teaser", content="<p>" + ("A" * (SUMMARY_MAX_CHARS + 200)) + "</p>")
    summaries = _summaries(xml)
    assert summaries == ["A" * SUMMARY_MAX_CHARS]
