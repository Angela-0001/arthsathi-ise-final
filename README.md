# ArthSathi — AI-Powered Multilingual Financial Companion

Voice-first, multilingual financial guidance for underprivileged communities in India.
Works on smartphones, WhatsApp/Telegram, and basic feature phones (IVR).

## Project Structure

```
arthsathi-final/
├── backend/          # FastAPI backend — API, DB, all services
│   ├── app/          # routes, models, services
│   └── bot/          # Telegram + WhatsApp bot (Node.js)
├── frontend/         # Next.js web/PWA
└── arthsathi-ml/     # ML core (separate repo: Angela-0001/arthsathi-ml)
    ├── translation/  # Our own seq2seq model + FastAPI endpoint
    ├── language_model/ # Our own GPT-style LM for scheme Q&A
    ├── models/       # Scheme + insurance recommenders, adaptive engine
    ├── speech/       # Offline ASR (Vosk) + TTS (pyttsx3)
    ├── channels/     # IVR (Asterisk), WhatsApp, Telegram handlers
    └── data/         # Collection + cleaning scripts
```

## Quick Start

### 1. Install backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# API docs → http://localhost:8000/docs
```

### 2. Install and run bot
```bash
cd backend/bot
npm install
# Copy .env.example to .env and add TELEGRAM_BOT_TOKEN
node src/index.js
```

### 3. Install frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 4. ML training (run on Kaggle GPU)
```bash
# Open arthsathi-ml/notebooks/01_quickstart.ipynb on Kaggle
# Enable GPU T4, run all cells
# Download checkpoints and put in arthsathi-ml/translation/checkpoints/
```

### 5. Start ML services (after training)
```bash
cd arthsathi-ml
# Translation API
uvicorn translation.serve:app --port 5001

# Language Model API  
uvicorn language_model.serve:app --port 5002
```

## Research Gaps Addressed
1. No multilingual financial/legal LLM for rural Indian languages
2. No scheme/welfare eligibility domain in any existing model
3. Digital financial inclusion tools assume smartphone + internet
4. No low-latency offline translation for financial/legal domain

## Team Split
- Member A — Scheme data + recommender + language model training
- Member B — Insurance data + recommender + adaptive engine
- Member C — Translation model + ASR/TTS + IVR/channels

## Tech Stack
- Backend: FastAPI + SQLite/PostgreSQL
- Frontend: Next.js + Tailwind
- Bot: Node.js + Grammy (Telegram) + Twilio (WhatsApp)
- Translation: Custom seq2seq transformer (built from scratch)
- LM: Custom GPT-style decoder (built from scratch)
- ASR: Vosk (offline)
- TTS: pyttsx3 (offline)
- IVR: Asterisk AGI
