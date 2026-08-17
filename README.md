# CyberTot: AI Child Safety & Parental Intelligence System

CyberTot is a parental-control app for Indian families with children aged 8 to 14. The child's device produces a constant stream of raw activity like app sessions, YouTube titles, chat messages, and web visits.

Parents want to know two key things:
1. **Is my child safe right now?** (Real-time alert status and risk score)
2. **What happened today?** (Parent-friendly summary of daily activity and insights)

This system turns that raw stream into those two answers using a privacy-first, on-device machine learning model coupled with a selective LLM briefing engine.

---

## Problem Overview & System Architecture

### The Problem
Raw child activity stream example:
```json
[
  {"ts":"2026-08-11T16:12:44+05:30","type":"app_session","app":"com.roblox.client","duration_s":4820},
  {"ts":"2026-08-11T17:41:02+05:30","type":"chat_message","app":"com.whatsapp","direction":"received","text":"tu kitna noob hai yaar, uninstall kar de game","counterparty":"class_group"},
  {"ts":"2026-08-11T19:20:31+05:30","type":"web_visit","domain":"freerobuxgenerator.xyz","title":"FREE ROBUX - just enter your parents card"},
  {"ts":"2026-08-11T21:47:03+05:30","type":"chat_message","app":"com.roblox.client","direction":"received","text":"how old r u? u seem mature for ur age. do u have insta? dont tell ur mom we talk","counterparty":"unknown_user_8812"},
  {"ts":"2026-08-11T22:58:19+05:30","type":"chat_message","app":"com.whatsapp","direction":"sent","text":"kuch samajh nahi aa raha, sone ka mann bhi nahi karta aajkal","counterparty":"best_friend"}
]
```

### Key Engineering Constraints

* **Scale (~50 Million Events/Day)**: Sending every event to an LLM fails on cost, latency, and privacy. We train a lightweight core ML model running locally on-device in under 1ms per message. An LLM is invoked only to summarize aggregated alert metadata for parents.
* **Asymmetric Errors**: A missed grooming attempt puts a real child in danger (False Negative). A false alarm is a parent wrongly confronting a child (False Positive). These are not equally bad. We optimize the **Macro F2 Score (beta = 2)** to prioritize Recall over Precision on danger categories.
* **Messy Input**: Handles Hinglish, code-switching, gaming trash talk, teen hyperbole, and sarcasm.
* **Context**: Incorporates metadata multipliers like late-night hours (10 PM to 5 AM) and unknown sender anonymity.
* **Minors Data (India DPDP Act)**: All raw text processing stays local on the child device. Zero raw text leaves the device.
* **Synthetic Dataset**: Built a realistic synthetic dataset simulating Indian child digital activity (real children data is prohibited under DPDP).

---

## Technical Design & Defense

### 1. Training Pipeline & Model Architecture
* **Model Choice**: TF-IDF Vectorizer (ngram range 1-2, sublinear TF) + Logistic Regression.
* **Why**: Executes in under 1ms on CPU, small memory footprint, handles Hinglish slang, and produces probability outputs suitable for decision threshold tuning.

### 2. Decision Threshold Tuning & Evidence
* **Asymmetric Threshold Tuning**: Lowered decision thresholds for grooming (0.15) and distress (0.15) compared to default (0.50).
* **Threshold Sweep Evidence**:
  * At threshold T = 0.90: Grooming Recall = 0.0% (Total Failure, Macro F2 = 0.0846).
  * At threshold T = 0.80: Grooming Recall = 31.7% (68% missed danger, Macro F2 = 0.6146).
  * At tuned threshold T = 0.15: Grooming Recall = 100.0% (Zero missed danger, Macro F2 = 0.9493).

### 3. Metric Selection for Imbalanced Safety
* **Headline Metric**: Macro F2 Score.
* **Why**: Accuracy is misleading on imbalanced safety data. F2 weights Recall twice as heavily as Precision to penalize False Negatives on grooming, distress, and cyberbullying.

### 4. Selective LLM Boundary & Privacy Architecture
* **On-Device Trained Model**: 100% of raw chat messages, YouTube titles, and web visits are classified locally on the device.
* **Selective LLM Integration**: Gemini API is used strictly to turn aggregated high-level alert counts and screen time totals into natural language parent summaries ("What happened today?").

### 5. Engineering Quality & Modularity
* Modular codebase structure under `src/`, automated training scripts, interactive web server (`src/app.py`), and Jupyter evaluation notebook (`notebooks/cybertot_analysis.ipynb`).

---

## Final Performance Evaluation

Evaluated on 480 test events across 6 safety categories:

| Risk Category | Precision | Recall | F1-Score | F2-Score | Support | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Grooming** | 0.95 | 1.00 | 0.98 | 0.990 | 82 | Zero Missed Threats |
| **Distress & Self-Harm** | 0.94 | 1.00 | 0.97 | 0.995 | 78 | Zero Missed Threats |
| **Cyberbullying** | 0.95 | 0.96 | 0.96 | 0.962 | 84 | High Protection |
| **Inappropriate Content** | 0.98 | 1.00 | 0.99 | 0.995 | 87 | Zero Missed Threats |
| **Scam & Phishing** | 0.92 | 1.00 | 0.96 | 0.982 | 67 | Zero Missed Threats |
| **Safe Chat & Gaming** | 0.95 | 0.74 | 0.84 | 0.778 | 82 | Controlled Trade-off |
| **Overall Accuracy** | - | - | **0.95** | - | **480** | - |
| **Macro Average** | **0.95** | **0.95** | **0.95** | **0.9493** | **480** | **Optimal Safety** |

---

## Project Structure

```
CyberTot/
├── data/                       # Generated synthetic datasets and daily streams
│   ├── train.csv
│   ├── test.csv
│   └── sample_daily_stream.json
├── models/                     # Saved model artifacts (.joblib)
│   └── safety_classifier.joblib
├── notebooks/                  # Interactive evaluation notebook
│   └── cybertot_analysis.ipynb
├── src/                        # Source code modules
│   ├── data_generator.py       # Synthetic dataset and scenario stream generator
│   ├── classifier.py           # Model training and asymmetric threshold evaluation
│   ├── aggregator.py           # Contextual risk engine (time and anonymity logic)
│   ├── llm_summarizer.py       # Selective LLM parent briefing generator
│   ├── app.py                  # FastAPI web application server
│   ├── main.py                 # CLI entrypoint runner
│   └── templates/
│       └── index.html          # Responsive dark-themed dashboard UI
├── requirements.txt            # Python dependencies
└── README.md                   # System documentation and technical defense
```

---

## Execution Guide

### 1. Run Main Pipeline via CLI
Execute data generation, model training, contextual analysis, and briefing generation:
```bash
python src/main.py --scenario grooming_attempt
```

Available preset scenarios: `--scenario safe_day`, `grooming_attempt`, `cyberbullying`, `scam_trap`.

### 2. Launch FastAPI Web Dashboard
Start the interactive dashboard at `http://127.0.0.1:8000`:
```bash
python src/main.py --server
```

### 3. Open Jupyter Notebook
Inspect metrics, confusion matrices, and threshold tuning curves:
```bash
jupyter notebook notebooks/cybertot_analysis.ipynb
```

---

## 🧑 Author

**Vasu Goel**

[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:vasugoel2754@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/vasugoel503/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/vasug27)
