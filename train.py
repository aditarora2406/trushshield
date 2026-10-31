"""
TrustShield Model Training Suite
Trains 3 TF-IDF + Logistic Regression models:
1. Scam Message Model (UCI SMS Spam / Seed dataset)
2. Fake Job Model (Kaggle Fake & Real Job Postings / Seed dataset)
3. Fake News Model (ISOT / WELFake / Seed dataset)

Reads uploaded CSVs from /data/ if present; otherwise seeds representative
multilingual (English + Hinglish) training sets so the app is immediately operational.
Evaluates on a held-out test set (80/20 split) and outputs Accuracy, Precision, Recall, and F1.
Saves models to /models/ directory using joblib.
"""

import os
import glob
import joblib
import pandas as pd
from typing import Tuple
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Curated high-fidelity seed datasets for instant bootstrap & fallback
SEED_SCAM_DATA = [
    # Safe SMS / WhatsApp messages
    ("Hey, are we still meeting for group study at the library at 5 PM?", 0),
    ("Your college fee receipt for Semester 4 has been generated. View on ERP portal.", 0),
    ("Mom said dinner is ready, please come home soon.", 0),
    ("Dear student, tomorrow's CS201 lab has been rescheduled to Thursday 2 PM.", 0),
    ("Happy Birthday Rahul! Have a wonderful year ahead bro.", 0),
    ("Bhai project submit kar diya tune? Code GitHub pe push kar de.", 0),
    ("Reminder: Your book return date at central library is 15th November.", 0),
    ("Can you please send the lecture notes for digital electronics?", 0),
    ("Sir please check my assignment attached in the email.", 0),
    ("Your Uber OTP is 4829. Do not share unless boarding.", 0),
    ("Swiggy delivery partner is arriving in 5 minutes with your order.", 0),
    ("Kal subah 9 baje practical exam hai, roll number slip leke aana.", 0),
    ("Thanks for paying your electricity bill of Rs 1420. Transaction reference #891273.", 0),
    ("Amazon: Your package will be delivered today between 2 PM and 6 PM.", 0),
    ("Bhai shaam ko canteen me milte hain, chai piyenge.", 0),
    
    # Scam SMS / WhatsApp messages
    ("Dear customer, your SBI YONO account will be blocked today! Update your PAN & Aadhaar immediately at https://bit.ly/sbi-kyc-update", 1),
    ("Congratulations! You have won Rs 25,00,000 in KBC Lucky Draw! Call WhatsApp officer at 9876543210 to claim prize now.", 1),
    ("Dear User, your electricity power will be disconnected tonight at 9:30 PM due to unpaid bill. Immediately call 9123456789.", 1),
    ("URGENT: Your parcel is on hold at customs. Pay Rs 499 clearance charge now at http://customs-track.xyz/pay", 1),
    ("Aadhaar OTP is 918234 for bank verification. Bank manager calling to verify. Turant batao.", 1),
    ("Part time work from home: Earn Rs 5,000 to 10,000 daily by liking YouTube videos! DM on Telegram @earn_fast_money", 1),
    ("Jaldi karo! Last chance to claim your free Rs 1000 Amazon gift voucher. Click here: https://tinyurl.com/free-loot-fest", 1),
    ("Your SIM card will be deactivated within 24 hours by TRAI. Share OTP with our executive to complete verification.", 1),
    ("Account suspended! Send your debit card CVV and PIN to restore access immediately.", 1),
    ("Aapka 50,000 ka loan approve ho chuka hai. Processing fee Rs 1,500 Paytm pe transfer karein: 9898989898", 1),
    ("Credit card reward points Rs 9,850 expiring tonight. Redeem cash directly to your bank account: http://redeem-reward-points.vip", 1),
    ("Bhai lottery lag gayi teri! Turant is link pe click kar aur registration fee deke claim kar.", 1),
    ("Police e-Challan pending against your vehicle. Pay Rs 2,000 fine within 2 hours or warrant issued: http://192.168.1.1/challan", 1),
    ("Free government laptop scheme for all students! Register with Aadhaar card and pay Rs 350 courier charge at https://bit.ly/pm-laptop", 1),
]

