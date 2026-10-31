# 🛡️ TrustShield — Student Online Safety Guard

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Google AI Studio](https://img.shields.io/badge/GenAI-Gemma%20%2F%20Gemini-4285F4?logo=google&logoColor=white)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

> **Hackathon Theme:** Helping students tell right from wrong online.  
> **Target Audience:** Indian college students frequently targeted by WhatsApp banking scams, fake internship offers, and viral misinformation forwards.

---

## 🌟 Overview & Key Capabilities

**TrustShield** is a fast, reliable, demo-ready web application providing **three essential verification tools in a single modern interface**:

1. **📩 Scam Message Checker:** Detects phishing SMS, WhatsApp threats, electricity disconnection frauds, and fake lottery lures (English & Hinglish).
2. **💼 Fake Job & Internship Checker:** Analyzes LinkedIn, Telegram, and WhatsApp job postings for fraudulent traits like upfront registration/laptop fees, free Gmail recruiter emails, and instant selection without interviews.
3. **📰 Fake News & Forward Checker:** Evaluates forwarded WhatsApp messages and viral headlines for emotional manipulation, ALL-CAPS panic, fake authority claims (UNESCO/NASA/WHO), and missing source citations.

---

## 🚀 Live Demo Highlights

- **Hybrid AI Engine:** Combines **scikit-learn TF-IDF + Logistic Regression** probabilities with a comprehensive **rule-based red-flag engine** tailored for English and Hinglish phrases.
- **In-Text Threat Highlighting:** Highlights exact red-flagged snippets (e.g., `"jaldi karo"`, `"registration fee"`, `"pay tm"`, `"bit.ly"`, `"OTP"`) directly inside the user's message with interactive tooltip breakdowns.
- **Explain Simply (Google AI Studio Gemma Integration):** Generates a concise, 2-to-3 sentence explanation in friendly English or Hinglish explaining why flags are dangerous to students. *Gemma only explains; TrustShield's deterministic engine computes the verdict.*
- **Zero-Storage Privacy First:** User messages and job posts are processed entirely in-memory and are **never stored, logged, or shared**.
- **"What Should I Do?" Action Guides:** Direct emergency guidance tailored for Indian students, including the **National Cybercrime Helpline (1930)**, `cybercrime.gov.in`, the Department of Telecommunications' **Chakshu portal**, and official **PIB Fact Check**.

---

## 🏗️ Architecture & Hybrid Scoring Logic

```
                    ┌────────────────────────────┐
                    │      User Input Text       │
                    │    (English / Hinglish)    │
                    └─────────────┬──────────────┘
                                  │
          ┌───────────────────────┴───────────────────────┐
          ▼                                               ▼
┌──────────────────────────────┐         ┌──────────────────────────────┐
│  TF-IDF + Logistic Regression│         │    Rule-Based Threat Engine  │
│      (scikit-learn)          │         │      (English & Hinglish)    │
│  Outputs ML Probability (0-1)│         │   Regex Spans + Threat Score │
└──────────────┬───────────────┘         └──────────────┬───────────────┘
               │                                        │
               └──────────────────┬─────────────────────┘
                                  ▼
                   ┌─────────────────────────────┐
                   │    Hybrid Score Fusion      │
                   │ • If ML unsure, rules decide│
                   │ • Critical flags elevate    │
                   └──────────────┬──────────────┘
                                  ▼
             ┌─────────────────────────────────────────┐
             │  Risk Score (0-100) & Verdict Mapping   │
             │  🟢 Safe  |  🟡 Suspicious  |  🔴 Scam  │
             └────────────────────┬────────────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│ Interactive Highlights & Badges │       │  Optional "Explain Simply"      │
│ In-text <mark> + 1930 Safe Tips │       │  Gemma API / Offline Fallback   │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

### Hybrid Score Decision Matrix
- **Decision boundary uncertainty:** If the ML probability is between `0.35` and `0.65`, the rule engine takes priority (`70% rules / 30% ML`).
- **Critical rule override:** If severe threats like asking for OTP, CVV, bank passwords, or upfront recruitment fees are detected, the score is elevated to ensure high-risk classification regardless of generic text styling.
- **Verdict Thresholds:**
  - `Risk Score >= 65`: **Likely Scam / Fake Job / Fake News** (🔴 Danger)
  - `30 <= Risk Score < 65`: **Suspicious / Caution Advised** (🟡 Warning)
  - `Risk Score < 30`: **Likely Safe / Legitimate / Credible** (🟢 Safe)

---

## 📁 Project Structure

```
trustshield/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app, REST endpoints (/scam, /job, /news, /explain)
│   ├── ml.py              # ML inference, pipeline loader, hybrid scoring, safe tips
│   ├── rules.py           # English & Hinglish regex engine, span offsets, threat weights
│   ├── explainer.py       # Google AI Studio (Gemma / Gemini) + offline fallback
│   └── schemas.py         # Pydantic request/response models & validation
├── static/
│   ├── index.html         # Single-page UI with 3 tabs, gauge meter, chips & tips
│   ├── style.css          # Responsive design, custom glowing highlights, gauge SVG
│   └── app.js             # Interactive tab switching, API calls, dynamic render
├── data/                  # Place uploaded Kaggle/UCI CSVs here
├── models/                # Trained joblib models
│   ├── scam_model.joblib
│   ├── job_model.joblib
│   └── news_model.joblib
├── train.py               # Model training script with held-out test set metrics
├── test_suite.py          # Complete unit test suite (10/10 tests)
├── Dockerfile             # Container configuration (Hugging Face Spaces ready)
├── requirements.txt       # Production dependencies
├── .env.example           # Environment variables template
└── README.md              # Documentation & Deployment Guide
```

---

## ⚡ Quickstart (Run Locally)

### 1. Prerequisites
- Python 3.9+ (Python 3.10, 3.11, 3.12, 3.13, 3.14 supported)
- pip

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Navigate to the project root
cd trustshield

# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure Environment (Optional for Gemma Explanations)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your Google AI Studio API key (free tier available at [aistudio.google.com](https://aistudio.google.com/)):
```env
GEMINI_API_KEY=your_google_ai_studio_api_key_here
```
> *Note:* If no API key is provided, TrustShield automatically uses its built-in heuristic explanation generator so the app continues working with zero errors during live hackathon demos!

### 4. Start the Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser and navigate to:
👉 **`http://localhost:8000`**

---

## 🎯 Model Training (`train.py`)

TrustShield includes pre-trained models out of the box using built-in curated multilingual seed datasets. You can also retrain on full Kaggle & UCI datasets:

### Datasets Supported
Place your CSV files directly into the `data/` directory:
1. **Scam Dataset:** UCI SMS Spam Collection (`data/spam.csv` or `data/SMSSpamCollection.txt`)
2. **Job Dataset:** Kaggle Fake and Real Job Postings / EMSCAD (`data/fake_job_postings.csv`)
3. **News Dataset:** Kaggle Fake News / ISOT / WELFake (`data/news.csv` or `data/WELFake_Dataset.csv`)

### Run Training
```bash
python train.py
```
`train.py` automatically:
- Detects whether your CSVs are present in `data/` or smoothly falls back to the curated seed datasets.
- Splits into an 80/20 held-out stratified test set.
- Computes and prints **Accuracy, Precision, Recall, and F1-score**.
- Serializes the optimized scikit-learn pipelines to `models/*.joblib`.

---

## 🧪 Running the Automated Test Suite

To verify all endpoints, validation errors, and regex heuristics:
```bash
python -m unittest discover -s . -p "test_suite.py"
```
Output:
```
..........
----------------------------------------------------------------------
Ran 10 tests in 2.621s

OK
```

---

## 🚀 Deployment Guides

### Option 1: Hugging Face Spaces (Recommended for Hackathons)
1. Create a new Space on [huggingface.co/spaces](https://huggingface.co/spaces) with **Docker** SDK.
2. Push the TrustShield repository files (including `Dockerfile`).
3. Under Space **Settings** -> **Variables and Secrets**, add:
   - Secret Name: `GEMINI_API_KEY`
   - Secret Value: *(Your Google AI Studio API Key)*
4. HF Spaces automatically builds the Docker image and serves the web app on port `7860`.

### Option 2: Streamlit Cloud / Render / Railway
1. **Render / Railway Web Service:**
   - Build Command: `pip install -r requirements.txt && python train.py`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add Environment Variable: `GEMINI_API_KEY`

### Option 3: Replit
1. Import repo into Replit.
2. Select **Python** template.
3. In Replit Secrets tab, add `GEMINI_API_KEY`.
4. Run command: `uvicorn app.main:app --host 0.0.0.0 --port 8080`.

---

## ⚖️ Disclaimer & Privacy Policy

- **AI-Assisted Aid:** TrustShield is an AI-assisted detection tool designed for educational and informational purposes. It is not an absolute guarantee. Always verify critical alerts directly with official banking, government, or educational authorities.
- **Privacy First:** TrustShield operates strictly with volatile in-memory processing. User messages and inputs are **never logged to disks or persistent databases**.
- **National Help Resources:**
  - National Cyber Crime Reporting Portal: [cybercrime.gov.in](https://cybercrime.gov.in)
  - National Cyber Helpline: **1930**
  - Department of Telecommunications Chakshu Portal: [sancharsaathi.gov.in](https://sancharsaathi.gov.in)
  - Press Information Bureau Fact Check: [factcheck.pib.gov.in](https://factcheck.pib.gov.in)
