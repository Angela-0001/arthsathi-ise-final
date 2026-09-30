# ArthSathi — AI-Powered Multilingual Financial Companion

> Voice-first, multilingual financial guidance for underprivileged communities in India.
> Works on smartphones, WhatsApp/Telegram, and basic feature phones (IVR/phone calls).

---

## The Problem

Over 800 million Indians are eligible for government welfare schemes — yet most never apply. The barriers are language, literacy, and access. Existing tools assume smartphone ownership, internet connectivity, and English or Hindi literacy. They ignore Marathi speakers, feature-phone users, and the rural poor who need help most.

Beyond schemes, millions sign loan and insurance documents they don't understand. Predatory clauses — forfeiture, unlimited liability, irrevocability — are buried in legal English that no one explains.

ArthSathi fixes this.

---

## What It Does

| Feature | Description |
|---|---|
| Scheme Matching | Matches users to eligible government welfare schemes based on age, income, occupation, and state |
| Document Risk Analysis | OCR + rule-based clause detection flags risky terms in loan/insurance documents |
| Financial Roadmap | Generates a personalised, step-by-step financial action plan |
| Multilingual | Hindi, Marathi, English — translated via our own self-hosted model |
| Multi-channel | Web app, Telegram bot, WhatsApp bot, IVR (feature phones) |
| Offline-first ML | Translation, ASR, TTS all run locally — no external API calls |

---

## Research Gaps Addressed

### Gap 1 — No multilingual financial/legal LLM for rural Indian languages
BharatGen's FinanceParam (the closest existing model) is English+Hindi only. Its quantized version scores **20.8% on its own benchmark — below random guessing (25%)**. It scores **0% on Taxation and Legal Finance** — the exact domains ArthSathi needs.
*Source: BharatGen BhashaBench-Finance; IndicFinNLP (LREC-COLING 2024)*

### Gap 2 — No scheme/welfare eligibility domain in any model or dataset
IndiaFinBench (arxiv 2025) documents that all Indian finance benchmarks draw from banking and taxation. No model has been trained or evaluated on government welfare scheme eligibility language. ArthSathi builds this from scratch: a fine-tuned model and evaluation set specifically for the scheme and insurance domain.

### Gap 3 — Financial inclusion tools assume smartphone + internet
UPI 123Pay covers payments for feature-phone users, but nothing covers scheme guidance, document safety, or insurance discovery without a smartphone. ArthSathi's IVR channel fills this gap using Asterisk (open-source PBX) with fully local inference.

### Gap 4 — No low-latency offline translation for financial/legal vocabulary
IndicTrans2 (AI Kosh) is the best open base model, but it is general-purpose. Financial/legal terms like "forfeit", "irrevocable", "PM-JAY eligibility" degrade in general NMT models. ArthSathi fine-tunes IndicTrans2 on a domain-specific parallel corpus and serves it via a self-hosted FastAPI endpoint.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Channels                         │
│  Web (Next.js)  Telegram  WhatsApp  IVR (Asterisk)  │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP
┌───────────────────────▼─────────────────────────────┐
│              FastAPI Backend (port 8000)             │
│                                                     │
│  /auth      — Phone OTP login                       │
│  /schemes   — Eligibility matching + engagement     │
│  /documents — OCR + risk clause detection           │
│  /roadmap   — Rule-based financial roadmap          │
│  /forms     — Playwright form auto-fill             │
│  /gateway   — Unified channel message dispatcher    │
│  /profile   — User profile management               │
│                                                     │
│  SQLite / PostgreSQL  ·  JWT auth  ·  APScheduler   │
└──────┬───────────────────────────┬──────────────────┘
       │                           │
