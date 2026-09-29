# ProductPulse ⚡

> **AI Product Operations Agent with Persistent Organizational Decision Memory**  
> *Built with Hindsight Memory Engine & Google Gemini*

---

## 1. Overview
**ProductPulse** is an AI Product Operations Agent that bridges customer feedback, telemetry anomalies, and organizational decision memory. 

Most software organizations suffer from **organizational amnesia**: when critical incidents, latency spikes, or UX regressions occur, teams repeatedly spend days rediscovering the same root causes, repeating flawed investigations, or running redundant experiments that were already resolved months prior.

ProductPulse solves this by embedding **Hindsight** as a persistent organizational memory bank. It does not simply analyze today's complaints in isolation; it recalls past incidents, proven interventions, and measured KPI outcomes to guide product decisions with verified historical wisdom.

```
       DETECT ──► REMEMBER ──► REASON ──► DECIDE
         ▲                                  │
         │                                  ▼
       LEARN  ◄── MEASURE  ◄──── ACT  ◄── APPROVE
```

---

## 2. The Real Product Problem
* **Feedback Overload & Triage Fatigue**: Product teams receive hundreds of complaints across app versions, device segments, and product areas. Finding emerging anomalies is slow and noisy.
* **Loss of Organizational Context**: When team members leave or time passes, institutional memory of past bug fixes, architectural tradeoffs, and experiment outcomes is lost.
* **Unfocused Technical Investigations**: Without memory of prior error signatures, teams waste 3–5 days triaging central databases or central services when the real culprit is a known third-party SDK wrapper timeout.
* **Lack of Closed-Loop Learning**: Actions are executed, but their before-and-after metric shift is rarely quantified, and lessons are never systematically retained for future AI reasoning.

---

## 3. The ProductPulse Solution
ProductPulse establishes a closed-loop operations lifecycle:
1. **Deterministic Feedback Detection**: Automatically groups customer feedback by product area and segment, computing complaint growth rates (+1300% WoW), sentiment shifts, and concentration metrics.
2. **Persistent Hindsight Recall**: Queries Hindsight's memory bank using TEMPR retrieval to extract relevant historical incidents, previous decisions, and runbooks.
3. **Dual-Perspective AI Reasoning (Gemini)**: Synthesizes problem evidence alongside recalled memories, contrasting what a naive baseline would do vs. how past lessons focus the decision.
4. **Human-in-the-Loop Governance**: Enforces an explicit state machine requiring human authorization before any consequential action is executed.
5. **Deterministic Outcome Measurement**: Automatically compares pre-intervention vs. post-intervention complaint volumes and sentiment rebound.
6. **Continuous Organizational Learning**: Distills the verified outcome and lesson back into Hindsight, making future agent decisions faster and smarter.

---

## 4. Why Organizational Memory is Essential
Standard AI agents operate in a vacuum: given a prompt, they output generic advice based solely on public pre-training.

In enterprise product operations, **context is everything**. Knowing that:
* Incident `INC-104` proved that payment failure spikes on Android v4.8+ were caused by GooglePay SDK token wrapper timeouts rather than payment gateway outages,
* Adding an async retry fallback resolved 82% of complaints in 7 days,

transforms a blind 5-day backend investigation into an immediate, high-conviction hotfix.

---

## 5. Target User
* **Product Managers (PMs)**: Need actionable problem clustering, data-grounded intervention recommendations, and longitudinal impact measurements.
* **Product Operations Leads**: Responsible for operational health, customer support escalations, and cross-team incident postmortems.
* **Engineering Leads**: Benefit from precise historical runbooks and error signature matches that prevent redundant debugging.

---

## 6. Complete Agent Decision Lifecycle

| Phase | System Component | What Happens |
| :--- | :--- | :--- |
| **1. DETECT** | `detector.py` | Deterministically calculates complaint counts, trend percentages (+%), average sentiment, and segment concentration. Flags anomalies. |
| **2. REMEMBER** | `hindsight_manager.py` | Issues TEMPR search queries against the Hindsight Memory Bank to recall relevant past incidents and runbooks. |
| **3. REASON** | `decider.py` + Gemini | Contrasts decision pathways: *Reasoning With Memory* vs *Reasoning Without Memory*. Formulates strategic influence. |
| **4. DECIDE** | `decider.py` | Generates a strictly bounded action (`CREATE_INVESTIGATION`, `CREATE_EXPERIMENT`, or `CREATE_PRODUCT_CHANGE`). |
| **5. APPROVE** | `state_machine.py` | Human-in-the-loop gate: Product Manager reviews and authorizes (`APPROVED`) or rejects (`REJECTED`) the action. |
| **6. ACT** | `state_machine.py` | Transitions the action to `EXECUTED` and initiates telemetry monitoring (`MEASURING`). |
| **7. MEASURE** | `measurer.py` | Quantifies pre vs post metrics (complaint delta %, sentiment delta) and classifies outcome (`SUCCESS`, `PARTIAL_SUCCESS`, `REGRESSION`, `NO_CLEAR_IMPACT`, `INSUFFICIENT_EVIDENCE`). |
| **8. LEARN** | `hindsight_manager.py` | Distills the intervention lesson and retains it into Hindsight with structured metadata for future recall. |

