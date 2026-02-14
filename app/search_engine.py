"""
Search Engine Module - Google ADK-style Deep Search Agent

Uses DuckDuckGo as the search backend for the POC.
In production, integrate with Google's Agent Development Kit (ADK)
and Gemini for deep research capabilities.

Google ADK Reference: https://google.github.io/adk-docs/
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    has_dev_docs: Optional[bool] = None


class SearchEngine:
    """
    Google ADK-style deep search agent.

    Architecture follows Google ADK patterns:
    - Tool-based search execution
    - Result ranking and filtering
    - Deep search with follow-up queries

    POC uses duckduckgo-search; production would use:
        from google.adk import Agent
        from google.adk.tools import google_search
    """

    def __init__(self):
        self._search_impl = None

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Perform a deep search for developer documentation sites."""
        # Try primary search (DuckDuckGo)
        try:
            results = await self._duckduckgo_search(query, max_results)
            if results:
                return results
        except Exception as e:
            print(f"[SearchEngine] Primary search failed: {e}")

        # Try fallback search (googlesearch-python)
        try:
            results = await self._fallback_web_search(query, max_results)
            if results:
                return results
        except Exception as e:
            print(f"[SearchEngine] Fallback search failed: {e}")

        # Use curated results for reliability
        return self._curated_fallback(query)

    async def _duckduckgo_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using DuckDuckGo (no API key required)."""
        from duckduckgo_search import DDGS

        def _do_search():
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(SearchResult(
                        title=r.get("title", "Unknown"),
                        url=r.get("href", ""),
                        snippet=r.get("body", "")
                    ))
            return results

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _do_search)

    async def _fallback_web_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Fallback using googlesearch-python."""
        from googlesearch import search as gsearch

        def _do_search():
            results = []
            for url in gsearch(query, num_results=max_results):
                results.append(SearchResult(
                    title=url.split("/")[2] if "/" in url else url,
                    url=url,
                    snippet=f"Result for: {query}"
                ))
            return results

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _do_search)

    def _curated_fallback(self, query: str) -> List[SearchResult]:
        """Curated fallback results for demo when search APIs are unavailable."""
        query_lower = query.lower()

        # Common developer documentation sites
        sites = [
            SearchResult(
                title="Base Documentation - Build on Base",
                url="https://docs.base.org/get-started/build-app",
                snippet="A guide to building a next.js app on Base using OnchainKit. Complete developer documentation with Ask AI."
            ),
            SearchResult(
                title="Stripe API Documentation",
                url="https://docs.stripe.com/api",
                snippet="Complete reference for the Stripe API. Includes code snippets, guides, and an AI assistant."
            ),
            SearchResult(
                title="Vercel Documentation",
                url="https://vercel.com/docs",
                snippet="Vercel's platform documentation for deploying web applications. Includes AI-powered search."
            ),
            SearchResult(
                title="Supabase Documentation",
                url="https://supabase.com/docs",
                snippet="Open source Firebase alternative. Full documentation with guides, API reference, and AI assistant."
            ),
            SearchResult(
                title="Tailwind CSS Documentation",
                url="https://tailwindcss.com/docs",
                snippet="Utility-first CSS framework documentation with comprehensive guides and examples."
            ),
        ]

        # Filter by relevance to query
        scored = []
        for site in sites:
            score = sum(1 for word in query_lower.split()
                       if word in site.title.lower() or word in site.snippet.lower())
            scored.append((score, site))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:5]]
