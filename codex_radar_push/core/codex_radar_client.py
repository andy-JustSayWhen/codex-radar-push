import json
import ssl
from urllib.error import URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://codex-reset-radar.pages.dev"


def fetch_current_json(base_url: str = DEFAULT_BASE_URL, timeout: int = 30) -> dict:
    with _open_url(_request(f"{base_url.rstrip('/')}/current.json"), timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_html(base_url: str = DEFAULT_BASE_URL, timeout: int = 30) -> str:
    with _open_url(_request(f"{base_url.rstrip('/')}/"), timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _request(url: str) -> Request:
    return Request(url, headers={"User-Agent": "codex-radar-refresh-push/1.0"})


def _open_url(request: Request, timeout: int):
    try:
        return urlopen(request, timeout=timeout)
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ssl.SSLCertVerificationError):
            context = ssl._create_unverified_context()
            return urlopen(request, timeout=timeout, context=context)
        raise
