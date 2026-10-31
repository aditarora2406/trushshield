"""
TrustShield ML Inference & Hybrid Scoring Engine
Combines scikit-learn Logistic Regression probability with rule-based heuristics.
Generates highlighted HTML markup, verdicts, and actionable student safety advice.
"""

import os
import html
import joblib
from typing import Dict, Any, List, Tuple
from app.rules import analyze_heuristics
from app.schemas import RedFlagItem, SafeActionTip, CheckResponse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Cache loaded models in memory
LOADED_MODELS: Dict[str, Any] = {}


def get_model(checker_type: str):
    """Loads and caches the TF-IDF + Logistic Regression pipeline."""
    if checker_type in LOADED_MODELS:
        return LOADED_MODELS[checker_type]
    
    filename_map = {
        "scam": "scam_model.joblib",
        "job": "job_model.joblib",
        "news": "news_model.joblib"
    }
    filepath = os.path.join(MODELS_DIR, filename_map.get(checker_type, "scam_model.joblib"))
    
    if os.path.exists(filepath):
        try:
            model = joblib.load(filepath)
            LOADED_MODELS[checker_type] = model
            return model
        except Exception as e:
            print(f"Error loading model {filepath}: {e}")
            return None
    return None


def predict_ml_probability(text: str, checker_type: str) -> float:
    """
    Computes ML probability of being Scam / Fake (0.0 to 1.0).
    Falls back gracefully if model is not loaded.
    """
    model = get_model(checker_type)
    if model is not None:
        try:
            # predict_proba returns [prob_class_0, prob_class_1]
            probs = model.predict_proba([text])[0]
            # Assuming class 1 is Scam / Fake
            return float(probs[1])
        except Exception as e:
            print(f"Prediction error: {e}")
    
    # Safe fallback if model is missing: neutral probability
    return 0.5


def build_highlighted_html(text: str, spans: List[Dict[str, Any]]) -> str:
    """
    Safely escapes raw user text and inserts styled <mark> tags around identified spans.
    """
    if not spans:
        return html.escape(text)

    # Sort spans in ascending order of start offset
    sorted_spans = sorted(spans, key=lambda s: s["start"])
    result_parts = []
    last_idx = 0

    for span in sorted_spans:
        start = max(0, span["start"])
        end = min(len(text), span["end"])
        if start < last_idx:
            # Skip if overlapping somehow
            continue

        # Text before mark
        result_parts.append(html.escape(text[last_idx:start]))

        # Highlighted span
        category = html.escape(span.get("category", "Flag"))
        desc = html.escape(span.get("description", ""))
        marked_text = html.escape(text[start:end])
        
        # Color styling depending on category
        mark_html = (
            f'<mark class="trust-mark" title="{category}: {desc}" '
            f'data-category="{category}" tabindex="0">'
            f'{marked_text}'
            f'<span class="trust-mark-tooltip">{category}</span>'
            f'</mark>'
        )
        result_parts.append(mark_html)
        last_idx = end

    # Remaining text
    result_parts.append(html.escape(text[last_idx:]))
    return "".join(result_parts)


