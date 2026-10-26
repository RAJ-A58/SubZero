# ❄️ SubZero (VeriDeprovision)
### The Verifiable Autonomous SaaS Deprovisioning & Contract Renegotiation Engine

<div align="center">

![Meta Global AI Developer Hackathon 2026](https://img.shields.io/badge/Meta%20Global%20AI-Developer%20Hackathon%202026-blue?style=for-the-badge)
![Theme](https://img.shields.io/badge/Theme-Build%20for%20Your%20World%20%7C%20Push%20the%20Frontier-orange?style=for-the-badge)
![Models](https://img.shields.io/badge/Meta%20Stack-SAM%203.1%20%7C%20Muse%20Wonder%20%7C%20Muse%20Spark-purple?style=for-the-badge)
![Verification](https://img.shields.io/badge/Sandbox-Modal%20Serverless%20Twin-green?style=for-the-badge)

**Built for the Meta Global AI Developer Hackathon 2026**

</div>

---

## 📌 Executive Summary

Every enterprise is quietly hemorrhaging capital on SaaS subscriptions—Gartner estimates over **$34 billion annually** in wasted licenses, unused seats, and auto-renewed zombie contracts.

While autonomous software auditing seems obvious, companies are terrified of letting AI touch their software subscriptions due to **three catastrophic risks**:

1. **The Infrastructure Outage Trap:** Headless CI/CD bots, webhook tokens, and critical integration service accounts have **zero human logins**. A naive AI flags them as "dead seats" and cancels them, instantly halting engineering pipelines.
2. **The Contract Fine-Print Trap:** Enterprise Master Services Agreements (MSAs) hide early termination penalties ($1,500–$10,000+) and strict 30/60-day auto-renewal notice windows. Canceling at the wrong time or missing a notice deadline locks companies into multi-thousand dollar contracts.
3. **The Vendor Dark Pattern:** Enterprise software cannot be cancelled with a simple button click. Vendors require formal legal notices citing contract clauses, filing specific offboarding tickets, or navigating multi-step vendor cancellation workflows.

**SubZero** is the world’s first **Cryptographically Verifiable Autonomous SaaS Deprovisioning & Contract Renegotiation System**. It bridges visual contract comprehension, deterministic payoff calculation, and digital-twin sandbox simulations to eliminate SaaS waste with **zero risk of production downtime**.

---

## 🏗️ System Architecture

```
                                  [ Scanned Enterprise Contracts & Invoices ]
                                                       │
                                                       ▼
      ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
      │  1. VISUAL-LEGAL DOCUMENT INTELLIGENCE                                                          │
      │  • SAM 3.1: Zero-shot visual segmentation of pricing tables, riders, and fine-print clauses     │
      │  • Meta Muse Wonder: Multimodal extraction of auto-renewal dates, notice windows & penalties    │
      └────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                       │ Structured Contract Model
                                                       ▼
      ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
      │  2. VERIFIABLE POLICY & PAYOFF ENGINE                                                           │
      │  • Meta Muse Spark Open (1026 on Baseten): Multi-step Chain-of-Verification (CoVe) planner      │
      │  • Net Present Value (NPV) Solver: Evaluates [Cancel Now] vs [Downgrade Tier] vs [Notice Alarm] │
      └────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                       │ Candidate Action Plan
                                                       ▼
      ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
      │  3. DIGITAL-TWIN SIMULATION SHIELD (Modal Sandboxes)                                            │
      │  • Spawns an ephemeral Modal sandbox replicating mock Okta IDP, GitHub Actions & webhooks       │
      │  • Dry-runs deprovisioning to cryptographically verify zero broken tokens or service pipelines  │
      └────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                       │ Simulation Proof: PASSED ✅
                                                       ▼
      ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
      │  4. EXECUTIVE COCKPIT & VOICE AUTHORIZATION                                                     │
      │  • Meta Muse Voice Transcribe: Real-time voice command & biometric approval override           │
      │  • Formal Termination Letter Synthesizer: Generates legally binding notice citing exact MSA     │
      │  • Modern Interactive Dashboard: Real-time telemetry, visual contract inspect & audit log       │
      └─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ How SubZero Exploits the Meta AI Stack

SubZero deeply integrates the newest Meta model suite across vision, reasoning, voice, and infrastructure:

| Model / Technology | Integration Role | Why It Outperforms |
| :--- | :--- | :--- |
| **Meta SAM 3.1** *(Segment Anything)* | Zero-Shot Document Layout Segmentation | Scanned multi-column MSAs break standard OCR. SAM 3.1 segments discrete visual bounding masks around fee tables, cancellation riders, and addendum blocks. |
| **Meta Muse Wonder** | Multimodal Legal Clause Extraction | Interprets SAM-segmented regions to accurately extract notice windows (e.g. `30 days`), renewal dates, and early exit fees without hallucination. |
| **Meta Muse Spark Open (`1026`)** | Verifiable Policy & Reasoning Engine | Hosted on **Baseten** (2M TPM limit). Generates structured action plans: `IMMEDIATE_CANCEL`, `DOWNGRADE_TIER`, `SCHEDULE_NOTICE`, or `RENEGOTIATE`. |
| **Modal Sandboxes** | Ephemeral Digital Twin Simulation | Simulates live enterprise identity environments (Okta, GitHub, Slack) to dry-run deprovisioning and catch headless bot traps before touching production. |
| **Meta Muse Voice Transcribe** | Executive Voice Command & Approval | Enables executives to conduct voice debriefings and issue authenticated vocal commands (*"Authorize Notion downgrade; freeze Salesforce seat"*). |
| **Meta Muse Code** | Dynamic Connector & API Script Synthesis | Generates customized API offboarding payloads and formal vendor legal termination letters. |

---

## 🎯 The Three Adversarial Traps SubZero Solves

### Trap 1: The Headless CI/CD Service Account (Downtime Trap)
* **The Scenario:** Subscription `sw_204` has had `0 human logins` in 90 days.
* **Naive AI Failure:** Flags it as an abandoned seat and cuts it, instantly breaking production deployment pipelines.
* **SubZero’s Solution:** The Modal Sandbox Digital Twin dry-runs the termination. The sandbox catches active webhook traffic and automated git commits, reclassifying the account as a protected headless bot.

### Trap 2: The Auto-Renewal Deadline Trap (Cost Trap)
* **The Scenario:** An enterprise contract auto-renews on December 1st for $24,000 with a strict **30-day written notice requirement**.
* **Naive AI Failure:** Ignores the notice window until it’s too late, locking the company into another full billing cycle.
* **SubZero’s Solution:** Muse Wonder identifies the notice window and establishes an automated **Notice Countdown Alarm** alerting management before the deadline expires.

### Trap 3: The Early-Termination Fee Penalty (Mathematical Trap)
* **The Scenario:** A $200/month idle license has a contract clause requiring an $1,800 liquidation fee if terminated before Month 12.
* **Naive AI Failure:** Cancels immediately to save $200, incurring an immediate $1,800 net loss.
* **SubZero’s Solution:** The Payoff Engine calculates Net Present Value (NPV), determining that downgrading to a free tier or scheduling a non-renewal notice saves more money than an early termination penalty.

---

## 🗂️ Repository Structure

```text
SubZero/
├── contracts/               # Sample enterprise MSAs, SOWs, and contract test fixtures
│   ├── datadog_msa.pdf
│   ├── figma_enterprise.pdf
│   └── notion_workspace_terms.pdf
├── server/                  # Backend orchestration & Meta API integration
│   ├── app.py               # FastAPI gateway
│   ├── vision_parser.py     # SAM 3.1 segmentation & Muse Wonder document extractor
│   ├── decision_engine.py   # Muse Spark Open reasoning & payoff solver
│   ├── voice_handler.py     # Muse Voice Transcribe processor
│   └── legal_generator.py   # Formal contract termination letter synthesizer
├── sandbox/                 # Modal digital twin simulation
│   ├── modal_twin.py        # Modal serverless sandbox definition
│   └── mock_enterprise.py   # Mock Okta, GitHub Actions, and webhook event generator
├── frontend/                # Interactive React / Vite Executive Dashboard
│   ├── src/
│   │   ├── components/      # Contract viewer, simulation logs, voice visualizer
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
└── README.md
```

---

## 🚀 Quickstart & Installation

### Prerequisites
* Python 3.10+
* Node.js 18+
* [Modal CLI](https://modal.com/docs/guide) (`pip install modal`)
* Meta Model API Key & Baseten API Key

### 1. Clone & Set Up the Repository
```bash
git clone https://github.com/RAJ-A58/SubZero.git
cd SubZero
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
META_MODEL_API_KEY="your-meta-model-api-key"
BASETEN_API_KEY="your-baseten-api-key"
MODAL_TOKEN_ID="your-modal-token-id"
MODAL_TOKEN_SECRET="your-modal-token-secret"
```

### 3. Backend Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install fastapi uvicorn pydantic requests modal
```

### 4. Run the Digital Twin Sandbox Simulation
```bash
modal run sandbox/modal_twin.py
```

### 5. Launch the Dashboard
```bash
cd frontend
npm install
npm run dev
```

---

## 🏆 Hackathon Alignment & Verification

* **Verifiable Agent Track:** Incorporates pre-execution dry-run state verification inside isolated Modal sandboxes.
* **No Basic RAG / No Disqualified Anti-Projects:** Zero generic chat wrappers; executes real-world actions, legal analysis, and automated deprovisioning.
* **Deterministic Financial Payoffs:** Computes mathematically grounded ROI calculations for SaaS portfolios.

---

## 📄 License
This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
