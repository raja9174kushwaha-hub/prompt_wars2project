# 🗳️ ElectionGuide AI

> **Interactive Election Process Assistant** – powered by **Google Vertex AI (Gemini)** and deployed on **Google Cloud Run**.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini-1.5_Flash-4285F4?logo=google)](https://ai.google.dev)
[![Cloud Run](https://img.shields.io/badge/Cloud_Run-Deployed-4285F4?logo=googlecloud)](https://cloud.google.com/run)

---

## 📌 Overview

**ElectionGuide AI** is a lightweight, production-ready web application that helps citizens understand the election process through:

- 🤖 **AI Chat Assistant** – Ask any election question in natural language (Gemini-powered)
- 🗺️ **Interactive Election Flow** – Clickable step-by-step election phases
- 📅 **Timeline Visualiser** – Animated progress through election phases
- 📚 **Knowledge Articles** – Filterable educational content
- ❓ **Quiz** – 5-question knowledge test with instant feedback
- 🌐 **Bilingual** – Full English + Hindi support (AI responses in Devanagari)
- 🎤 **Voice Input** – Web Speech API for hands-free questions
- 📱 **PWA Installable** – Add to home screen on mobile/desktop

---

## 🧰 Tech Stack (100% Google Ecosystem)

| Layer | Technology |
|---|---|
| **Frontend** | HTML5 · CSS3 · Vanilla JS (zero dependencies) |
| **Backend** | Python 3.11 · FastAPI · Uvicorn |
| **AI / NLP** | Google Vertex AI – Gemini 1.5 Flash |
| **Deployment** | Google Cloud Run |
| **Container** | Docker (multi-stage, `python:3.11-slim`) |
| **VCS** | GitHub (repo < 10 MB) |

---

## 🏗️ Architecture

```
Browser (HTML/CSS/JS)
        │  REST (JSON)
        ▼
FastAPI Backend  ──────────►  Google Vertex AI (Gemini)
        │                             │
        │ static JSON (in-process)    │ structured prompt templates
        ▼                             ▼
  Election Knowledge Base      AI-generated responses
```

**Routing:** All pages are served by a single SPA (`index.html`). Navigation is hash-based, no page reloads.

---

## 📁 Project Structure

```
electionguide/
├── app/
│   ├── main.py                  # FastAPI app factory, middleware, routing
│   ├── routes/
│   │   ├── chat.py              # POST /api/chat/message, GET /api/chat/suggestions
│   │   ├── election.py          # GET /api/election/steps|phases|knowledge|quiz
│   │   └── health.py            # GET /api/health
│   ├── services/
│   │   ├── ai_service.py        # Gemini integration, prompt engineering, fallback
│   │   └── election_service.py  # In-process election knowledge base
│   ├── utils/
│   │   ├── validators.py        # Input sanitisation & validation
│   │   └── logging_config.py    # Structured logging
│   └── static/
│       ├── index.html           # Single-page application shell
│       ├── styles.css           # Design system, responsive, accessible
│       ├── app.js               # SPA router, chat, quiz, voice, animations
│       ├── sw.js                # Service worker (offline support)
│       └── manifest.json        # PWA manifest (installable app)
├── tests/
│   └── test_app.py              # 50 unit & integration tests
├── Dockerfile                   # Multi-stage, non-root, Cloud Run ready
├── requirements.txt             # Pinned Python deps
├── .env.example                 # Environment variable template
├── .gitignore
├── .dockerignore
└── README.md
```

---

## 🚀 Local Setup

### Prerequisites

- Python 3.11+
- A Google AI Studio API key: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

### 1. Clone & install

```bash
git clone https://github.com/your-org/electionguide-ai.git
cd electionguide-ai

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your-key-here
```

### 3. Run locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Open **http://localhost:8080**

### 4. Run tests

```bash
pytest tests/ -v --tb=short
```

Expected: **50 tests passing** in < 10 seconds.

---

## 🐳 Docker

### Build

```bash
docker build -t electionguide-ai .
```

### Run

```bash
docker run -p 8080:8080 \
  -e GEMINI_API_KEY=your-key-here \
  electionguide-ai
```

Open **http://localhost:8080**

### Check image size

```bash
docker image inspect electionguide-ai --format='{{.Size}}' | awk '{print $1/1024/1024 " MB"}'
# Target: < 200 MB
```

---

## ☁️ Cloud Run Deployment

### Prerequisites

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
```

### Option A – Direct source deploy (simplest)

```bash
gcloud run deploy electionguide-ai \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-key-here,ENVIRONMENT=production \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --port 8080
```

### Option B – Container registry deploy

```bash
# 1. Build & push image
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1
export IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/electionguide/app:latest"

gcloud artifacts repositories create electionguide \
  --repository-format=docker \
  --location=$REGION

gcloud auth configure-docker $REGION-docker.pkg.dev

docker build -t $IMAGE .
docker push $IMAGE

# 2. Deploy
gcloud run deploy electionguide-ai \
  --image $IMAGE \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-key-here \
  --memory 512Mi \
  --port 8080
```

### Secure API key with Secret Manager (recommended for production)

```bash
echo -n "your-key-here" | \
  gcloud secrets create GEMINI_API_KEY --data-file=-

gcloud run deploy electionguide-ai \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
  ... (other flags)
```

---

## 🔒 Security Features

| Feature | Implementation |
|---|---|
| **No exposed secrets** | Environment variables / Secret Manager |
| **Input sanitisation** | Unicode normalisation + HTML escaping |
| **Injection detection** | Regex-based prompt injection guard |
| **Rate limiting** | SlowAPI – 60 req/min global, 20 req/min on chat |
| **CORS** | Configurable origins via `ALLOWED_ORIGINS` env var |
| **Non-root container** | Dedicated `appuser` in Docker image |
| **XSS prevention** | All user content HTML-escaped before insertion |
| **Content-type validation** | Pydantic models enforce schema on every request |
| **Request tracing** | Unique `X-Request-ID` and `X-Response-Time` headers on every response |

---

## ⚡ Performance Features

| Feature | Detail |
|---|---|
| **Repo size** | < 10 MB (no bundled images, no node_modules) |
| **Docker image** | < 200 MB (multi-stage build, slim base) |
| **Zero JS frameworks** | Vanilla JS – no React/Angular/Vue bundle overhead |
| **CDN fonts** | Google Fonts loaded from CDN, not bundled |
| **Service worker** | Cache-first for static assets; offline-capable |
| **Lazy page init** | Each page section initialised only when first visited |
| **In-process data** | Election knowledge base is in-memory (no DB round-trip) |
| **Gemini Flash** | Fastest Gemini model – avg response < 1.5s |
| **PWA** | Installable app via `manifest.json` + service worker |
| **Bilingual AI** | Language-aware prompts for English and Hindi |

---

## 🎯 Evaluation Criteria Coverage

| Criterion | Implementation |
|---|---|
| ✅ **Code Quality** | Modular routes/services/utils, type hints, docstrings |
| ✅ **Security** | Input validation, rate limiting, CORS, no exposed keys |
| ✅ **Efficiency** | Minimal deps, lazy loading, in-process data, fast model |
| ✅ **Testing** | 50 pytest tests covering routes, validators, services |
| ✅ **Accessibility** | ARIA roles, skip link, keyboard nav, focus management, reduced-motion |
| ✅ **Google Services** | Vertex AI (Gemini), Cloud Run, Artifact Registry |

---

## 📊 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Liveness probe |
| GET | `/api/chat/suggestions` | Example questions |
| POST | `/api/chat/message` | AI chat response |
| GET | `/api/election/steps` | Election flow steps |
| GET | `/api/election/phases` | Timeline phases |
| GET | `/api/election/knowledge` | All knowledge articles |
| GET | `/api/election/knowledge/{id}` | Single article |
| GET | `/api/election/quiz` | Quiz questions |

Interactive docs: `http://localhost:8080/api/docs`

---

## 👥 Built For

**Hack2Skill Hackathon** – ElectionGuide AI submission.  
Fully Google-stack, Cloud Run deployable, < 10 MB repo.

---

*ElectionGuide AI is for educational purposes. Always verify election information with your official electoral commission.*
