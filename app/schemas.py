"""
TrustShield Pydantic schemas for request and response validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CheckRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=10000, description="The message, job description, or news headline to check.")
    explain_simply: Optional[bool] = Field(default=False, description="Request an optional AI explanation.")


class ExplainRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=10000)
    checker_type: str = Field(..., description="scam, job, or news")
    verdict: str
    risk_score: int
    flags: List[str] = Field(default_factory=list)


class RedFlagItem(BaseModel):
    phrase: str
    category: str
    description: str
    weight: int
    start: int
    end: int


class SafeActionTip(BaseModel):
    title: str
    description: str
    badge: Optional[str] = None
    action_url: Optional[str] = None


class CheckResponse(BaseModel):
    tool: str
    verdict: str
    verdict_type: str  # "danger", "warning", "success"
    risk_score: int    # 0 - 100
    confidence_label: str
    ml_probability: float
    rule_score: int
    flags: List[RedFlagItem]
    highlighted_html: str
    safe_action_tips: List[SafeActionTip]
    explanation: Optional[str] = None
    disclaimer: str = "AI-assisted aid, not a guarantee. Verify with official sources."
    privacy_note: str = "🔒 Privacy First: Your text was analyzed in-memory and never saved, logged, or shared."
