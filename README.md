# Business Discovery Tool

AI-powered business discovery and recommendation tool for SEEK Business (Australia).

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/drizzter/business-discovery-tool.git
cd business-discovery-tool

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file with your API key
echo 'OPENAI_BASE_URL=https://three-mistress-opera-locations.trycloudflare.com/v1' > .env
echo 'OPENAI_API_KEY=your-api-key-here' >> .env

# 4. Run the app
streamlit run app.py
```

The browser opens automatically at `http://localhost:8501`.

## What It Does

1. **Scrapes** SEEK Business listings (seekbusiness.com.au) — parses the Apollo/Next.js SSR cache for structured data
2. **Filters** by category, location, opportunity type, and price range
3. **AI Recommends** businesses based on:
   - Pricing analysis — is it over/underpriced vs similar listings?
   - Market saturation — how many competitors in same category/location?
   - Investment value — structured scorecards with opportunity score, risk level, and next steps

## Features

- **SEEK Business scraper** — real-time listings from 14 Australian cities
- **AI recommendation engine** — structured scorecards (opportunity score, price/location/market scores, risk level)
- **Guided criteria** — budget, location, industry, involvement, risk tolerance, ROI
- **7 analysis modes** — Best Overall, Lowest Risk, Highest Growth, Under Budget, Owner-Operator, Passive, Undervalued
- **Export** — CSV, Excel, and AI report downloads
- **Demo mode** — sample data for testing without API calls

## Architecture

```
business-discovery-tool/
├── app.py                  # Streamlit UI (main entry point)
├── config.py               # Environment config (API keys)
├── models.py               # Data models (Business, Recommendation)
├── requirements.txt        # Python dependencies
├── .env                    # API keys (git-ignored)
├── scraper/
│   ├── base.py             # Abstract base scraper
│   ├── seek_scraper.py     # SEEK Business scraper (parses __NEXT_DATA__ Apollo cache)
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
- Model: `smart` (auto-routed)

## Adding a New Platform

1. Create `scraper/new_platform.py`
2. Extend `BaseScraper`, implement `_scrape_raw()`
3. Add to `SCRAPERS` dict in `app.py`

## Requirements

- Python 3.10+
- Internet connection (for SEEK Business scraping)
- API key for AI recommendations (optional — demo mode works without it)
