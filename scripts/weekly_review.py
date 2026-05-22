"""
Weekly Research Digest: Experimentation, Causal Inference, AI Evaluation
Searches the web via Tavily and synthesizes with Claude API.
Saves output to digests/weekly-review-YYYY-MM-DD.md
"""

import os
import re
import sys
import datetime
from pathlib import Path

import anthropic
from tavily import TavilyClient

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

DIGEST_DIR = Path("digests")

SEARCH_QUERIES = {
    "Experimentation & A/B Testing": [
        "A/B testing online experimentation new research 2026",
        "CUPED variance reduction switchback experiments peeking problem",
        "experiment design statistical power network effects 2026",
    ],
    "Causal Inference": [
        "causal inference difference-in-differences new paper 2026",
        "synthetic control instrumental variables regression discontinuity 2026",
        "causal machine learning double ML debiased 2026",
    ],
    "AI Evaluation": [
        "LLM evaluation benchmark new 2026",
        "AI evaluation methodology LLM-as-judge alignment 2026",
        "model evaluation frameworks generative AI 2026",
    ],
}


def search(query: str) -> list[dict]:
    try:
        result = tavily.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            days=7,
        )
        return result.get("results", [])
    except Exception as e:
        print(f"Search failed for '{query}': {e}", file=sys.stderr)
        return []


def get_seen_urls() -> set:
    seen = set()
    for f in sorted(DIGEST_DIR.glob("weekly-review-*.md")):
        content = f.read_text(encoding="utf-8")
        seen.update(re.findall(r"https?://[^\s|>)\"']+", content))
    return seen


def collect_results(seen_urls: set) -> dict:
    all_results = {}
    for section, queries in SEARCH_QUERIES.items():
        seen_in_section = set(seen_urls)
        deduped = []
        for q in queries:
            for r in search(q):
                url = r.get("url", "")
                if url and url not in seen_in_section:
                    seen_in_section.add(url)
                    deduped.append(r)
        all_results[section] = deduped[:8]
    return all_results


def build_prompt(today: str, all_results: dict) -> str:
    context = f"Today is {today}.\n\n"
    for section, results in all_results.items():
        context += f"### {section} search results:\n"
        if results:
            for r in results:
                context += (
                    f"- Title: {r.get('title', 'N/A')}\n"
                    f"  URL: {r.get('url', '')}\n"
                    f"  Excerpt: {r.get('content', '')[:400]}\n\n"
                )
        else:
            context += "  (no results found)\n\n"

    context += f"""
Generate a weekly research digest for Leihua Ye, a Senior Data Scientist specializing in experimentation and causal inference.

Use this exact format:

---
# 📊 Weekly Research Digest — {today}

## Experimentation & A/B Testing
- **[Title]** — [Source] | [URL]
  > One-sentence summary of key insight

## Causal Inference
- **[Title]** — [Source] | [URL]
  > One-sentence summary of key insight

## AI Evaluation
- **[Title]** — [Source] | [URL]
  > One-sentence summary of key insight

## 💡 This Week's Highlight
[Pick the single most interesting finding across all three topics and explain why it matters to an experimentation practitioner]
---

Rules:
- Only include items from the search results provided — do not fabricate titles or URLs
- 3–5 items per section; if fewer strong results exist, write "Light week for [topic]" with 1–2 items
- Prefer: industry blogs (Netflix Tech, Airbnb Engineering, Meta Research, Google Research), arXiv, practitioner newsletters
- Source label should be the domain name (e.g. arxiv.org, netflixtechblog.com)
"""
    return context


def main():
    today = datetime.date.today().isoformat()
    DIGEST_DIR.mkdir(exist_ok=True)

    seen_urls = get_seen_urls()
    skipped = 0

    all_results = collect_results(seen_urls)
    for section, results in all_results.items():
        # Count how many raw candidates were filtered by deduplication
        for q in SEARCH_QUERIES[section]:
            pass  # dedup already done in collect_results

    prompt = build_prompt(today, all_results)

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    digest = response.content[0].text
    output_path = DIGEST_DIR / f"weekly-review-{today}.md"
    output_path.write_text(digest, encoding="utf-8")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
