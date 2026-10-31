/**
 * TrustShield Frontend Logic
 * Dynamic tab management, sample loading, API interaction, 
 * in-text red-flag rendering, animated score gauges, and AI explanation.
 */

let currentTab = 'scam';
let lastResult = null;
let lastInputText = '';

// Curated demo-ready samples: exactly 3 per tab (including at least 1 Hinglish each)
const SAMPLE_MESSAGES = {
  scam: [
    {
      label: "🚨 Bank KYC Threat (English)",
      type: "scam",
      text: "Dear customer, your SBI YONO account will be blocked today! Update your PAN & Aadhaar immediately at https://bit.ly/sbi-kyc-update to avoid permanent suspension."
    },
    {
      label: "💸 Loan Scam (Hinglish)",
      type: "scam",
      text: "Aapka 50,000 ka pre-approved loan approve ho chuka hai! Jaldi karo last chance hai. Sirf Rs 1,500 registration fee Paytm pe transfer karein aur turant paise pao: 9898989898"
    },
    {
      label: "✅ College Notice (Safe)",
      type: "safe",
      text: "Dear Student, your semester examination hall ticket has been published on the official college intranet. Please login with your university roll number to download."
    }
  ],
  job: [
    {
      label: "⚠️ Telegram Fee Trap (English)",
      type: "scam",
      text: "Urgent Requirement: Direct selection for Google Remote Data Entry Intern! Earn 50k daily working from home. No interview required! Pay Rs 1,500 laptop courier fee. DM on Telegram @google_hr_officer"
    },
    {
      label: "💻 Video Like Job (Hinglish)",
      type: "scam",
      text: "Ghar baithe kamao! Rozana kamayein Rs 3000 sirf YouTube videos like karke. Direct joining bina kisi interview ke. Registration fee Rs 500 refundable deposit. WhatsApp karein: 9123456789"
    },
    {
      label: "✅ Campus Drive (Safe)",
      type: "safe",
      text: "Infosys is hiring Junior Software Engineer Interns for Summer 2026. Eligibility: B.Tech CS/IT with 65% aggregate. Two technical rounds and one HR round required. Apply on official portal https://careers.infosys.com. No fees charged at any stage."
    }
  ],
  news: [
    {
      label: "⚠️ Health Panic Hoax (English)",
      type: "scam",
      text: "ALERT: WHO warns that drinking cold water causes heart attacks immediately! Banned in Europe! Share before it's deleted! Forward to everyone in your family groups right now!!!"
    },
    {
      label: "📢 Free Scheme Viral (Hinglish)",
      type: "scam",
      text: "Dhamaka khabar! UNESCO ne Indian National Anthem ko world ka best anthem declare kiya hai! Aur sarkar sabhi students ko 3 months free recharge de rahi hai. Jaldi sabko share karo!"
    },
    {
      label: "✅ ISRO Mission (Safe)",
      type: "safe",
      text: "ISRO has successfully launched the INSAT-3DS meteorological satellite from Satish Dhawan Space Centre in Sriharikota, achieving the desired geostationary transfer orbit as confirmed in the official press release."
    }
  ]
};

const TAB_CONFIG = {
  scam: {
    title: "Scam Message Checker",
    desc: "Analyzes SMS, WhatsApp forwards, KYC expiry alerts, electricity cuts, and courier fraud.",
    placeholder: "Paste SMS, WhatsApp message, or email text here to verify...",
    btnText: "Check Message for Scams"
  },
  job: {
    title: "Fake Job & Internship Checker",
    desc: "Verifies internship offers, work-from-home gigs, Telegram tasks, and recruitment emails.",
    placeholder: "Paste internship or job posting text (from LinkedIn, Telegram, WhatsApp, email) here...",
    btnText: "Check Job Legitimacy"
  },
  news: {
    title: "Fake News & Forward Checker",
    desc: "Evaluates viral WhatsApp forwards, sensational headlines, authority claims, and hoax alerts.",
    placeholder: "Paste headline, claim, or forwarded viral message here to check credibility...",
    btnText: "Check News Credibility"
  }
};

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  renderSampleButtons();
  updateTextareaPlaceholder();
  lucide.createIcons();

  const textarea = document.getElementById("input-text");
  textarea.addEventListener("input", () => {
    document.getElementById("char-count").innerText = `${textarea.value.length} characters`;
    hideError();
  });
});

