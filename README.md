# HustleYetu

[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Frontend-Next.js_14-black.svg)](https://nextjs.org/)
[![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E.svg)](https://supabase.com/)

> **Civic technology bridging Kenyan national legislation, county regulations, and the microenterprise sector.**  
> Built and awarded during the **Democracy & AI Hackathon** — hosted by the **Mozilla Foundation** & **KamiLimu**.

---

## The Team

| Name | Role | GitHub |
| :--- | :--- | :--- |
| **Steve Wanangwe** | Backend & AI Systems Architecture | [@SteveWanash](https://github.com/SteveWanash) |
| **Maryanne Farida** | Frontend & UX Architecture | [@MaryanneFarida](https://github.com/MaryanneFarida) |

**Team Name**: Techies &nbsp;|&nbsp; **Institutions**: JKUAT & USIU

---

## Problem Statement & Civic Context

### The Challenge
**83.8% of Kenya's workforce (over 18.1 million people)** operates within the informal economy (*Kenya Economic Survey 2026, KNBS*). Boda boda riders, tuk-tuk drivers, and small transport operators face routine financial blindsiding from national finance acts and county regulations passed without their advance awareness or meaningful input.

- **Sudden Financial Shocks**: Provisions like the Motor Vehicle Circulation Tax (2.5% of vehicle value) can impose unexpected lump sums (e.g. Ksh 5,000 for a boda boda rider or Ksh 17,500+ for an app driver) at annual insurance renewal.
- **Regulatory Penalties**: New county permit requirements, safety mandates, and route restrictions often become known to informal workers only at police checkpoints or county enforcement roadblocks.
- **The Information Asymmetry**: Traditional legislative platforms operate on a *pull* model requiring dense legal literacy, reliable desktop internet, and hours to parse 80+ page parliamentary bills.

### The HustleYetu Solution
HustleYetu is an AI-powered, mobile-first civic intelligence pipeline that:
1. **Monitors & Ingests** parliamentary bills and county regulatory notices.
2. **Models Real Financial Impacts** in Kenya Shillings (KES) tailored to specific informal worker profiles (Boda Boda, Taxi/Ride-hailing, Fleet Operators).
3. **Generates Compliance Checklists** in plain English and Swahili.
4. **Proactively Alerts Workers** via SMS and a lightweight Web App before public participation closes and before enforcement takes effect.
5. **Ensures Privacy-First Civic Engagement**: No revenue, turnover, or tax ledger data is ever stored, shielding informal workers from surveillance exposure while protecting their constitutional right to public participation.

---

## Architecture & Technology Stack

```
                     ┌──────────────────────────────────────────────┐
                     │           Next.js 14 Web Frontend            │
                     │ (Bill Explorer, Impact Calculator, Profile)  │
                     └───────────────────────┬──────────────────────┘
                                             │ HTTPS / JSON
                                             ▼
                     ┌──────────────────────────────────────────────┐
                     │               FastAPI Backend                │
                     │ ┌──────────────────────────────────────────┐ │
                     │ │       Multi-Agent AI Pipeline (RAG)      │ │
                     │ │ • Summarizer (DeepSeek / Gemini 2.0)     │ │
                     │ │ • Financial Impact Modeler               │ │
                     │ │ • Regulatory Verifier (pgvector)         │ │
                     │ │ • Swahili / English Translator           │ │
                     │ └──────────────────────────────────────────┘ │
                     │ • Regex Metric Extraction & Ingestion      │
                     │ • Africa's Talking SMS Dispatcher          │
                     └───────────────┬──────────────┬───────────────┘
                                     │              │
                    PostgreSQL / RLS │              │ Webhooks / SMS
                                     ▼              ▼
                     ┌───────────────────────┐  ┌───────────────────┐
                     │   Supabase Cloud DB   │  │  Africa's Talking │
                     │ (Auth, Vector, Data)  │  │   SMS Gateway     │
                     └───────────────────────┘  └───────────────────┘
```

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 14, React 18, CSS3 Design System | Responsive, mobile-first UI for exploring bills, calculating personalized impact, and managing SMS notification preferences. |
| **Backend** | FastAPI, Python 3.11+, Pydantic v2, Uvicorn | High-throughput REST API, webhook verification (Svix HMAC), and agent pipeline orchestration. |
| **AI & NLP** | Google Gemini 2.0 / DeepSeek, LangChain, pdfplumber, Tesseract OCR | Structured bill extraction, plain-language translation, numeric tax formula validation, and RAG verification. |
| **Database** | Supabase (PostgreSQL 15, pgvector, Row-Level Security) | Persistent storage for bill records, sector impacts, and privacy-preserving phone number registrations. |
| **Messaging** | Africa's Talking SMS API | Plain-language SMS alerts dispatched across Kenyan mobile networks. |

---

## Getting Started (Local Development)

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**
- **Supabase Account** (or local Supabase CLI instance)
- *(Optional)* **Tesseract OCR** (for scanned PDF bill ingestion)

---

### 1. Clone the Repository
```bash
git clone https://github.com/stevewanash/hustleyetu.git
cd hustleyetu
```

---

### 2. Configure Environment Variables
Copy the root `.env.example` file and configure your credentials:
```bash
cp .env.example .env
```
Key configuration settings required:
- `SUPABASE_URL` & `SUPABASE_KEY` (Supabase project settings)
- `SUPABASE_SERVICE_KEY` & `SUPABASE_DB_URL`
- `GEMINI_API_KEY` or `DEEPSEEK_API_KEY` (AI agents)
- `AFRICAS_TALKING_USERNAME` & `AFRICAS_TALKING_API_KEY` (SMS testing via sandbox)
- `ENCRYPTION_KEY` (32-byte AES key for profile privacy)
- `NEXT_PUBLIC_SUPABASE_URL` & `NEXT_PUBLIC_SUPABASE_ANON_KEY`

---

### 3. Backend Setup (FastAPI)
```bash
# Navigate to backend directory
cd backend

# Create and activate a Python virtual environment
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (apply SQL files in supabase/migrations/ to your Supabase project)

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```
Backend interactive API documentation will be live at `http://localhost:8000/docs`.

---

### 4. Frontend Setup (Next.js)
```bash
# In a separate terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## Running Tests

```bash
# Run backend test suite
cd backend
pytest -v

# Run frontend build check & linting
cd frontend
npm run lint
npm run build
```

---

## Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── agents/          # Multi-agent intelligence (Summarizer, Impact, Verifier, Translator)
│   │   ├── api/             # FastAPI route handlers (bills, impact, dashboard, webhooks)
│   │   ├── models/          # Pydantic schemas & business profile data structures
│   │   ├── services/        # Extractor, embedder, scraper, SMS notifier
│   │   └── main.py          # FastAPI application entrypoint
│   ├── data/                # Sample Kenyan legislative bills & fixtures
│   ├── scripts/             # Ingestion & database seeding scripts
│   └── tests/               # Backend test suite (pytest)
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router (bills, impact, dashboard, subscribe)
│   │   ├── lib/             # Supabase & API client configurations
│   │   └── styles/          # Responsive design system & CSS variables
│   └── package.json
├── supabase/
│   └── migrations/          # PostgreSQL schemas, RLS policies, & pgvector setups
├── docs/
│   ├── architectural_design.md
│   └── problemstatement.md
├── .env.example             # Safe sanitized environment template
├── CONTRIBUTING.md          # Contribution guidelines
├── CODE_OF_CONDUCT.md       # Contributor Covenant 2.1
├── SECURITY.md              # Vulnerability reporting & data privacy standards
└── LICENSE                  # Mozilla Public License 2.0 (MPL-2.0)
```

---

## Privacy & Responsible Data Governance

HustleYetu is engineered in compliance with Kenya’s **Data Protection Act (2019)**:
- **No Revenue Tracking**: We do not store turnover, income, or transaction histories.
- **Cryptographic Protection**: Phone numbers used for SMS alerts are isolated and encrypted using AES-256.
- **Opt-In / Opt-Out**: Subscribers retain complete control to pause or delete their notification profiles at any time.

---

## Contributing

We welcome contributions from developers, civic tech enthusiasts, policy analysts, and translators! Please read our [Contributing Guidelines](CONTRIBUTING.md) and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

For vulnerability disclosure, please review [SECURITY.md](SECURITY.md).

---

## License & Acknowledgements

- **License**: This project is open source and licensed under the [Mozilla Public License 2.0 (MPL-2.0)](LICENSE).
- **Acknowledgements**: Deep gratitude to the **Mozilla Foundation** and **KamiLimu** for championing democratic participation and artificial intelligence for public interest during the **Democracy & AI Hackathon**.