SEED_JOB_DATA = [
    # Legitimate Job / Internship Postings
    ("Software Engineer Intern at Infosys. Requirements: B.Tech Computer Science, solid knowledge of Python, Java, Data Structures. 2 rounds of technical interviews + HR round. Apply on https://careers.infosys.com", 0),
    ("Frontend Developer (React.js) at Zomato. Gurgaon office / Hybrid. Minimum 1 year experience with TypeScript, React, Redux. Competitive stipend Rs 45,000/month. No fees required at any stage of recruitment.", 0),
    ("Data Analyst Trainee - TCS Campus Drive 2026. Eligibility: 60% aggregate in graduation. Written test on TCS iON platform followed by interview. Official correspondence from @tcs.com only.", 0),
    ("Research Assistant in Machine Learning - IIT Delhi. 6 months funded project. Stipend as per DST norms (Rs 31,000 + HRA). Send resume and statement of purpose to prof_ml@iitd.ac.in.", 0),
    ("Graphic Design Intern - Swiggy Design Team. Must have portfolio showcasing UI/UX or vector illustration. Formal interview with Design Lead. Apply via official LinkedIn job portal.", 0),
    ("Junior Backend Developer - Python/FastAPI. Remote within India. Full-time role with healthcare benefits and PF. Code pair programming interview required. Send CV to jobs@fintechstartup.in", 0),
    ("Content Writer Internship - EdTech company. 3 months duration. Paid stipend Rs 15,000/month. Writing sample evaluation followed by 30-min Google Meet conversation. Apply on company career site.", 0),
    
    # Fake Job / Internship Postings
    ("Urgent requirement: Direct selection for Data Entry Operator! Earn Rs 40,000/month working from home. No interview required! Registration fee Rs 1,200 refundable with first salary. WhatsApp 9876543210.", 1),
    ("Congratulations! You have been selected for Google Remote Internship. Monthly salary 1.5 Lakh INR. Send Rs 3,500 for company laptop courier and training kit to UPI id hr.google@paytm.", 1),
    ("Work from home: Earn 50k daily by copy-pasting text and rating hotels on Telegram. No skills needed, students welcome. DM on Telegram @hr_officer_jobs. Urgent vacancy, apply jaldi!", 1),
    ("Amazon Customer Care Representative hiring! Direct joining without interview. Email your resume to amazon.hiring.careers2026@gmail.com and pay verification charge Rs 999.", 1),
    ("Part-time typing job: Earn Rs 2,000 per day. Pay Rs 500 security deposit first. Rozana ghar baithe kamao. WhatsApp message only to 9123456780.", 1),
    ("TATA Motors mega campus hiring! Guaranteed job placement with 8 LPA package. Pay document verification fees Rs 2,500 via Google Pay to HR Manager.", 1),
    ("Selected for Senior Analyst at Microsoft India! Directly receive offer letter. Contact HR on WhatsApp only: +91-9988776655. Laptop security deposit required.", 1),
]

SEED_NEWS_DATA = [
    # Real News / Credible Headlines
    ("ISRO successfully launches new weather satellite from Sriharikota space centre, official press release confirms.", 0),
    ("Reserve Bank of India keeps repo rate unchanged at 6.5 percent following Monetary Policy Committee review meeting.", 0),
    ("Delhi University releases official admission schedule for 2026 undergraduate courses on du.ac.in portal.", 0),
    ("Indian meteorological department predicts heavy rainfall in coastal regions over the next 48 hours; red alert issued.", 0),
    ("CBSE issues circular warning schools against unauthorized textbooks and reminding students to refer to NCERT curriculum.", 0),
    ("Government of India announces launch of new semiconductor fabrication facility in Gujarat with Rs 22,000 crore investment.", 0),
    ("Health ministry advises citizens to complete routine vaccinations; seasonal flu cases show mild increase in northern states.", 0),
    ("Indian railway announces 50 special trains for upcoming festival rush, bookings available on IRCTC official website.", 0),
    
    # Fake News / Viral Misinformation
    ("FORWARD TO EVERYONE! UNESCO has declared Indian National Anthem as the best anthem in the world! Share before it's deleted!!!", 1),
    ("ALERT: WHO warns that drinking cold water causes heart attacks immediately! Banned in Europe! Share with all WhatsApp groups now!", 1),
    ("NASA confirmed huge radiation storm hitting Earth tonight at 12:30 AM! Keep your mobile phones switched off! Forward to family!", 1),
    ("FREE RECHARGE SCEME: Prime Minister is giving free 3 months recharge to all students for 2026 elections! Click link to activate: http://pm-free-recharge.xyz", 1),
    ("BREAKING: WhatsApp will start charging Rs 499 per month from tomorrow unless you forward this message to 20 people! Dhamaka khabar!", 1),
    ("SHOCKING TRUTH: Doctors don't want you to know this simple kitchen spice 100% cures cancer in 3 days! Media won't show this!", 1),
    ("Government to deposit Rs 1,00,000 in every student's bank account tomorrow morning under new scheme. Check name in list: http://scheme-list.top", 1),
]