function switchTab(tab) {
  currentTab = tab;

  // Update tab buttons
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.remove("active");
    btn.classList.add("text-slate-600");
  });
  
  const activeBtn = document.getElementById(`tab-${tab}`);
  activeBtn.classList.add("active");
  activeBtn.classList.remove("text-slate-600");

  // Update UI text context
  const config = TAB_CONFIG[tab];
  document.getElementById("tool-title").innerText = config.title;
  document.getElementById("tool-desc").innerText = config.desc;
  document.getElementById("check-btn-text").innerText = config.btnText;
  
  updateTextareaPlaceholder();
  renderSampleButtons();
  hideError();
  
  // Re-run icons
  lucide.createIcons();
}

function updateTextareaPlaceholder() {
  const textarea = document.getElementById("input-text");
  textarea.placeholder = TAB_CONFIG[currentTab].placeholder;
}

function renderSampleButtons() {
  const container = document.getElementById("sample-buttons");
  container.innerHTML = "";

  const samples = SAMPLE_MESSAGES[currentTab];
  samples.forEach(sample => {
    const btn = document.createElement("button");
    btn.type = "button";
    
    let colorClasses = "bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300";
    if (sample.type === "scam") {
      colorClasses = "bg-red-50 hover:bg-red-100 text-red-700 border-red-200";
    } else if (sample.type === "safe") {
      colorClasses = "bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border-emerald-200";
    }

    btn.className = `text-xs font-medium px-2.5 py-1.5 rounded-lg border transition cursor-pointer flex items-center gap-1.5 ${colorClasses}`;
    btn.innerHTML = `<span>${sample.label}</span>`;
    btn.onclick = () => loadSample(sample.text);
    container.appendChild(btn);
  });
}

function loadSample(text) {
  const textarea = document.getElementById("input-text");
  textarea.value = text;
  document.getElementById("char-count").innerText = `${text.length} characters`;
  hideError();
  textarea.focus();
}

function clearInput() {
  const textarea = document.getElementById("input-text");
  textarea.value = "";
  document.getElementById("char-count").innerText = "0 characters";
  document.getElementById("results-container").classList.add("hidden");
  hideError();
  lastResult = null;
}

function showError(msg) {
  const errBox = document.getElementById("error-box");
  const errMsg = document.getElementById("error-message");
  errMsg.innerText = msg;
  errBox.classList.remove("hidden");
  lucide.createIcons();
}

function hideError() {
  document.getElementById("error-box").classList.add("hidden");
}