---

## 7. How Hindsight is Used
Hindsight serves as the **persistent organizational memory layer**.

ProductPulse does not simply treat memory as a key-value store. It maintains structured decision lifecycles across 6 distinct categories:
* `PROBLEM`: Past incident title and failure signature.
* `EVIDENCE`: Quantitative complaint volume, error codes, and concentration.
* `DECISION`: Strategic triage choice (e.g. avoid database refactoring; patch client wrapper).
* `ACTION`: Exact hotfix or configuration deployed.
* `OUTCOME`: Verified before/after result (e.g. 82% reduction, conversion restored).
* `LESSON`: Distilled operational runbook rule.

### The Memory Feedback Loop
```
Past Problem ──► Past Evidence ──► Past Decision ──► Past Action ──► Past Outcome ──► Lesson
                                                                                         │
Future Better Decision ◄── Future AI Reasoning ◄── Hindsight TEMPR Recall ◄──────────────┘
```

---

## 8. Technical Architecture

### Mermaid Diagram
```mermaid
flowchart TD
    subgraph Feedback Ingestion & Telemetry
        FB[Synthetic Customer Feedback Dataset\nWeeks 1 - 4]
        DET[Deterministic Problem Detector\nCounts, Trends %, Sentiment, Severity]
        FB --> DET
    end

    subgraph Organizational Memory Layer
        HS[(Hindsight Memory Bank\nproductpulse-ops)]
        SEED[Seed Foundational Memories\nINC-104, EXP-042]
        SEED -.-> HS
    end

    subgraph AI Decision & Governance Engine
        REC[Hindsight TEMPR Recall\nProblem, Evidence, Decision, Action, Outcome, Lesson]
        GEM[Google Gemini LLM Reasoning\nPrompt: Problem + Evidence + Recalled Memories]
        CONTR[Decision Contrast Synthesizer\nWith Memory vs Without Memory]
        ACT_REC[Bounded Recommended Action\nINVESTIGATION | EXPERIMENT | PRODUCT_CHANGE]
        GOV{Human Approval Gate\nApprove or Reject}
        
        DET --> REC
        HS <--> REC
        REC --> GEM
        GEM --> CONTR
        CONTR --> ACT_REC
        ACT_REC --> GOV
    end

    subgraph Execution & Learning Loop
        SM[Action State Machine\nRECOMMENDED -> APPROVED -> EXECUTED -> MEASURING -> COMPLETED]
        MEAS[Deterministic Measurement Engine\nPre vs Post Volume, Sentiment Shift, Outcome Classification]
        LEARN[Lesson Distiller & Hindsight Retain]

        GOV -- Approved --> SM
        GOV -- Rejected --> REJ[Action Rejected / Blocked]
        SM --> MEAS
        MEAS --> LEARN
        LEARN -->|Retain Lesson & Metadata| HS
    end

    subgraph Presentation Layer
        UI[ProductPulse SaaS Operations UI\nInter, Responsive Dashboard, Stepper]
        UI <-->|REST API| DET
        UI <-->|REST API| ACT_REC
        UI <-->|REST API| GOV
        UI <-->|REST API| MEAS
        UI <-->|REST API| LEARN
    end
```

---

## 9. Tech Stack
* **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2
* **AI & LLM Reasoning**: Google Gemini (`google-genai` SDK, `gemini-2.5-flash`)
* **Organizational Memory**: Hindsight Memory Engine (`hindsight-client`, TEMPR recall, semantic search, reflection)
* **Frontend**: Vanilla HTML5, CSS3 (Linear/Stripe-inspired design system), Vanilla JavaScript (ES6+)
* **Testing**: Pytest, FastAPI TestClient (22 automated unit/integration tests)

---

## 10. Project Structure
```
ProductPulse/
├── backend/
│   ├── agent/
│   │   ├── decider.py          # Gemini AI reasoning layer, prompt builder, memory contrast
│   │   ├── detector.py         # Deterministic complaint frequency & trend analytics
│   │   ├── measurer.py         # Deterministic before/after measurement & lesson generation
│   │   └── state_machine.py    # Strict lifecycle state machine (Human governance)
│   ├── data/
│   │   ├── feedback_dataset.py # Synthetic feedback generator across 4 weeks
│   │   └── schema.py           # Typed Pydantic models for problems, actions, memories
│   ├── memory/
│   │   └── hindsight_manager.py# Hindsight client interface (Retain, Recall, Reflect)
│   ├── storage/                # Local data storage directory
│   ├── tests/
│   │   ├── test_agent_loop.py          # End-to-end headless lifecycle test
│   │   ├── test_ai_reasoning.py        # Gemini reasoning, prompt, & state machine tests
│   │   ├── test_hindsight_validation.py# Memory recall, metadata, & Case A vs B tests
│   │   ├── test_frontend_serving.py    # FastAPI static mount & SPA routing tests
│   │   ├── test_e2e_integration.py     # Fresh-start flow & rejection governance tests
│   │   └── test_reliability_audit.py   # Behaviors A-F (malformed outputs, API fallback)
│   ├── app.py                  # FastAPI server & REST API endpoints
│   └── config.py               # Application settings & environment configuration
├── frontend/
│   ├── index.html              # Product Operations single-page dashboard
│   └── static/
│       ├── css/
│       │   └── style.css       # SaaS theme, card elevations, animations, typography
│       └── js/
│           └── app.js          # Client controller, API connector, interactive stepper
├── .gitignore                  # Clean repository ignore rules (secrets, caches)
└── README.md                   # Complete documentation
```