def compute_verdict_and_tips(checker_type: str, risk_score: int) -> Tuple[str, str, str, List[SafeActionTip]]:
    """
    Maps risk score to verdict string, visual category ('danger', 'warning', 'success'),
    confidence label, and student safe-action tips.
    """
    if checker_type == "scam":
        if risk_score >= 65:
            verdict = "Likely Scam"
            vtype = "danger"
            conf = "High Risk Detected"
            tips = [
                SafeActionTip(
                    title="Do NOT Share Sensitive Info",
                    description="Never share OTP, ATM PIN, UPI MPIN, or click links in this message. Banks and officials never ask for them.",
                    badge="Crucial"
                ),
                SafeActionTip(
                    title="Report on National Cybercrime Portal",
                    description="Report this number and message on cybercrime.gov.in or immediately call the toll-free helpline 1930.",
                    badge="Helpline: 1930",
                    action_url="https://cybercrime.gov.in"
                ),
                SafeActionTip(
                    title="Block & Report on Sanchar Saathi",
                    description="Report suspected fraudulent communications on the Indian Government's Chakshu portal (sancharsaathi.gov.in).",
                    badge="Government Portal",
                    action_url="https://sancharsaathi.gov.in"
                )
            ]
        elif risk_score >= 30:
            verdict = "Suspicious"
            vtype = "warning"
            conf = "Caution Recommended"
            tips = [
                SafeActionTip(
                    title="Cross-Verify Directly",
                    description="Do not call numbers or click links in the message. Check your official bank app or website independently.",
                    badge="Verification"
                ),
                SafeActionTip(
                    title="Pause Before Acting",
                    description="Scammers rely on fake urgency (e.g., 'account blocked in 2 hours'). Take 5 minutes to verify calmly.",
                    badge="Safety Tip"
                ),
                SafeActionTip(
                    title="Ask Someone You Trust",
                    description="Show this message to a parent, teacher, or college tech-support before clicking anything.",
                    badge="Second Opinion"
                )
            ]
        else:
            verdict = "Likely Safe"
            vtype = "success"
            conf = "No Red Flags Found"
            tips = [
                SafeActionTip(
                    title="Maintain Healthy Vigilance",
                    description="While this message looks harmless, remember to never share your password, OTP, or CVV with anyone.",
                    badge="General Best Practice"
                ),
                SafeActionTip(
                    title="Official Communication Only",
                    description="Ensure sensitive communications come from verified business accounts or official sender headers (e.g., VM-SBIINB).",
                    badge="Info"
                )
            ]

    elif checker_type == "job":
        if risk_score >= 65:
            verdict = "Likely Fake / Scam Job"
            vtype = "danger"
            conf = "High Fraud Risk"
            tips = [
                SafeActionTip(
                    title="Never Pay for a Job or Internship",
                    description="No genuine company ever asks for registration fees, training fees, or laptop security deposits.",
                    badge="Rule #1 for Students"
                ),
                SafeActionTip(
                    title="Check Corporate Domain & Recruiter",
                    description="Official recruiters correspond via company domains (e.g., @tcs.com, @infosys.com), never free @gmail.com accounts.",
                    badge="Recruiter Check"
                ),
                SafeActionTip(
                    title="Report Fake Recruiter",
                    description="Report the account on Telegram/WhatsApp and alert your college training and placement cell (TPO).",
                    badge="Alert TPO"
                )
            ]
        elif risk_score >= 30:
            verdict = "Suspicious Posting"
            vtype = "warning"
            conf = "Verify Before Applying"
            tips = [
                SafeActionTip(
                    title="Look Up on Official Career Page",
                    description="Search for the exact Job ID or title directly on the company's official careers portal, not third-party links.",
                    badge="Verify Role"
                ),
                SafeActionTip(
                    title="Inspect LinkedIn Profiles",
                    description="Search the recruiter's name and company on LinkedIn. Check their employee network and tenure.",
                    badge="LinkedIn Check",
                    action_url="https://www.linkedin.com"
                ),
                SafeActionTip(
                    title="Avoid Telegram-Only Interviews",
                    description="Reputable firms conduct video/voice interviews over Zoom, Teams, or Google Meet, never text-only Telegram chats.",
                    badge="Interview Check"
                )
            ]
        else:
            verdict = "Likely Legitimate Job"
            vtype = "success"
            conf = "Standard Job Format"
            tips = [
                SafeActionTip(
                    title="Apply on Official Portal",
                    description="Even with legitimate postings, prefer submitting your resume directly on the company's verified careers portal.",
                    badge="Tip"
                ),
                SafeActionTip(
                    title="Prepare for Formal Rounds",
                    description="Legitimate internships evaluate core skills through technical interviews, coding rounds, or portfolios.",
                    badge="Preparation"
                )
            ]

    else:  # news
        if risk_score >= 65:
            verdict = "Likely Fake News / Hoax"
            vtype = "danger"
            conf = "High Misinformation Risk"
            tips = [
                SafeActionTip(
                    title="Do NOT Forward to Groups",
                    description="Break the viral chain. Misinformation spreads rapidly when forwarded without verification.",
                    badge="Stop Viral Chain"
                ),
                SafeActionTip(
                    title="Verify on PIB Fact Check",
                    description="Check the official Government of India fact-checker on pib.gov.in/factcheck or WhatsApp +91 8799711259.",
                    badge="PIB Fact Check",
                    action_url="https://factcheck.pib.gov.in"
                ),
                SafeActionTip(
                    title="Reverse Search the Headline",
                    description="Paste key phrases into Google News. If credible mainstream newspapers have not covered it, it is likely false.",
                    badge="Google News Check",
                    action_url="https://news.google.com"
                )
            ]
        elif risk_score >= 30:
            verdict = "Unverified / Sensational"
            vtype = "warning"
            conf = "Needs Independent Verification"
            tips = [
                SafeActionTip(
                    title="Check the Original Source & Date",
                    description="Look for a direct hyperlink to the original press release, journal paper, or government gazette notification.",
                    badge="Source Check"
                ),
                SafeActionTip(
                    title="Beware Clickbait & Exaggeration",
                    description="Sensational headlines often twist half-truths out of context to generate rage or fear.",
                    badge="Critical Thinking"
                ),
                SafeActionTip(
                    title="Consult Reputable Fact Checkers",
                    description="Check trusted Indian independent fact-checking platforms such as Alt News, Boom Live, or Quint WebQoof.",
                    badge="Fact Checkers"
                )
            ]
        else:
            verdict = "Likely Credible News"
            vtype = "success"
            conf = "Standard News Structure"
            tips = [
                SafeActionTip(
                    title="Cross-Reference with Multiple Outlets",
                    description="Always good practice to read coverage across multiple independent news portals for a balanced viewpoint.",
                    badge="Media Literacy"
                ),
                SafeActionTip(
                    title="Verify Date & Context",
                    description="Old news is often recycled as recent breaking news. Confirm the publication date matches today's event.",
                    badge="Timestamp Check"
                )
            ]

    return verdict, vtype, conf, tips


