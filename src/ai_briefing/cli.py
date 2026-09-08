import httpx
from dotenv import load_dotenv

from ai_briefing.runner import run


def main() -> int:
    load_dotenv()
    with httpx.Client(timeout=httpx.Timeout(180.0, connect=10.0)) as client:
        return run(http=client)
