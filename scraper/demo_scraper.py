"""Demo scraper — generates sample data for testing the UI and AI engine.
Replace with a real scraper once the target platform is known.
"""
import random
from datetime import datetime, timedelta

from models import Business
from scraper.base import BaseScraper

SAMPLE_NAMES = [
    "Sydney Solar Solutions",
    "Blue Gum Landscaping",
    "Coastal Electrical Group",
    "Harbour City Plumbing",
    "Outback IT Services",
    "Gold Coast Digital",
    "Southern Cross Accounting",
    "Brisbane Property Advisors",
    "Aussie Clean Team",
    "Urban Edge Marketing",
    "Tasman Legal Partners",
    "Pacific Trade Services",
    "Canberra Business Consulting",
    "Melbourne Fitness Hub",
    "Perth Security Solutions",
    "Hunter Valley Property Group",
    "Sunshine Coast Electrical",
    "Northern Beaches Landscaping",
    "Adelaide Home Services",
    "Elite Aussie Contractors",
]

SAMPLE_CATEGORIES = [
    "Food & Drink",
    "Retail",
    "Health, Beauty & Fitness",
    "Cleaning & Maintenance",
    "Accommodation, Tourism & Leisure",
    "Commercial Services",
    "Education, Coaching & Training",
    "Automotive & Marine",
    "Manufacturing, Wholesale & Distribution",
    "Home & Garden",
    "Technology & Internet",
    "Transport & Logistics",
]

SAMPLE_LOCATIONS = [
    "Sydney, NSW",
    "Melbourne, VIC",
    "Brisbane, QLD",
    "Perth, WA",
    "Adelaide, SA",
    "Gold Coast, QLD",
    "Canberra, ACT",
    "Newcastle, NSW",
    "Wollongong, NSW",
    "Hobart, TAS",
]

SAMPLE_DESCRIPTIONS = [
    "Full-service {cat} provider specializing in residential and commercial clients.",
    "Award-winning {cat} company with 10+ years of experience.",
    "Budget-friendly {cat} solutions for small businesses.",
    "Premium {cat} services with 24/7 support and satisfaction guarantee.",
    "Innovative {cat} startup disrupting the local market.",
]


class DemoScraper(BaseScraper):
    platform_name = "Demo (Sample Data)"

    def _scrape_raw(self, location: str, category: str, max_results: int) -> list[Business]:
        businesses = []
        for i, name in enumerate(SAMPLE_NAMES[:max_results]):
            cat = category if category else random.choice(SAMPLE_CATEGORIES)
            loc = location if location else random.choice(SAMPLE_LOCATIONS)
            desc_tmpl = random.choice(SAMPLE_DESCRIPTIONS)

            biz = Business(
                name=name,
                url=f"https://example.com/biz/{i}",
                platform=self.platform_name,
                description=desc_tmpl.format(cat=cat.lower()),
                location=loc,
                category=cat,
                rating=round(random.uniform(3.0, 5.0), 1),
                review_count=random.randint(5, 500),
                date_posted=datetime.now() - timedelta(days=random.randint(0, 6)),
                price_range=random.choice(["$", "$$", "$$$", "$$$$"]),
                phone=f"04{random.randint(10,99)} {random.randint(100,999)} {random.randint(100,999)}"
            )
            businesses.append(biz)

        # Apply filters if given
        if location:
            businesses = [b for b in businesses if location.lower() in b.location.lower()]
        if category:
            businesses = [b for b in businesses if category.lower() in b.category.lower()]

        return businesses
