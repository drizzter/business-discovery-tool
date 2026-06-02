"""SEEK Business scraper — extracts listings from seekbusiness.com.au Apollo cache."""
import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from models import Business
from scraper.base import BaseScraper

# Major Australian cities/regions for bulk scraping
MAJOR_CITIES = [
    "Sydney",
    "Melbourne",
    "Brisbane",
    "Perth",
    "Adelaide",
    "Gold Coast",
    "Canberra",
    "Newcastle",
    "Hobart",
    "Darwin",
    "Geelong",
    "Townsville",
    "Cairns",
    "Wollongong",
]


class SeekBusinessScraper(BaseScraper):
    platform_name = "SEEK Business"

    BASE_URL = "https://www.seekbusiness.com.au/businesses-for-sale"

    def _scrape_raw(self, location: str, category: str, max_results: int) -> list[Business]:
        """Scrape SEEK Business by parsing the __NEXT_DATA__ Apollo cache."""
        businesses = []
        seen_ids = set()

        # Determine list of cities to scrape
        if location.lower() == "all":
            cities = MAJOR_CITIES
        elif location.strip():
            cities = [location]
        else:
            cities = [""]  # No location filter — all Australia

        for city in cities:
            url = self.BASE_URL
            if city:
                slug = city.lower().replace(" ", "-").replace(",", "")
                url = f"{url}/in-{slug}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-AU,en;q=0.9",
            }

            # Scrape multiple pages per city
            pages_to_scrape = max(1, (max_results // len(cities)) // 20 + 1)
            for page_num in range(1, pages_to_scrape + 1):
                page_url = url if page_num == 1 else f"{url}?page={page_num}"
                try:
                    resp = requests.get(page_url, headers=headers, timeout=20)
                    resp.raise_for_status()
                    page_businesses = self._parse_page(resp.text, category)

                    for biz in page_businesses:
                        biz_id = biz.raw_data.get("id")
                        if biz_id and biz_id not in seen_ids:
                            seen_ids.add(biz_id)
                            businesses.append(biz)

                    if len(businesses) >= max_results:
                        break
                except Exception as e:
                    print(f"Error scraping {city} page {page_num}: {e}")
                    break

            if len(businesses) >= max_results:
                break

        return businesses[:max_results]

    def _parse_page(self, html: str, category_filter: str = "") -> list[Business]:
        """Parse listings from the __NEXT_DATA__ Apollo cache."""
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")

        if not script:
            return []

        data = json.loads(script.string)
        apollo = data.get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {})

        listings = {
            k: v for k, v in apollo.items()
            if k.startswith("SearchListing:") and isinstance(v, dict) and "title" in v
        }

        businesses = []
        for key, listing in listings.items():
            biz = self._parse_listing(listing, apollo)

            # Apply category filter
            if category_filter and category_filter.lower() not in biz.category.lower():
                continue

            businesses.append(biz)

        return businesses

    def _parse_listing(self, listing: dict, apollo: dict) -> Business:
        """Convert an Apollo SearchListing dict into a Business object."""
        # Resolve district → location
        district = self._resolve_ref(listing.get("district"), apollo)
        state = self._resolve_ref(district.get("state", {}), apollo) if isinstance(district, dict) else {}
        location = f"{district.get('displayTitle', '')}, {state.get('title', '')}" if district else ""

        # Resolve industry
        industry = self._resolve_ref(listing.get("industry"), apollo)
        industry_group = self._resolve_ref(listing.get("industryGroup"), apollo)
        category = ""
        if isinstance(industry_group, dict):
            category = industry_group.get("title", "")
        if isinstance(industry, dict) and industry.get("title"):
            category = f"{category} > {industry['title']}" if category else industry["title"]

        # Parse price
        invest = listing.get("investment", {})
        price_range_data = invest.get("range", {}) if isinstance(invest, dict) else {}
        price_min = price_range_data.get("min", 0)
        price_max = price_range_data.get("max", 0)
        is_poa = invest.get("isPoa", False) if isinstance(invest, dict) else False

        if is_poa:
            price_str = "Price on Application"
        elif price_min == price_max:
            price_str = f"${price_min:,.0f}" if price_min else ""
        else:
            price_str = f"${price_min:,.0f} - ${price_max:,.0f}" if price_min else ""

        # Parse date
        refresh_str = listing.get("refreshDate", "")
        date_posted = None
        if refresh_str:
            try:
                date_posted = datetime.fromisoformat(refresh_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, TypeError):
                pass

        # Build URL (SEEK requires listing ID in the path)
        url_key = listing.get("urlKey", "")
        listing_id = listing.get("id", "")
        url = f"https://www.seekbusiness.com.au/business-listing/{url_key}/{listing_id}" if url_key else ""

        return Business(
            name=listing.get("title", "").strip(),
            url=url,
            platform=self.platform_name,
            description=listing.get("summary", ""),
            location=location.strip().strip(","),
            category=category,
            rating=None,  # SEEK doesn't have ratings
            review_count=0,
            date_posted=date_posted,
            price_range=price_str,
            phone="",
            website="",
            raw_data={
                "id": listing.get("id"),
                "opportunity_type": listing.get("opportunityType", ""),
                "price_min": price_min,
                "price_max": price_max,
                "is_poa": is_poa,
                "district_id": district.get("id") if isinstance(district, dict) else None,
                "industry_id": industry.get("id") if isinstance(industry, dict) else None,
            },
        )

    @staticmethod
    def _resolve_ref(obj, cache: dict):
        """Resolve an Apollo __ref to its cached object."""
        if isinstance(obj, dict) and "__ref" in obj:
            return cache.get(obj["__ref"], {})
        if isinstance(obj, dict):
            return obj
        return {}
