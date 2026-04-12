# AI Summarizers — Claude Code Context

## Purpose
Automated weekly digests on AI progress and AI evaluation, generated via Claude API + Tavily web search. Output saved as markdown files in `digests/`.

## Run
```bash
# AI Weekly digest (model releases, benchmarks, eval research)
python scripts/ai_weekly.py

# Weekly review (broader AI + experimentation topics)
python scripts/weekly_review.py
```

## Architecture
- `scripts/ai_weekly.py` — searches Tavily across 6 queries, synthesizes with Claude API, saves to `digests/ai-weekly-YYYY-MM-DD.md`
- `scripts/weekly_review.py` — similar pipeline for broader weekly review
- `digests/` — output markdown files, one per week

## Dependencies
```bash
pip install -r requirements.txt  # anthropic, tavily-python
```

## Required Environment Variables
- `ANTHROPIC_API_KEY`
- `TAVILY_API_KEY`

## Output Format
Each digest covers:
- **AI Progress** — model releases, architecture breakthroughs, lab announcements
- **AI Evaluation** — new benchmarks, eval methodology, LLM-as-judge research
- **This Week's Highlight** — single most impactful development for practitioners

## GitHub
- Remote: `https://github.com/LeihuaYe/ai-summarizers.git`
- Push after every commit.