async function runCheck() {
  const textarea = document.getElementById("input-text");
  const text = textarea.value.trim();

  if (!text) {
    showError("Please enter or paste text to analyze.");
    textarea.focus();
    return;
  }

  if (text.length < 4) {
    showError("Input text is too short. Please enter at least 4 characters.");
    return;
  }

  hideError();
  setLoading(true);

  try {
    const endpoint = `/${currentTab}`;
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, explain_simply: false })
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server error: ${response.status}`);
    }

    const data = await response.json();
    lastResult = data;
    lastInputText = text;
    renderResults(data);

  } catch (err) {
    showError(err.message || "Failed to reach TrustShield backend. Ensure the server is running.");
  } finally {
    setLoading(false);
  }
}

function setLoading(isLoading) {
  const checkBtn = document.getElementById("check-btn");
  const checkIcon = document.getElementById("check-icon");
  const spinner = document.getElementById("loading-spinner");
  const btnText = document.getElementById("check-btn-text");

  if (isLoading) {
    checkBtn.disabled = true;
    checkIcon.classList.add("hidden");
    spinner.classList.remove("hidden");
    btnText.innerText = "Analyzing Text...";
  } else {
    checkBtn.disabled = false;
    checkIcon.classList.remove("hidden");
    spinner.classList.add("hidden");
    btnText.innerText = TAB_CONFIG[currentTab].btnText;
  }
}

function renderResults(data) {
  const container = document.getElementById("results-container");
  container.classList.remove("hidden");

  // 1. Verdict Card
  const verdictCard = document.getElementById("verdict-card");
  const verdictBadge = document.getElementById("verdict-badge");
  const verdictTitle = document.getElementById("verdict-title");
  const verdictSummary = document.getElementById("verdict-summary");
  const confidenceTag = document.getElementById("confidence-tag");

  verdictTitle.innerText = data.verdict;
  confidenceTag.innerText = data.confidence_label;

  // Visual Palette depending on verdict_type
  verdictCard.className = "md:col-span-2 rounded-2xl p-6 border transition flex flex-col justify-between shadow-sm ";
  
  if (data.verdict_type === "danger") {
    verdictCard.classList.add("bg-red-50/90", "border-red-200", "text-red-950");
    verdictBadge.className = "px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-red-600 text-white shadow-xs";
    verdictBadge.innerText = `Danger • ${data.verdict}`;
    verdictSummary.innerText = "This text triggers critical red flags characteristic of fraud, deceit, or high-risk scams. Exercise extreme caution.";
  } else if (data.verdict_type === "warning") {
    verdictCard.classList.add("bg-amber-50/90", "border-amber-200", "text-amber-950");
    verdictBadge.className = "px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-500 text-white shadow-xs";
    verdictBadge.innerText = `Caution • ${data.verdict}`;
    verdictSummary.innerText = "Several suspicious elements were detected. Do not click unverified links or share personal details without independent verification.";
  } else {
    verdictCard.classList.add("bg-emerald-50/90", "border-emerald-200", "text-emerald-950");
    verdictBadge.className = "px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-600 text-white shadow-xs";
    verdictBadge.innerText = `Safe • ${data.verdict}`;
    verdictSummary.innerText = "No common scam signatures or malicious manipulation patterns were detected. Follow standard internet hygiene.";
  }

  // Scoring Details
  document.getElementById("ml-prob-val").innerText = `${(data.ml_probability * 100).toFixed(1)}%`;
  document.getElementById("rule-score-val").innerText = `${data.rule_score}/100`;

  // 2. Animated Gauge Meter
  updateGauge(data.risk_score, data.verdict_type);

  // 3. Highlighted Text
  const textBox = document.getElementById("highlighted-text-box");
  textBox.innerHTML = data.highlighted_html || htmlEscape(data.text);

  // 4. Red Flag Chips
  const flagsContainer = document.getElementById("flags-chip-container");
  flagsContainer.innerHTML = "";

  if (data.flags && data.flags.length > 0) {
    data.flags.forEach(flag => {
      const chip = document.createElement("div");
      chip.className = "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-100 text-red-900 border border-red-200";
      chip.innerHTML = `
        <span class="w-1.5 h-1.5 rounded-full bg-red-600"></span>
        <strong>${escapeHtml(flag.category)}:</strong>
        <span>"${escapeHtml(flag.phrase)}"</span>
      `;
      flagsContainer.appendChild(chip);
    });
  } else {
    flagsContainer.innerHTML = '<span class="text-xs text-slate-400 italic">No red flags flagged in this text.</span>';
  }

  // 5. Safe Action Tips
  const tipsContainer = document.getElementById("tips-container");
  tipsContainer.innerHTML = "";

  if (data.safe_action_tips && data.safe_action_tips.length > 0) {
    data.safe_action_tips.forEach((tip, idx) => {
      const card = document.createElement("div");
      card.className = "p-4 rounded-xl border border-slate-200 bg-slate-50 flex flex-col justify-between hover:border-slate-300 transition space-y-2";
      
      let actionBtnHtml = "";
      if (tip.action_url) {
        actionBtnHtml = `
          <a href="${tip.action_url}" target="_blank" rel="noopener" class="mt-2 text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1">
            <span>Open Official Portal</span>
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
          </a>
        `;
      }

      card.innerHTML = `
        <div>
          <div class="flex items-center justify-between gap-1 mb-1">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Step ${idx + 1}</span>
            ${tip.badge ? `<span class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">${escapeHtml(tip.badge)}</span>` : ""}
          </div>
          <h5 class="text-sm font-bold text-slate-900">${escapeHtml(tip.title)}</h5>
          <p class="text-xs text-slate-600 mt-1 leading-relaxed">${escapeHtml(tip.description)}</p>
        </div>
        ${actionBtnHtml}
      `;
      tipsContainer.appendChild(card);
    });
  }

  // 6. Reset Explanation Section
  document.getElementById("explanation-box").classList.add("hidden");
  document.getElementById("explanation-text").innerText = "";
  document.getElementById("explain-btn-text").innerText = "Explain Simply";

  // Reinitialize Lucide icons
  lucide.createIcons();

  // Smooth scroll into results view
  container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function updateGauge(score, verdictType) {
  const scoreNum = document.getElementById("score-number");
  const gaugeCircle = document.getElementById("gauge-circle");
  const scoreLabel = document.getElementById("score-label");

  // Animate counter
  let currentVal = 0;
  const step = Math.max(1, Math.floor(score / 25));
  const timer = setInterval(() => {
    currentVal = Math.min(score, currentVal + step);
    scoreNum.innerText = currentVal;
    if (currentVal >= score) clearInterval(timer);
  }, 20);

  // Circle circumference is 2 * PI * 40 ≈ 251.2
  const circumference = 251.2;
  const offset = circumference - (score / 100) * circumference;
  gaugeCircle.style.strokeDashoffset = offset;

  // Color stroke and badge based on verdict
  gaugeCircle.classList.remove("stroke-red-500", "stroke-amber-500", "stroke-emerald-500");
  scoreLabel.className = "mt-3 text-xs font-semibold px-3 py-1 rounded-full ";

  if (verdictType === "danger") {
    gaugeCircle.classList.add("stroke-red-500");
    scoreLabel.classList.add("bg-red-100", "text-red-800");
    scoreLabel.innerText = "High Threat Level";
  } else if (verdictType === "warning") {
    gaugeCircle.classList.add("stroke-amber-500");
    scoreLabel.classList.add("bg-amber-100", "text-amber-800");
    scoreLabel.innerText = "Moderate Risk / Caution";
  } else {
    gaugeCircle.classList.add("stroke-emerald-500");
    scoreLabel.classList.add("bg-emerald-100", "text-emerald-800");
    scoreLabel.innerText = "Low Risk / Clean";
  }
}

async function requestExplanation() {
  if (!lastResult || !lastInputText) return;

  const btn = document.getElementById("explain-btn");
  const spinner = document.getElementById("explain-spinner");
  const btnText = document.getElementById("explain-btn-text");
  const explainBox = document.getElementById("explanation-box");
  const explainText = document.getElementById("explanation-text");

  btn.disabled = true;
  spinner.classList.remove("hidden");
  btnText.innerText = "Generating Explanation...";

  try {
    const flagPhrases = (lastResult.flags || []).map(f => f.phrase);
    const response = await fetch("/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: lastInputText,
        checker_type: currentTab,
        verdict: lastResult.verdict,
        risk_score: lastResult.risk_score,
        flags: flagPhrases
      })
    });

    if (!response.ok) throw new Error("Explanation request failed");
    const data = await response.json();

    explainText.innerText = data.explanation;
    explainBox.classList.remove("hidden");
    btnText.innerText = "Explained!";
  } catch (err) {
    explainText.innerText = "Scammers often create artificial urgency or request sensitive information. Genuine organizations never ask for passwords or upfront payments. Turant verify karein!";
    explainBox.classList.remove("hidden");
    btnText.innerText = "Explain Simply";
  } finally {
    btn.disabled = false;
    spinner.classList.add("hidden");
    lucide.createIcons();
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, m => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[m]);
}
