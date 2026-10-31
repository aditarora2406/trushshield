"""
TrustShield - Rule-Based Red-Flag Engine (English & Hinglish)
Identifies high-risk patterns, extracts character spans for UI text highlighting,
and computes category-specific rule risk scores (0-100).
"""

import re
from typing import List, Dict, Any, Tuple

# Common Indian scam & urgency triggers
URGENCY_PATTERNS = [
    (r"\b(act now|urgent action|immediately|action required)\b", "Urgent action demanded", 25),
    (r"\b(last chance|limited time|hurry|offer ends|expires? (today|soon|within))\b", "Artificial scarcity / deadline", 25),
    (r"\b(jaldi karo|turant|abhibhi waqt hai|samay khatam|khatam ho jayega|jaldi kijiye)\b", "Urgency pressure (Hinglish)", 30),
    (r"\b(within\s+\d+\s*(hours?|hrs?|mins?|minutes?)|in\s+24\s*hours?)\b", "Tight countdown timer", 20),
    (r"\b(account (will be|has been) (blocked|suspended|deactivated|closed))\b", "Account suspension threat", 35),
    (r"\b(bijli kat jayegi|electricity will be disconnected|power cut)\b", "Utility disconnection scam", 35),
]

SENSITIVE_REQUEST_PATTERNS = [
    (r"\b(otp|one[-\s]?time[-\s]?password|verification code)\b", "OTP request (NEVER share OTP)", 45),
    (r"\b(pin|atm pin|upi pin|mpin)\b", "PIN / MPIN solicitation", 45),
    (r"\b(cvv|cvv2|card security code|expiry date)\b", "Debit/Credit card secrets", 45),
    (r"\b(aadhaar(\s*card|\s*number)?|pan(\s*card)?|bank\s*account\s*number)\b", "Sensitive identity/KYC document request", 35),
    (r"\b(netbanking password|login credentials|password reset link)\b", "Password / credentials request", 40),
    (r"\b(update (your )?kyc|kyc expired|complete kyc verification)\b", "Fake KYC update trap", 40),
    (r"\b(share screen|download anydesk|install rustdesk|teamviewer|quicksupport)\b", "Remote access tool trap", 50),
]

MONEY_REQUEST_PATTERNS = [
    (r"\b(registration fee|application fee|processing fee|onboarding fee)\b", "Upfront registration/processing fee", 40),
    (r"\b(security deposit|refundable deposit|caution deposit)\b", "Advance deposit demand", 40),
    (r"\b(pay to get job|pay rs\.?|send rs\.?|transfer money|pay (now|first))\b", "Pay money upfront demand", 45),
    (r"\b(upi|gpay|google pay|phonepe|paytm|bhim)\s+(karo|pe bhejo|transfer|payment)\b", "Direct mobile wallet transfer demand", 35),
    (r"\b(paisa bhejo|khate me daalo|deposit karo)\b", "Direct money transfer demand (Hinglish)", 35),
    (r"\b(daily return|double your money|guaranteed profit|invest \d+ get \d+)\b", "Get-rich-quick Ponzi/investment scam", 45),
]

FAKE_PRIZE_PATTERNS = [
    (r"\b(lottery|lucky draw|bumper prize|kbc lottery|kaun banega crorepati)\b", "Fake lottery / Lucky draw lure", 40),
    (r"\b(you have won|congratulations you won|winner of|selected for prize)\b", "Unsolicited prize winner claim", 35),
    (r"\b(\d+\s*(lakh|crore|crores|usd|\$|inr)\s*(prize|cash|cheque|reward))\b", "Exaggerated cash prize lure", 40),
    (r"\b(free gift card|claim your (iphone|reward|voucher|gift))\b", "Unrealistic gift / reward lure", 30),
    (r"\b(inayat kiya gaya hai|inaam mila hai|apka naam nikla hai)\b", "Fake prize claim (Hinglish)", 35),
]

