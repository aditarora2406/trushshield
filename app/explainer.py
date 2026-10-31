"""
TrustShield Explainer Service.
Communicates with Google AI Studio (Gemma / Gemini) to produce 2-3 line explanations
in student-friendly English or conversational Hinglish.
CRITICAL RULE: Gemma only explains the already-computed verdict and flags; it NEVER decides or overrides the verdict.
Includes automatic graceful heuristic fallback when the API key is not configured or network is offline.
"""

import os
import requests
from typing import List, Optional

AI_STUDIO_MODELS = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemma-2-9b-it",
    "gemini-2.0-flash"
]


def get_api_key() -> Optional[str]:
    """Retrieve Google AI Studio key from standard environment variable names."""
    return (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMMA_API_KEY")
        or os.getenv("GOOGLE_AI_STUDIO_KEY")
    )


def generate_explanation(
    text: str,
    checker_type: str,
    verdict: str,
    risk_score: int,
    detected_flags: List[str]
) -> str:
    """
    Produces a 2-3 line student-friendly explanation.
    Tries Google AI Studio API first; if unavailable, uses rule-based heuristic generation.
    """
    api_key = get_api_key()
    
    # 1. If API key is present, attempt call to Google AI Studio
    if api_key:
        try:
            explanation = call_gemma_api(api_key, text, checker_type, verdict, risk_score, detected_flags)
            if explanation and len(explanation.strip()) > 10:
                return explanation.strip()
        except Exception:
            # Fall back to heuristic seamlessly without error
            pass

    # 2. Heuristic fallback (fast, offline, demo-proof)
    return generate_fallback_explanation(checker_type, verdict, risk_score, detected_flags)


def call_gemma_api(
    api_key: str,
    text: str,
    checker_type: str,
    verdict: str,
    risk_score: int,
    detected_flags: List[str]
) -> Optional[str]:
    """
    Sends request to Google AI Studio with candidate models (Gemini / Gemma).
    """
    flags_summary = ", ".join(detected_flags) if detected_flags else "none detected"
    
    system_prompt = (
        "You are TrustShield's Student Safety Explainer for Indian college students. "
        "The system has ALREADY determined the verdict and risk score below. "
        "YOUR SOLE PURPOSE IS TO EXPLAIN IN EXACTLY 2 TO 3 SHORT, FRIENDLY SENTENCES "
        "(in simple English or light Hinglish) why this text received this verdict based on the flags. "
        "NEVER alter, recalculate, or contradict the verdict. "
        "Do not use bullet points or academic jargon. Keep it direct and practical for a 19-year-old student."
    )
    
    user_prompt = (
        f"Tool Type: {checker_type.upper()}\n"
        f"Verdict: {verdict} (Risk Score: {risk_score}/100)\n"
        f"Detected Red Flags: {flags_summary}\n"
        f"Original User Input Snippet:\n\"\"\"{text[:400]}\"\"\"\n\n"
        "Explain simply in 2-3 sentences why this is flagged and what students should watch out for:"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": system_prompt + "\n\n" + user_prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 150
        }
    }
    headers = {"Content-Type": "application/json"}

    for model_name in AI_STUDIO_MODELS:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            response = requests.post(url, json=payload, headers=headers, timeout=6)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text_val = parts[0].get("text", "").strip()
                        if text_val:
                            return text_val
        except Exception:
            continue

    return None


def generate_fallback_explanation(
    checker_type: str,
    verdict: str,
    risk_score: int,
    detected_flags: List[str]
) -> str:
    """
    High-fidelity offline explanation engine.
    Ensures students always get clear, contextual reasoning even with no API key or internet.
    """
    flags_str = ", ".join(detected_flags[:3]) if detected_flags else "unusual formatting"
    
    if checker_type == "scam":
        if risk_score >= 65:
            return (
                f"This message exhibits classic scam traits like {flags_str}. "
                "Legitimate banks, government bodies, and courier services will never ask you to transfer money, "
                "share OTPs, or click unverified links under threat of blocking your account. Turant ignore karein aur block karein."
            )
        elif risk_score >= 35:
            return (
                f"Some patterns in this message ({flags_str}) look suspicious. "
                "Scammers often create artificial urgency or use shortened links to deceive students. "
                "Always verify directly by logging into the official portal or calling customer care before taking any action."
            )
        else:
            return (
                "No overt scam patterns or sensitive requests were found in this text. "
                "However, always stay cautious and never share confidential banking credentials, passwords, or personal ID proofs."
            )

    elif checker_type == "job":
        if risk_score >= 65:
            return (
                f"This post triggers severe employment red flags including {flags_str}. "
                "Reputable organizations never hire solely through Telegram or WhatsApp, nor do they ever charge registration, "
                "training, or laptop security fees. Kisi bhi internship ya job ke liye kabhi pehle paise na dein!"
            )
        elif risk_score >= 35:
            return (
                f"This job post raises doubts due to factors such as {flags_str}. "
                "Watch out for vague job descriptions, lack of formal interview rounds, or personal email addresses (like Gmail). "
                "Always verify the company on LinkedIn and their official career website before responding."
            )
        else:
            return (
                "This posting appears normal without standard fake-job red flags. "
                "To remain safe, ensure communication stays on official company domains and verify the recruiter on LinkedIn."
            )

    else:  # news
        if risk_score >= 65:
            return (
                f"This item exhibits strong indicators of viral misinformation ({flags_str}). "
                "Fabricated news often uses emotional panic, fake authority claims (like NASA or WHO), and calls to 'forward to everyone'. "
                "Aisi khabron ko aage forward na karein and verify on official fact-checking channels like PIB Fact Check."
            )
        elif risk_score >= 35:
            return (
                f"This claim lacks verified citations and contains sensational elements like {flags_str}. "
                "Misinformation frequently twists real events or fabricates quotes to grab quick attention. "
                "Look for coverage from established news publications before believing or sharing."
            )
        else:
            return (
                "The text does not show typical sensationalism or viral hoax patterns. "
                "Always confirm breaking news from primary, reputable news sources and official government portals."
            )
