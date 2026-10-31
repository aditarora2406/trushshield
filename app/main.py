"""
TrustShield FastAPI Server
Exposes endpoints:
- POST /scam   : Scam Message Checker
- POST /job    : Fake Job & Internship Checker
- POST /news   : Fake News & Misinformation Checker
- POST /explain: Optional 2-3 line Gemma/Gemini explanation
- GET  /health : Health check
- Serves static front-end assets (HTML, CSS, JS)
"""

import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Load environment variables (.env)
load_dotenv()

from app.schemas import CheckRequest, CheckResponse, ExplainRequest
from app.ml import analyze_text
from app.explainer import generate_explanation

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="TrustShield API",
    description="Student-focused ML & Rule-Based Shield against Scams, Fake Jobs, and Misinformation",
    version="1.0.0"
)

# Enable CORS for cross-origin or local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_input_text(raw_text: str) -> str:
    """Validates and trims user input, ensuring it is non-empty and reasonable."""
    if not raw_text or not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Input text cannot be empty. Please paste a message, job posting, or news headline."
        )
    trimmed = raw_text.strip()
    if len(trimmed) < 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Input text is too short to analyze. Please enter at least 4 characters."
        )
    if len(trimmed) > 10000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Input text exceeds maximum length of 10,000 characters."
        )
    return trimmed


@app.post("/scam", response_model=CheckResponse, summary="Analyze SMS/WhatsApp/Email for scams")
def check_scam(request: CheckRequest):
    text = validate_input_text(request.text)
    response = analyze_text(text, "scam")
    if request.explain_simply:
        flag_names = [f.phrase for f in response.flags]
        response.explanation = generate_explanation(
            text, "scam", response.verdict, response.risk_score, flag_names
        )
    return response


@app.post("/job", response_model=CheckResponse, summary="Analyze job/internship postings")
def check_job(request: CheckRequest):
    text = validate_input_text(request.text)
    response = analyze_text(text, "job")
    if request.explain_simply:
        flag_names = [f.phrase for f in response.flags]
        response.explanation = generate_explanation(
            text, "job", response.verdict, response.risk_score, flag_names
        )
    return response


@app.post("/news", response_model=CheckResponse, summary="Analyze headlines and viral forwards")
def check_news(request: CheckRequest):
    text = validate_input_text(request.text)
    response = analyze_text(text, "news")
    if request.explain_simply:
        flag_names = [f.phrase for f in response.flags]
        response.explanation = generate_explanation(
            text, "news", response.verdict, response.risk_score, flag_names
        )
    return response


@app.post("/explain", summary="Generate a 2-3 line simple explanation via Gemma API or fallback")
def explain_result(req: ExplainRequest):
    text = validate_input_text(req.text)
    explanation = generate_explanation(
        text, req.checker_type, req.verdict, req.risk_score, req.flags
    )
    return {
        "explanation": explanation,
        "disclaimer": "AI-assisted explanation. Verify with official sources."
    }


@app.get("/health", summary="Service health check")
def health_check():
    return {
        "status": "healthy",
        "service": "TrustShield",
        "version": "1.0.0"
    }


# Serve static web frontend
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def serve_index():
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "TrustShield API is active. Web UI index.html not found."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
