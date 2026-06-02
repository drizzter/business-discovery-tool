"""Data models for business listings."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Business:
    """Represents a scraped business listing."""
    name: str
    url: str
    platform: str
    description: str = ""
    location: str = ""
    category: str = ""
    rating: Optional[float] = None
    review_count: int = 0
    date_posted: Optional[datetime] = None
    price_range: str = ""
    phone: str = ""
    website: str = ""
    raw_data: dict = field(default_factory=dict)

    @property
    def days_old(self) -> int:
        if self.date_posted:
            return (datetime.now() - self.date_posted).days
        return 999

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "platform": self.platform,
            "description": self.description,
            "location": self.location,
            "category": self.category,
            "rating": self.rating,
            "review_count": self.review_count,
            "date_posted": self.date_posted.isoformat() if self.date_posted else None,
            "price_range": self.price_range,
            "phone": self.phone,
            "website": self.website,
        }


@dataclass
class Recommendation:
    """AI-generated recommendation for a business."""
    business: Business
    score: float  # 0-10
    reasoning: str
    highlights: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
