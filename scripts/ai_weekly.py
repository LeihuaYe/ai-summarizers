"""
AI Weekly Digest: AI Progress and AI Evaluation
Searches the web via Tavily and synthesizes with Claude API.
Saves output to digests/ai-weekly-YYYY-MM-DD.md
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
    "AI Progress": [
        "new LLM model release AI lab announcement 2026",
        "LLM architecture breakthrough training technique multimodal AI 2026",
        "open source model release AI agents 2026",
    ],
    "AI Evaluation": [
        "new LLM benchmark evaluation framework 2026",
        "LLM-as-judge evaluation methodology safety alignment eval 2026",
        "model leaderboard RLHF evaluation AI capability assessment 2026",
    ],
}

PRIORITY_SOURCES = [
    "anthropic.com",
    "openai.com",
    "deepmind.google",
    "ai.meta.com",
    "mistral.ai",
    "huggingface.co",
    "arxiv.org",
    "paperswithcode.com",
    "thegradient.pub",
]


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
    for f in sorted(DIGEST_DIR.glob("ai-weekly-*.md")):
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
Generate a weekly AI digest for Leihua Ye, a Senior Data Scientist who wants to stay current on AI progress and AI evaluation.

Use this exact format:

---
# AI Weekly — {today}

## AI Progress
- **[Title]** — [Source] | [URL]
  > One-sentence summary of key development

## AI Evaluation
- **[Title]** — [Source] | [URL]
  > One-sentence summary of key development

## This Week's Highlight
**[Title of most significant item]**
[2–3 sentences explaining why this matters, especially for practitioners building or evaluating AI systems]

---
*Generated {today}*
---

Rules:
- Only include items from the search results provided — do not fabricate titles or URLs
- 4–6 items per section; if fewer strong results exist, write "Light week for [topic]" with fewer items
- Prioritize: Anthropic, OpenAI, Google DeepMind, Meta AI, Mistral, Hugging Face blogs; arXiv; Papers With Code
- Source label should be the domain name (e.g. arxiv.org, anthropic.com)
- For "This Week's Highlight", pick the single most impactful development for someone building or evaluating AI systems
"""
    return context


def main():
    today = datetime.date.today().isoformat()
    DIGEST_DIR.mkdir(exist_ok=True)

    seen_urls = get_seen_urls()
    all_results = collect_results(seen_urls)

    prompt = build_prompt(today, all_results)

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    digest = response.content[0].text
    output_path = DIGEST_DIR / f"ai-weekly-{today}.md"
    output_path.write_text(digest, encoding="utf-8")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
