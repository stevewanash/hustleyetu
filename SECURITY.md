# Security Policy

The **HustleYetu** team takes the security of our platform and the privacy of the citizens and informal sector workers we serve very seriously.

Because HustleYetu interacts with Kenyan legislative data and delivers SMS alerts to informal micro-entrepreneurs, maintaining the integrity of our calculations and the confidentiality of user communication records is paramount.

---

## Supported Versions

We provide security updates for the current main branch and the latest minor release:

| Version / Branch | Supported |
| :--- | :--- |
| `main` (Latest) | :white_check_mark: |
| < 0.1.0 | :x: |

---

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities via public GitHub issues.**

If you discover a security vulnerability, please report it privately:

1. **GitHub Private Vulnerability Reporting (Preferred)**:
   - Navigate to the **Security** tab of the repository on GitHub.
   - Click **Report a vulnerability** to open an advisory draft.
2. **Direct Email**:
   - Send an encrypted or confidential email to: **stevewanash1@gmail.com**
   - Subject line: `[SECURITY] HustleYetu Vulnerability Report`

### What to Include in Your Report
To help us triage and resolve the issue quickly, please include:
- A clear description of the potential vulnerability.
- Steps to reproduce (proof of concept script or request payload).
- Any affected endpoints, files, or configurations.
- The potential impact (e.g., unauthorized data access, SMS spoofing, webhook bypass, prompt injection).

### Response Timeline
- **Initial Acknowledgment**: Within 48 hours.
- **Triage & Severity Assessment**: Within 5 business days.
- **Fix & Public Disclosure**: We coordinate a responsible disclosure timeline once a patch is tested and deployed.

---

## Security & Privacy Architecture Highlights

When auditing or testing the project, please keep our security design in mind:

- **Row Level Security (RLS)**: All Supabase tables containing citizen feedback, subscriptions, and profiles are protected by PostgreSQL RLS policies. Direct read/write access is restricted to authenticated sessions or service-role calls.
- **SMS Webhook Verification**: All Supabase Auth Custom SMS webhooks are validated using cryptographic signatures (`Svix-Signature`, `Svix-Timestamp`, `Svix-Id`) using an HMAC-SHA256 secret.
- **Data Minimization (Kenya Data Protection Act 2019)**:
  - We do not store citizen income, tax returns, or business turnover.
  - Phone numbers stored for alert dispatch are isolated and encrypted using AES-256.
- **Prompt Injection Defense**: All multi-agent LLM prompts utilize strict structured Pydantic schema validation and citation verification against verified legislative text extracted from official gazettes.

---

## Recognition

We are grateful to security researchers who practice responsible disclosure. We are happy to publicly acknowledge your contribution in our release notes (unless you prefer to remain anonymous).
