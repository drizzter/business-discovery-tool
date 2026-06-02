"""Abstract base scraper — implement this for each platform."""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from models import Business


class BaseScraper(ABC):
    """Base class for platform scrapers."""

    platform_name: str = "unknown"

    def scrape(self, days_back: int = 7, location: str = "", category: str = "", max_results: int = 100) -> list[Business]:
        """
        Scrape listings from the last N days.
        Subclasses implement _scrape_raw(); this handles date filtering.
        """
        cutoff = datetime.now() - timedelta(days=days_back)
        raw_listings = self._scrape_raw(location=location, category=category, max_results=max_results)

        # Filter to last N days
        filtered = []
        for biz in raw_listings:
            if biz.date_posted and biz.date_posted >= cutoff:
                filtered.append(biz)
            elif biz.date_posted is None:
                filtered.append(biz)  # Include if date unknown
        return filtered

    @abstractmethod
    def _scrape_raw(self, location: str, category: str, max_results: int) -> list[Business]:
        """Platform-specific scraping logic. Must be implemented."""
        ...
