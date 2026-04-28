"""
🔍 search_tool.py — Web Search Tool (DuckDuckGo)
==================================================
Free web search for the Market Researcher agent.
No API key needed — uses DuckDuckGo's API.
"""

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web using DuckDuckGo.

    Args:
        query: Search query string
        max_results: Number of results to return

    Returns:
        List of dicts with keys: title, url, snippet
    """
    if not HAS_DDGS:
        return [{
            "title": "Search unavailable",
            "url": "",
            "snippet": (
                "duckduckgo-search not installed. "
                "Run: pip install duckduckgo-search"
            ),
        }]

    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        return results

    except Exception as e:
        return [{
            "title": "Search error",
            "url": "",
            "snippet": f"Error: {type(e).__name__}: {e}",
        }]


def format_search_results(results: list[dict]) -> str:
    """Format search results into a readable string for the LLM."""
    if not results:
        return "No search results found."

    output = []
    for i, r in enumerate(results, 1):
        output.append(
            f"[{i}] {r['title']}\n"
            f"    URL: {r['url']}\n"
            f"    {r['snippet']}\n"
        )
    return "\n".join(output)


if __name__ == "__main__":
    print("Testing DuckDuckGo search...\n")
    results = search_web("electric bike rental startup failure")
    print(format_search_results(results))