┌──────▼──────┐           ┌────────▼────────┐
│  arthsathi  │           │  arthsathi-ml   │
│  -ml FAISS  │           │  Translation    │
│  Recommender│           │  API (port 5001)│
│  (schemes + │           │  LM API         │
│  insurance) │           │  (port 5002)    │
└─────────────┘           └─────────────────┘
```

---

## ML Components

### Scheme & Insurance Recommender
- Sentence embeddings via `paraphrase-multilingual-MiniLM-L12-v2`
- FAISS vector index for fast similarity search
- Hard eligibility filters (age, income, state, occupation)
- **Thompson Sampling bandit** (adaptive engine) — learns from user interactions in real time, ranking schemes users actually engage with higher over time

### Translation Model
- Custom seq2seq transformer trained from scratch
- Fine-tuned on domain-specific parallel corpus (PIB + myScheme + curated financial/legal text)
- Served as a self-hosted FastAPI endpoint — no external API calls
- Supports Hindi ↔ English and Marathi ↔ English

### Language Model
- Custom GPT-style decoder fine-tuned on BharatGen Param-1 (2.9B)
- LoRA fine-tuning on scheme Q&A + legal clause instruction data
- Evaluated against BhashaBench-Finance benchmark
- Served at port 5002

### ASR / TTS
- **ASR**: Vosk — fully offline, Hindi/Marathi, runs on CPU
- **TTS**: pyttsx3 — system voices, no internet, works on Windows/Linux/Mac
- Used by the IVR channel and Telegram voice note handling

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, aiosqlite, Alembic, APScheduler |
| Frontend | Next.js 15, React 18, TypeScript, Tailwind CSS |
| Bot | Node.js, Grammy (Telegram), Twilio (WhatsApp), Express |
| ML — Translation | Custom seq2seq transformer (PyTorch) |
| ML — LM | Custom GPT-style decoder (PyTorch), LoRA fine-tune |
| ML — Recommender | FAISS, sentence-transformers, Thompson Sampling bandit |
| ML — Speech | Vosk (ASR), pyttsx3 (TTS) |
| IVR | Asterisk AGI |
| Auth | Phone OTP + JWT |
| DB | SQLite (dev), PostgreSQL (prod) |

---

## Project Structure

```
arthsathi-final/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # auth, schemes, documents, roadmap, forms, gateway, profile
│   │   ├── core/             # config, database, security (JWT + OTP)
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── services/         # scheme_matcher, document_risk, translation, ocr, roadmap_engine
│   └── bot/
│       └── src/              # Telegram + WhatsApp bot (Node.js)
├── frontend/
│   └── src/
│       ├── app/              # Next.js pages: home, login, schemes, document, roadmap, profile
│       ├── components/       # BottomNav
│       └── lib/              # axios API client with JWT interceptor
└── arthsathi-ml/
    ├── data/                 # Collection + cleaning scripts, JSONL datasets
    ├── models/               # scheme_recommender, insurance_recommender, adaptive_engine
    ├── language_model/       # Custom GPT-style LM: train, serve, evaluate
    ├── translation/          # Custom seq2seq: train, serve, evaluate
    ├── speech/               # Vosk ASR, pyttsx3 TTS
    └── channels/             # IVR, WhatsApp, Telegram handlers
```

---

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# API docs → http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Bot (needs TELEGRAM_BOT_TOKEN)
```bash
cd backend/bot
npm install
# add TELEGRAM_BOT_TOKEN to backend/bot/.env
node src/index.js
```

### ML Services (after training)
```bash
cd arthsathi-ml
pip install -r requirements.txt

# Translation API (port 5001)
uvicorn translation.serve:app --port 5001

# Language Model API (port 5002)
uvicorn language_model.serve:app --port 5002
```

### ML Training (GPU recommended — run on Kaggle)
```bash
# Data collection
python data/scripts/collect_schemes.py
python data/scripts/collect_insurance.py
python data/scripts/clean_and_format.py

# Build FAISS indexes
python models/scheme_recommender/train.py
python models/insurance_recommender/train.py

# Fine-tune translation + LM (GPU)
python translation/train.py
python language_model/train.py
```

---

## AI Kosh Resources

| Resource | Used For |
|---|---|
| [Param-1 (2.9B)](https://aikosh.indiaai.gov.in/home/models/details/bharatgen_param_1) | Base model for language model fine-tuning |
| [IndicTrans2](https://aikosh.indiaai.gov.in/home/models/details/indic_trans2.html) | Base model for translation fine-tuning |
| [Samanantar](https://aikosh.indiaai.gov.in/home/datasets/details/samanantar) | Parallel corpus for translation training |
| [BhashaBench-Finance](https://aikosh.indiaai.gov.in/home/datasets/details/bhashabench_finance.html) | Evaluation benchmark |
| [Sangraha](https://aikosh.indiaai.gov.in/home/datasets/details/sangraha.html) | Indic pretraining data |

---

## Team

| Member | Owns |
|---|---|
| A | Scheme data collection · FAISS scheme recommender · Language model fine-tuning |
| B | Insurance data · Insurance recommender · Thompson Sampling adaptive engine |
| C | Translation model · ASR/TTS · IVR + WhatsApp + Telegram channels |
