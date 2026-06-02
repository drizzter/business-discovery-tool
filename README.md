# Business Discovery Tool

AI-powered business discovery and recommendation tool for SEEK Business (Australia).

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## What It Does

1. **Scrapes** SEEK Business listings (seekbusiness.com.au) — parses the Apollo/Next.js SSR cache for structured data
2. **Filters** by category, location, and opportunity type
3. **AI Recommends** businesses based on:
   - **Pricing analysis** — is it over/underpriced vs similar listings?
   - **Market saturation** — how many competitors in same category/location?
   - **Investment value** — overall assessment

## Architecture

```
business-discovery-tool/
├── app.py                  # Streamlit UI (main entry point)
├── config.py               # Environment config (API keys)
├── models.py               # Data models (Business, Recommendation)
├── requirements.txt
├── .env                    # API keys (git-ignored)
├── scraper/
│   ├── base.py             # Abstract base scraper
│   ├── seek_scraper.py     # SEEK Business scraper (parses __NEXT_DATA__ Apollo cache)
│   ├── yelp_scraper.py     # Yelp scraper skeleton
│   └── demo_scraper.py     # Sample data for testing
├── engine/
│   └── recommender.py      # AI recommendation engine (OpenAI-compatible API)
└── ui/
    └── (future components)
```

## API Integration

Uses an OpenAI-compatible endpoint (via LiteLLM):
- `OPENAI_BASE_URL` — the model endpoint
- `OPENAI_API_KEY` — API key for authentication

## Adding a New Platform

1. Create `scraper/new_platform.py`
2. Extend `BaseScraper`, implement `_scrape_raw()`
3. Add to `SCRAPERS` dict in `app.py`