def analyze_text(text: str, checker_type: str) -> CheckResponse:
    """
    Main pipeline:
    1. Heuristic regex and red-flag extraction (English + Hinglish).
    2. ML probability estimation using TF-IDF + Logistic Regression.
    3. Hybrid weighted fusion:
       - Rules decide if ML is unsure.
       - Critical red flags automatically elevate risk score.
    4. Highlighted HTML markup generation.
    5. Verdict, safety tips, and disclaimer creation.
    """
    # 1. Rule-based analysis
    spans, rule_score, meta = analyze_heuristics(text, checker_type)
    
    # 2. ML Probability
    ml_prob = predict_ml_probability(text, checker_type)
    ml_score = int(ml_prob * 100)
    
    # 3. Hybrid Score Fusion
    # ML uncertainty check: near decision boundary (0.35 - 0.65)
    is_ml_unsure = 0.35 <= ml_prob <= 0.65
    
    if is_ml_unsure or len(spans) >= 2:
        # Rules take priority when ML is unsure or multiple clear red flags are detected
        risk_score = int(0.30 * ml_score + 0.70 * rule_score)
    else:
        # Balanced weighting
        risk_score = int(0.55 * ml_score + 0.45 * rule_score)
        
    # Enforce minimum score if strong red flags exist
    if rule_score >= 70:
        risk_score = max(risk_score, rule_score)
    elif rule_score == 0 and ml_score < 35:
        risk_score = min(risk_score, 20)
        
    risk_score = max(0, min(100, risk_score))
    
    # 4. Generate highlighted HTML
    highlighted_html = build_highlighted_html(text, spans)
    
    # 5. Build red flag items
    flags = [
        RedFlagItem(
            phrase=s["phrase"],
            category=s["category"],
            description=s["description"],
            weight=s["weight"],
            start=s["start"],
            end=s["end"]
        )
        for s in spans
    ]
    
    # 6. Verdict and tips
    verdict, verdict_type, conf_label, tips = compute_verdict_and_tips(checker_type, risk_score)
    
    return CheckResponse(
        tool=checker_type,
        verdict=verdict,
        verdict_type=verdict_type,
        risk_score=risk_score,
        confidence_label=conf_label,
        ml_probability=round(ml_prob, 3),
        rule_score=rule_score,
        flags=flags,
        highlighted_html=highlighted_html,
        safe_action_tips=tips,
        explanation=None,  # Will be populated if explain_simply is True or via /explain endpoint
        disclaimer="AI-assisted aid, not a guarantee. Verify with official sources.",
        privacy_note="🔒 Privacy First: Your text was analyzed in-memory and never saved, logged, or shared."
    )