def load_scam_dataset() -> Tuple[pd.DataFrame, str]:
    """
    Looks for UCI SMS Spam dataset in data/ (spam.csv, sms.csv, SMSSpamCollection).
    Falls back to robust seed dataset if not present.
    """
    candidates = glob.glob(os.path.join(DATA_DIR, "*spam*")) + glob.glob(os.path.join(DATA_DIR, "*sms*"))
    for filepath in candidates:
        try:
            if filepath.endswith(".csv"):
                # Check for standard UCI spam columns (v1, v2 or label, text)
                df = pd.read_csv(filepath, encoding="latin-1")
                if "v1" in df.columns and "v2" in df.columns:
                    df = df[["v1", "v2"]].rename(columns={"v1": "label", "v2": "text"})
                    df["label"] = df["label"].map({"ham": 0, "spam": 1})
                    return df.dropna(), f"Loaded {filepath} ({len(df)} rows)"
                elif "label" in df.columns and "text" in df.columns:
                    if df["label"].dtype == object:
                        df["label"] = df["label"].str.lower().map({"ham": 0, "spam": 1, "safe": 0, "scam": 1}).fillna(0).astype(int)
                    return df[["text", "label"]].dropna(), f"Loaded {filepath} ({len(df)} rows)"
            elif "SMSSpamCollection" in filepath:
                df = pd.read_csv(filepath, sep="\t", names=["label", "text"], encoding="utf-8")
                df["label"] = df["label"].map({"ham": 0, "spam": 1})
                return df.dropna(), f"Loaded {filepath} ({len(df)} rows)"
        except Exception as e:
            print(f"Notice reading {filepath}: {e}")

    # Fallback to seed dataset
    df = pd.DataFrame(SEED_SCAM_DATA, columns=["text", "label"])
    # Augment seed dataset with realistic permutations for balanced learning
    augmented = []
    for text, label in SEED_SCAM_DATA:
        augmented.append((text, label))
        augmented.append((text.lower(), label))
        augmented.append((text + " Contact urgently.", label if label == 1 else 0))
    df_aug = pd.DataFrame(augmented, columns=["text", "label"])
    return df_aug, "Built-in curated seed dataset (English + Hinglish)"


def load_job_dataset() -> Tuple[pd.DataFrame, str]:
    """
    Looks for Kaggle Fake and Real Job Postings / EMSCAD (fake_job_postings.csv, jobs.csv).
    Falls back to curated seed dataset if not present.
    """
    candidates = glob.glob(os.path.join(DATA_DIR, "*job*"))
    for filepath in candidates:
        try:
            if filepath.endswith(".csv"):
                df = pd.read_csv(filepath, encoding="utf-8", on_bad_lines="skip")
                if "fraudulent" in df.columns:
                    # Combine title, company_profile, description, requirements
                    text_parts = []
                    for col in ["title", "company_profile", "description", "requirements"]:
                        if col in df.columns:
                            text_parts.append(df[col].fillna(""))
                    if text_parts:
                        df["text"] = text_parts[0]
                        for part in text_parts[1:]:
                            df["text"] = df["text"] + " " + part
                    else:
                        df["text"] = df["description"].fillna("")
                    df["label"] = df["fraudulent"].astype(int)
                    return df[["text", "label"]].dropna(), f"Loaded {filepath} ({len(df)} rows)"
                elif "label" in df.columns and "text" in df.columns:
                    return df[["text", "label"]].dropna(), f"Loaded {filepath} ({len(df)} rows)"
        except Exception as e:
            print(f"Notice reading {filepath}: {e}")

    # Fallback to seed dataset
    augmented = []
    for text, label in SEED_JOB_DATA:
        augmented.append((text, label))
        augmented.append((text.lower(), label))
        augmented.append((text + " Immediate joining.", label))
    df = pd.DataFrame(augmented, columns=["text", "label"])
    return df, "Built-in curated seed dataset (English + Hinglish)"


