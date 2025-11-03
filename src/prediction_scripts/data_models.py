from typing import Dict, List, Optional
from pydantic import BaseModel

class CreatorQuery(BaseModel):
    question: str
    # niche: Optional[str] = None

class RecommendationResponse(BaseModel):
    answer: str
    trending_items: List[Dict]
    sources: List[Dict]
    timestamp: str