SUSPICIOUS_LINK_PATTERNS = [
    (r"https?://(?:bit\.ly|tinyurl\.com|rb\.gy|is\.gd|t\.co|cutt\.ly|shorturl\.at)/\S+", "Suspicious URL shortener (hides actual destination)", 30),
    (r"https?://(?:t\.me|telegram\.me|wa\.me|chat\.whatsapp\.com)/\S+", "Redirects directly to WhatsApp/Telegram chat", 30),
    (r"https?://[a-zA-Z0-9.-]+\.(?:xyz|top|ru|cn|cc|vip|club|click|tk|ml|ga|work|download)/?\S*", "High-risk domain TLD often used in scams", 35),
    (r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?(?:/\S*)?", "Bare IP address link instead of official domain", 40),
    (r"https?://(?:docs\.google\.com/forms|forms\.gle)/\S+", "Generic free Google Form used for official process", 25),
    (r"https?://(?:apkpure|mediafire|drive\.google\.com)/\S+\.apk", "Untrusted APK download link (malware risk)", 45),
]

# Job & Internship Specific Patterns
JOB_SPECIFIC_PATTERNS = [
    (r"\b(contact (on|via|only) (whatsapp|telegram)|dm on telegram|whatsapp us at)\b", "Informal WhatsApp/Telegram-only recruitment", 35),
    (r"[a-zA-Z0-9._%+-]+@(gmail|yahoo|hotmail|outlook|rediffmail)\.com", "Free personal email used for company hiring (No corporate domain)", 40),
    (r"\b(earn (?:rs\.?|inr|\$)?\s*\d{2,6}\s*(?:daily|per day|per hour|weekly))\b", "Unrealistically high daily/hourly payout", 40),
    (r"\b(work from home earn (?:50k|40k|30k|20k|10k|50000|big money))\b", "Classic work-from-home high-income trap", 40),
    (r"\b(no interview|direct (selection|joining|offer letter)|selected without interview)\b", "No interview / instant selection red flag", 45),
    (r"\b(typing job|data entry job|sms sending job|copy paste job)\b.*?\b(earn|daily|weekly|pay)\b", "High-frequency fake data entry/typing scam", 35),
    (r"\b(pay for (training|laptop|courier|uniform|id card|kit))\b", "Demand to pay for company equipment/training", 50),
    (r"\b(like youtube videos|subscribe channels and earn|review products earn)\b", "Part-time task / telegram rating task scam", 45),
    (r"\b(ghar baithe kamao|rozana kamayein|bina kisi interview ke)\b", "Instant home earning promise (Hinglish)", 40),
]

# News & Information Specific Patterns
NEWS_SPECIFIC_PATTERNS = [
    (r"\b(forward(ed)?\s+(to|as)\s+(everyone|all|groups?|received)|share\s+before\s+it(?:'?s|\s+is)\s+deleted)\b", "Viral forwarding coercion tactic", 35),
    (r"\b(share\s+(with|to)\s+all\s+(your\s+)?(friends|contacts|family|groups?))\b", "Chain-message viral spread prompt", 30),
    (r"\b(media\s+(will\s+not|won'?t)\s+show\s+this|hidden\s+truth|banned\s+by\s+government)\b", "Conspiratorial claim of suppressed truth", 35),
    (r"\b(unesco|nasa|who|pmo|icmr|aiims|supreme\s*court)\b.*?\b(declared|voted|awarded|confirmed|warned|announced|declare\s*kiya|ke\s*anusar|ne\s*kaha)\b", "Authority name-dropping without official citation", 40),
    (r"\b(best\s+anthem(\s+in\s+the\s+world)?|declared.*?best\s+anthem)\b", "Classic national anthem UNESCO hoax", 40),
    (r"\b(miracle\s+cure|100%\s+cure\s+for\s+cancer|guaranteed\s+remedy|doctor\s+secrets)\b", "Unscientific medical / miracle claim", 40),
    (r"\b(breaking\s+news|dhamaka\s+khabar|sabko\s+bhejo|aage\s+bhejo|jaldi\s*(sabko\s*)?(share|forward)\s*karo)\b", "Sensational forward hook (Hinglish)", 35),
    (r"\b(whatsapp\s+will\s+be\s+chargeable|free\s+recharge|muft\s+recharge|free\s+laptop\s+scheme|pm\s+scheme\s+free|free\s+3\s+months\s+recharge)\b", "Classic viral hoax claims", 45),
]


def extract_matched_spans(text: str, patterns: List[Tuple[str, str, int]], category: str) -> List[Dict[str, Any]]:
    """
    Scans text for regular expression patterns, collects exact start/end character offsets,
    matched substrings, severity, and rule descriptions.
    """
    matches = []
    for pattern, description, weight in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            matches.append({
                "start": match.start(),
                "end": match.end(),
                "phrase": match.group(0),
                "category": category,
                "description": description,
                "weight": weight
            })
    return matches


def merge_and_sort_spans(raw_matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sorts matches by start offset and eliminates redundant sub-span overlaps.
    """
    if not raw_matches:
        return []
    
    sorted_matches = sorted(raw_matches, key=lambda m: (m["start"], -(m["end"] - m["start"])))
    merged = []
    
    for current in sorted_matches:
        if not merged:
            merged.append(current)
            continue
        
        last = merged[-1]
        # If current starts before last ends, they overlap
        if current["start"] < last["end"]:
            # If current extends beyond last, keep highest weight description or merge
            if current["end"] > last["end"]:
                # Extend end if weight is significant
                if current["weight"] > last["weight"]:
                    merged[-1] = current
        else:
            merged.append(current)
            
    return merged


def analyze_heuristics(text: str, checker_type: str) -> Tuple[List[Dict[str, Any]], int, Dict[str, Any]]:
    """
    Analyzes text based on checker type ('scam', 'job', 'news').
    Returns:
      - merged_spans: list of matched text spans with offsets & categories
      - rule_score: aggregate risk score (0-100)
      - meta: auxiliary stats (caps ratio, exclamation marks, etc.)
    """
    raw_matches: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {}
    
    # 1. Check universal patterns for all checkers
    raw_matches.extend(extract_matched_spans(text, URGENCY_PATTERNS, "Urgency Pressure"))
    raw_matches.extend(extract_matched_spans(text, SENSITIVE_REQUEST_PATTERNS, "Sensitive Data Request"))
    raw_matches.extend(extract_matched_spans(text, MONEY_REQUEST_PATTERNS, "Financial / Upfront Payment"))
    raw_matches.extend(extract_matched_spans(text, FAKE_PRIZE_PATTERNS, "Prize / Lottery Lure"))
    raw_matches.extend(extract_matched_spans(text, SUSPICIOUS_LINK_PATTERNS, "Suspicious Link / Channel"))
    
    # 2. Checker specific rules
    if checker_type == "job":
        raw_matches.extend(extract_matched_spans(text, JOB_SPECIFIC_PATTERNS, "Job Red Flag"))
    elif checker_type == "news":
        raw_matches.extend(extract_matched_spans(text, NEWS_SPECIFIC_PATTERNS, "Sensational / Hoax Pattern"))
        
        # Punctuation check (excessive !!! or ???)
        exclamation_matches = list(re.finditer(r"[!?]{2,}", text))
        if exclamation_matches:
            meta["excessive_punctuation"] = len(exclamation_matches)
            for m in exclamation_matches:
                raw_matches.append({
                    "start": m.start(),
                    "end": m.end(),
                    "phrase": m.group(0),
                    "category": "Excessive Punctuation",
                    "description": "Exaggerated punctuation indicates sensationalist clickbait",
                    "weight": 15
                })
        
        # ALL CAPS analysis
        words = text.split()
        if len(words) >= 4:
            all_caps_words = [w for w in words if len(w) >= 3 and w.isupper() and w.isalpha()]
            caps_ratio = len(all_caps_words) / len(words)
            meta["caps_ratio"] = round(caps_ratio, 2)
            if caps_ratio > 0.35:
                # Highlight capital words
                for m in re.finditer(r"\b[A-Z]{3,}\b", text):
                    raw_matches.append({
                        "start": m.start(),
                        "end": m.end(),
                        "phrase": m.group(0),
                        "category": "ALL CAPS Panic",
                        "description": "Aggressive capitalization used to induce panic",
                        "weight": 15
                    })

    # Clean & merge spans
    merged_spans = merge_and_sort_spans(raw_matches)
    
    # Calculate weighted rule risk score
    if not merged_spans:
        rule_score = 0
    else:
        # Sum weights with diminishing returns formula
        raw_weight_sum = sum(s["weight"] for s in merged_spans)
        # Cap high severity at 100, smoothly scaling
        rule_score = min(100, int(raw_weight_sum * 0.95))
        # Ensure if critical sensitive items (OTP/PIN/CVV or pay for job) are present, score is at least 75
        critical_categories = ["Sensitive Data Request", "Financial / Upfront Payment"]
        has_critical = any(s["category"] in critical_categories and s["weight"] >= 40 for s in merged_spans)
        if has_critical:
            rule_score = max(rule_score, 78)

    return merged_spans, rule_score, meta
