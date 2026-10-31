"""
TrustShield Comprehensive Test Suite
Tests handlers, Pydantic validation, heuristics, ML inference, and explainer.
"""

import os
import unittest
from pydantic import ValidationError
from fastapi import HTTPException
from app.main import check_scam, check_job, check_news, explain_result, health_check, validate_input_text
from app.schemas import CheckRequest, ExplainRequest
from app.rules import analyze_heuristics
from app.ml import analyze_text
from app.explainer import generate_fallback_explanation


class TestTrustShield(unittest.TestCase):

    def test_health_check(self):
        res = health_check()
        self.assertEqual(res["status"], "healthy")
        self.assertEqual(res["service"], "TrustShield")

    def test_empty_input_validation(self):
        # 1. Pydantic schema rejection for empty string
        with self.assertRaises(ValidationError):
            CheckRequest(text="")

        # 2. Pydantic schema rejection for too short string (< 3 chars)
        with self.assertRaises(ValidationError):
            CheckRequest(text="hi")

        # 3. Handler validation for whitespace only
        with self.assertRaises(HTTPException) as ctx:
            validate_input_text("     ")
        self.assertEqual(ctx.exception.status_code, 422)

    def test_scam_checker_english_danger(self):
        text = "URGENT: Your SBI account will be blocked today! Update your KYC and submit OTP at https://bit.ly/sbi-kyc"
        req = CheckRequest(text=text)
        res = check_scam(req)
        
        self.assertEqual(res.verdict, "Likely Scam")
        self.assertEqual(res.verdict_type, "danger")
        self.assertGreaterEqual(res.risk_score, 65)
        self.assertIn("<mark", res.highlighted_html)
        self.assertTrue(len(res.flags) >= 2)
        self.assertIn("AI-assisted aid", res.disclaimer)
        self.assertIn("never saved", res.privacy_note)
        self.assertTrue(len(res.safe_action_tips) >= 2)

    def test_scam_checker_hinglish_danger(self):
        text = "Aapka loan pass ho gaya hai! Jaldi karo, last chance. Sirf Rs 1500 registration fee Paytm karo aur turant paise pao: 9898989898"
        req = CheckRequest(text=text)
        res = check_scam(req)
        
        self.assertIn(res.verdict, ["Likely Scam", "Suspicious"])
        self.assertGreaterEqual(res.risk_score, 50)
        phrases = [f.phrase.lower() for f in res.flags]
        self.assertTrue(any("jaldi" in p or "registration fee" in p or "last chance" in p for p in phrases))

    def test_scam_checker_safe(self):
        text = "Dear student, the campus library will remain open until 9 PM for the mid-semester examination period. Happy studying!"
        req = CheckRequest(text=text)
        res = check_scam(req)
        
        self.assertEqual(res.verdict, "Likely Safe")
        self.assertEqual(res.verdict_type, "success")
        self.assertLess(res.risk_score, 35)

    def test_job_checker_fake_recruitment(self):
        text = "Direct joining for Google Remote Intern! Earn 50k daily. No interview required! Pay Rs 1500 laptop courier fee. DM on Telegram @hr_jobs."
        req = CheckRequest(text=text)
        res = check_job(req)
        
        self.assertEqual(res.verdict, "Likely Fake / Scam Job")
        self.assertEqual(res.verdict_type, "danger")
        self.assertGreaterEqual(res.risk_score, 65)
        self.assertTrue(any("Never Pay" in tip.title for tip in res.safe_action_tips))

    def test_job_checker_legitimate(self):
        text = "TCS is conducting national qualifier test for engineering graduates. Apply on https://careers.tcs.com. Three interview rounds required. No fees charged."
        req = CheckRequest(text=text)
        res = check_job(req)
        
        self.assertEqual(res.verdict, "Likely Legitimate Job")
        self.assertEqual(res.verdict_type, "success")

    def test_news_checker_fake_forward(self):
        text = "FORWARD TO EVERYONE! UNESCO has declared Indian National Anthem best in the world! Share before it is deleted right now!!!"
        req = CheckRequest(text=text)
        res = check_news(req)
        
        self.assertEqual(res.verdict, "Likely Fake News / Hoax")
        self.assertEqual(res.verdict_type, "danger")
        self.assertGreaterEqual(res.risk_score, 60)
        self.assertTrue(any("PIB" in tip.title or "PIB" in tip.description for tip in res.safe_action_tips))

    def test_news_checker_credible(self):
        text = "The Reserve Bank of India has maintained the benchmark interest rate at 6.5 percent following the bi-monthly monetary policy committee meeting."
        req = CheckRequest(text=text)
        res = check_news(req)
        
        self.assertEqual(res.verdict, "Likely Credible News")
        self.assertEqual(res.verdict_type, "success")

    def test_explain_endpoint_fallback(self):
        req = ExplainRequest(
            text="Your SBI account will be blocked. Send OTP immediately.",
            checker_type="scam",
            verdict="Likely Scam",
            risk_score=85,
            flags=["OTP", "Account blocked"]
        )
        res = explain_result(req)
        self.assertTrue(len(res["explanation"]) > 20)
        self.assertIn("Verify with official sources", res["disclaimer"])

    def test_all_sample_scam_messages(self):
        # Sample 1: English threat
        r1 = check_scam(CheckRequest(text="Dear customer, your SBI YONO account will be blocked today! Update your PAN & Aadhaar immediately at https://bit.ly/sbi-kyc-update to avoid permanent suspension."))
        self.assertEqual(r1.verdict, "Likely Scam")
        self.assertEqual(r1.verdict_type, "danger")

        # Sample 2: Hinglish loan trap
        r2 = check_scam(CheckRequest(text="Aapka 50,000 ka pre-approved loan approve ho chuka hai! Jaldi karo last chance hai. Sirf Rs 1,500 registration fee Paytm pe transfer karein aur turant paise pao: 9898989898"))
        self.assertEqual(r2.verdict, "Likely Scam")
        self.assertEqual(r2.verdict_type, "danger")

        # Sample 3: Safe college notice
        r3 = check_scam(CheckRequest(text="Dear Student, your semester examination hall ticket has been published on the official college intranet. Please login with your university roll number to download."))
        self.assertEqual(r3.verdict, "Likely Safe")
        self.assertEqual(r3.verdict_type, "success")

    def test_all_sample_job_messages(self):
        # Sample 1: English telegram fee trap
        r1 = check_job(CheckRequest(text="Urgent Requirement: Direct selection for Google Remote Data Entry Intern! Earn 50k daily working from home. No interview required! Pay Rs 1,500 laptop courier fee. DM on Telegram @google_hr_officer"))
        self.assertEqual(r1.verdict, "Likely Fake / Scam Job")
        self.assertEqual(r1.verdict_type, "danger")

        # Sample 2: Hinglish video like job
        r2 = check_job(CheckRequest(text="Ghar baithe kamao! Rozana kamayein Rs 3000 sirf YouTube videos like karke. Direct joining bina kisi interview ke. Registration fee Rs 500 refundable deposit. WhatsApp karein: 9123456789"))
        self.assertEqual(r2.verdict, "Likely Fake / Scam Job")
        self.assertEqual(r2.verdict_type, "danger")

        # Sample 3: Safe campus drive
        r3 = check_job(CheckRequest(text="Infosys is hiring Junior Software Engineer Interns for Summer 2026. Eligibility: B.Tech CS/IT with 65% aggregate. Two technical rounds and one HR round required. Apply on official portal https://careers.infosys.com. No fees charged at any stage."))
        self.assertEqual(r3.verdict, "Likely Legitimate Job")
        self.assertEqual(r3.verdict_type, "success")

    def test_all_sample_news_messages(self):
        # Sample 1: English health hoax
        r1 = check_news(CheckRequest(text="ALERT: WHO warns that drinking cold water causes heart attacks immediately! Banned in Europe! Share before it's deleted! Forward to everyone in your family groups right now!!!"))
        self.assertEqual(r1.verdict, "Likely Fake News / Hoax")
        self.assertEqual(r1.verdict_type, "danger")

        # Sample 2: Hinglish anthem / free recharge forward
        r2 = check_news(CheckRequest(text="Dhamaka khabar! UNESCO ne Indian National Anthem ko world ka best anthem declare kiya hai! Aur sarkar sabhi students ko 3 months free recharge de rahi hai. Jaldi sabko share karo!"))
        self.assertEqual(r2.verdict, "Likely Fake News / Hoax")
        self.assertEqual(r2.verdict_type, "danger")

        # Sample 3: Safe scientific mission news
        r3 = check_news(CheckRequest(text="ISRO has successfully launched the INSAT-3DS meteorological satellite from Satish Dhawan Space Centre in Sriharikota, achieving the desired geostationary transfer orbit as confirmed in the official press release."))
        self.assertEqual(r3.verdict, "Likely Credible News")
        self.assertEqual(r3.verdict_type, "success")


if __name__ == "__main__":
    unittest.main()