---

## 11. Environment Variables

Create a `.env` file in the project root or configure environment variables:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | *(Required)* | Google Gemini API Key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model for AI reasoning |
| `HINDSIGHT_API_URL` | `http://127.0.0.1:8888` | URL of the Hindsight server |
| `HINDSIGHT_BANK_ID` | `productpulse-ops` | Target organizational memory bank ID |
| `HOST` | `127.0.0.1` | Application host |
| `PORT` | `8000` | Application port |

> **Note**: ProductPulse includes a resilient fallback memory cache in `hindsight_manager.py`. If a live external Hindsight daemon is not actively listening on port 8888, ProductPulse automatically uses its internal semantic recall and reflection engine without breaking the application.

---

## 12. Local Setup & Execution

### 1. Clone & Set Up Environment
```powershell
# Navigate to project directory
cd c:\Users\saikr\Documents\ProductPulse

# Set Gemini API Key (PowerShell example)
$env:GEMINI_API_KEY="your-gemini-api-key-here"
```

### 2. Run Automated Tests
Verify that all 22 unit, integration, and behavioral tests pass:
```powershell
python -m pytest backend/tests/ -v
```

### 3. Launch the Application Server
```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Open the Interface
Navigate to **`http://127.0.0.1:8000/`** in your browser.

---

## 13. 60-Second Hackathon Demo Script

* **[0:00 – 0:10] The Emerging Problem**:
  > *"Welcome to ProductPulse. Our deterministic detector monitors Week 3 customer feedback and immediately flags a critical anomaly: Android checkout payment failures surged by +1300%, with severe negative customer sentiment (-0.89)."*
* **[0:10 – 0:25] Hindsight Recalls Organizational Memory**:
  > *"When we select this problem, ProductPulse doesn't guess from scratch. It queries Hindsight's organizational memory bank and recalls Incident INC-104 from 4 months ago—recalling the exact failure signature, the past decision, the hotfix deployed, and the verified outcome."*
* **[0:25 – 0:40] AI Reasoning & Memory Contrast**:
  > *"Gemini synthesizes this evidence. Notice the dual contrast: Without memory, a team would waste 3–5 days triaging central databases. With Hindsight memory, Gemini pinpoints the GooglePay SDK token wrapper and recommends deploying the proven retry fallback."*
* **[0:40 – 0:50] Human Approval & Execution**:
  > *"ProductPulse enforces human governance. The Product Manager clicks 'Approve Action', advances the action to Execution, and launches telemetry monitoring."*
* **[0:50 – 1:00] Measurement & Closed-Loop Learning**:
  > *"Once Week 4 telemetry arrives, ProductPulse measures the impact: complaints dropped by -92.9%, sentiment rebounded by +1.62, and the outcome is classified as SUCCESS. We click 'Retain Lesson', and this operational runbook is permanently stored back into Hindsight for future incidents."*

> **Core Takeaway**: *"ProductPulse doesn't just analyze today's feedback. It remembers what the organization learned before and uses those lessons to make better product decisions over time."*

---

## 14. Example Scenarios: Divergence Testing

### Scenario A: Relevant Historical Memory Exists (Incident `INC-104`)
* **Problem**: Checkout payment timeouts surge on Android following an app update.
* **Hindsight Recall**: 6 memories recalled detailing how `INC-104` was resolved via client SDK token retry logic.
* **AI Decision**: Targeted investigation into GooglePay SDK wrapper; deploys retry fallback.
* **Impact**: Avoids 3–5 days of unfocused backend gateway troubleshooting.

### Scenario B: Novel Problem with No Relevant Memory
* **Problem**: iOS Push Notification delivery delays.
* **Hindsight Recall**: 0 matching memories found.
* **AI Decision**: Explicitly states no prior organizational memory exists; applies first-principles baseline diagnostics without hallucinating past incidents.

---

## 15. Limitations & Future Roadmap
* **Synthetic Data**: The current demonstration uses synthetic feedback datasets across 4 weeks with realistic app version and device segment distributions.
* **Bounded Actions**: Action execution in this hackathon version simulates operations runbooks (`CREATE_INVESTIGATION`, `CREATE_EXPERIMENT`, `CREATE_PRODUCT_CHANGE`).
* **Roadmap**:
  * Direct webhook ingestion from Zendesk, App Store Connect, and Google Play Console.
  * Real-time Slack/Teams notifications for Human-in-the-Loop approval requests.
  * Multi-bank clustering across different product lines.
