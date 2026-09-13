# Contributing to HustleYetu

Thank you for your interest in contributing to **HustleYetu**! 🇰🇪

HustleYetu is an open-source civic technology platform dedicated to making legislative and regulatory changes in Kenya transparent, accessible, and actionable for informal sector workers (such as boda boda operators, taxi drivers, and micro-entrepreneurs).

Whether you are fixing a bug, adding support for a new county regulation, improving Swahili translations, optimizing our AI multi-agent pipeline, or refining the mobile UI, your contributions are warmly welcome.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat all contributors and community members with respect, empathy, and professionalism.

---

## Ways to Contribute

1. **Suggest a Kenyan Bill or Policy**: Help us keep legislative tracking up to date. Open a [Bill Request Issue](https://github.com/stevewanash/hustleyetu/issues/new?template=bill_request.md) with links to parliament or county gazette notices.
2. **Report Bugs**: If you encounter errors, broken links, or calculation discrepancies, submit a detailed [Bug Report](https://github.com/stevewanash/hustleyetu/issues/new?template=bug_report.md).
3. **Enhance AI Agents & Data Ingestion**: Improve PDF parsing reliability (via `pdfplumber`/OCR), refine prompts, enhance regex value extractors, or optimize pgvector RAG verification.
4. **Improve Translations**: Verify and enrich plain-language Swahili translations for legal and tax terminology.
5. **Frontend & Mobile UX**: Improve responsive design, accessibility (a11y), offline support, and low-bandwidth performance on mobile devices.

---

## Development Setup & Workflow

### 1. Fork and Clone
```bash
# 1. Fork the repo on GitHub, then clone your fork:
git clone https://github.com/<your-username>/hustleyetu.git
cd hustleyetu

# 2. Add upstream remote:
git remote add upstream https://github.com/stevewanash/hustleyetu.git
```

### 2. Create a Topic Branch
Branch from `main` using descriptive naming conventions:
```bash
git checkout -b feat/swahili-impact-clarity
# or
git checkout -b fix/pdf-table-parser-bounds
# or
git checkout -b docs/add-supabase-rls-guide
```

### 3. Local Environment
- Follow the instructions in the [README.md](README.md#getting-started-local-development) to configure your `.env` file from `.env.example`.
- Set up both the `backend/` (FastAPI) and `frontend/` (Next.js) environments.

### 4. Code Standards & Style
- **Python**: Follow [PEP 8](https://peps.python.org/pep-0008/). Use clear docstrings, type annotations, and Pydantic schemas.
- **JavaScript/React**: Use idiomatic React (Next.js App Router). Keep UI components modular and responsive.
- **Commit Messages**: We follow [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat: add boda boda county permit extraction script`
  - `fix: resolve SMS delivery timeout on Africa's Talking sandbox`
  - `docs: update local Supabase migration instructions`
  - `test: add unit tests for RAG verifier citation match`

---

## Testing Your Changes

Before submitting your Pull Request, ensure that all tests pass:

```bash
# Backend tests
cd backend
pytest -v

# Frontend build & lint checks
cd ../frontend
npm run lint
npm run build
```

---

## Critical Civic Tech & Data Ethics Guidelines

When contributing to HustleYetu, please keep our core civic principles in mind:

1. **Zero Secret Leaks**: Never commit `.env` files, production database passwords, Africa's Talking API keys, or cloud credentials. Ensure git push protection is active.
2. **Citizen Privacy**: Never commit or log real citizen phone numbers or personal identifiers. Any test fixtures must use synthetic or mock phone numbers (e.g. `+254700000000`).
3. **No Revenue Ingestion**: HustleYetu explicitly does *not* track, collect, or store informal business turnover or earnings. Do not introduce features that store user revenue.
4. **Factual Integrity & Verifiability**: All legislative summaries and financial formulas must cite specific clauses, sections, and schedules of the source bills. AI outputs must be verifiable against the primary legal text.

---

## Submitting a Pull Request (PR)

1. Ensure your branch is rebased with the latest `upstream/main`:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```
2. Push your branch to your GitHub fork:
   ```bash
   git push origin feat/your-feature-name
   ```
3. Open a Pull Request against `stevewanash/hustleyetu:main`.
4. Fill out the [Pull Request Template](.github/pull_request_template.md) detailing the motivation, changes made, and verification steps.

---

## Contributor Licensing Agreement

By submitting a Pull Request to HustleYetu, you agree that your contributions will be licensed under the project's [Mozilla Public License 2.0 (MPL-2.0)](LICENSE).