def load_news_dataset() -> Tuple[pd.DataFrame, str]:
    """
    Looks for Kaggle Fake News / ISOT / WELFake dataset (news.csv, WELFake_Dataset.csv).
    Falls back to curated seed dataset if not present.
    """
    candidates = glob.glob(os.path.join(DATA_DIR, "*news*")) + glob.glob(os.path.join(DATA_DIR, "*fake*"))
    for filepath in candidates:
        try:
            if filepath.endswith(".csv"):
                df = pd.read_csv(filepath, encoding="utf-8", on_bad_lines="skip")
                label_col = None
                for col in ["label", "fraudulent", "is_fake", "target"]:
                    if col in df.columns:
                        label_col = col
                        break
                text_col = None
                for col in ["text", "title", "statement", "headline"]:
                    if col in df.columns:
                        text_col = col
                        break
                if label_col and text_col:
                    if "title" in df.columns and text_col != "title":
                        df["combined_text"] = df["title"].fillna("") + " " + df[text_col].fillna("")
                    else:
                        df["combined_text"] = df[text_col].fillna("")
                    df["label"] = df[label_col]
                    if df["label"].dtype == object:
                        df["label"] = df["label"].str.lower().map({"fake": 1, "real": 0, "true": 0}).fillna(0).astype(int)
                    return df[["combined_text", "label"]].rename(columns={"combined_text": "text"}).dropna(), f"Loaded {filepath} ({len(df)} rows)"
        except Exception as e:
            print(f"Notice reading {filepath}: {e}")

    # Fallback to seed dataset
    augmented = []
    for text, label in SEED_NEWS_DATA:
        augmented.append((text, label))
        augmented.append((text.lower(), label))
        augmented.append((text + " Share this news fast!", label))
    df = pd.DataFrame(augmented, columns=["text", "label"])
    return df, "Built-in curated seed dataset (English + Hinglish)"


def train_single_model(name: str, df: pd.DataFrame, source_desc: str, filename: str):
    """
    Trains a TF-IDF + Logistic Regression pipeline, evaluates on held-out test set,
    prints metrics, and saves to models/ directory.
    """
    print("\n" + "=" * 65)
    print(f"🎯 Training {name}")
    print(f"📁 Data Source: {source_desc}")
    print(f"📊 Dataset Size: {len(df)} samples ({df['label'].value_counts().to_dict()})")
    print("=" * 65)

    X = df["text"].astype(str)
    y = df["label"].astype(int)

    # Held-out 80/20 train/test split with stratify
    test_size = 0.20 if len(df) >= 20 else 0.25
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    # Scikit-learn Pipeline with TF-IDF (1-2 ngrams) + Logistic Regression
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=12000,
            sublinear_tf=True,
            strip_accents="unicode"
        )),
        ("clf", LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            C=1.5,
            random_state=42
        ))
    ])

    # Fit pipeline
    pipeline.fit(X_train, y_train)

    # Evaluate on held-out test set
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    print(f"📈 Evaluation Results on Held-out Test Set ({len(y_test)} samples):")
    print(f"   • Accuracy:  {acc * 100:.2f}%")
    print(f"   • Precision: {prec * 100:.2f}%")
    print(f"   • Recall:    {rec * 100:.2f}%")
    print(f"   • F1 Score:  {f1 * 100:.2f}%")
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred, digits=4, zero_division=0))

    # Save serialized model
    save_path = os.path.join(MODELS_DIR, filename)
    joblib.dump(pipeline, save_path)
    print(f"💾 Model saved successfully to: {save_path}")


def main():
    print("=================================================================")
    print("       🛡️  TrustShield Machine Learning Training Pipeline        ")
    print("=================================================================")
    print(f"Target Models Directory: {MODELS_DIR}")
    print(f"Source Data Directory:   {DATA_DIR}")

    # 1. Train Scam Message Model
    df_scam, scam_desc = load_scam_dataset()
    train_single_model("Scam Message Checker (SMS/WhatsApp)", df_scam, scam_desc, "scam_model.joblib")

    # 2. Train Fake Job Model
    df_job, job_desc = load_job_dataset()
    train_single_model("Fake Job / Internship Checker", df_job, job_desc, "job_model.joblib")

    # 3. Train Fake News Model
    df_news, news_desc = load_news_dataset()
    train_single_model("Fake News / Misinformation Checker", df_news, news_desc, "news_model.joblib")

    print("\n" + "=" * 65)
    print("🎉 All 3 TrustShield models trained and saved successfully!")
    print("=================================================================")


if __name__ == "__main__":
    main()
