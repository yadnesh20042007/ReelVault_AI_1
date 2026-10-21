from dataclasses import dataclass, field
from functools import lru_cache
from urllib.parse import urlparse

from langchain_core.tools import tool
from tavily import TavilyClient

from app.config import get_settings
from app.services.tools.domain_rules import check_domain as _check_domain


@lru_cache
def get_tavily() -> TavilyClient:
    return TavilyClient(api_key=get_settings().tavily_api_key)


@dataclass
class ToolRun:
    """Everything the tools did in ONE deep cook. The Verdict Guard treats this as ground truth."""

    organizer: str = ""
    seen_urls: set[str] = field(default_factory=set)
    pages: dict[str, str] = field(default_factory=dict)
    search_results: dict[str, str] = field(default_factory=dict)
    domain_checks: dict[str, dict] = field(default_factory=dict)


def _host(url: str) -> str:
    return urlparse(url).hostname or ""


def build_tools(run: ToolRun, tavily: TavilyClient | None = None):
    tv = tavily or get_tavily()

    @tool
    def web_search(query: str, include_domains: list[str] | None = None) -> list[dict]:
        """Search the web with Tavily. Optionally restrict to include_domains (e.g. the organizer's site).
        Returns up to 5 results: title, url, snippet, domain."""
        kwargs = {"query": query, "max_results": 5, "search_depth": "basic"}
        if include_domains:
            kwargs["include_domains"] = include_domains
        resp = tv.search(**kwargs)
        hits = [
            {
                "title": r.get("title", ""),
                "url": r["url"],
                "snippet": (r.get("content") or "")[:300],
                "domain": _host(r["url"]),
            }
            for r in resp.get("results", [])
        ]
        run.seen_urls.update(h["url"] for h in hits)
        for hit in hits:
            run.search_results[hit["url"]] = "\n".join(part for part in (hit["title"], hit["snippet"]) if part).strip()
        return hits

    @tool
    def read_page(url: str) -> dict:
        """Read a public web page with Tavily Extract. Returns cleaned text (truncated to 6000 chars)."""
        resp = tv.extract(urls=[url])
        results = resp.get("results", [])
        if not results:
            raise ValueError(f"could not read page: {resp.get('failed_results')}")
        r = results[0]
        text = r.get("raw_content") or ""
        final = r.get("url", url)
        dc = _check_domain(final, run.organizer)
        for u in {url, final}:
            run.seen_urls.add(u)
            run.pages[u] = text
            run.domain_checks[u] = dc
        return {"url": final, "text": text[:6000]}

    @tool("check_domain")
    def check_domain_tool(url: str) -> dict:
        """Deterministic trust heuristics for a URL's domain (official suffix, shortener, bait/risky signals)."""
        dc = _check_domain(url, run.organizer)
        run.domain_checks.setdefault(url, dc)
        return dc

    return [web_search, read_page, check_domain_tool]
