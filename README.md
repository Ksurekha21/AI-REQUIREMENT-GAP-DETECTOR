# AI Requirement Gap Detector

> Identify potential gaps, missing details, and unhandled edge cases in software requirements before development begins.

---

## 1. Problem Statement

In software engineering, ambiguous, incomplete, or underspecified requirements are one of the leading causes of project delays, scope creep, costly refactoring, and production failures. Stakeholders often write high-level user stories such as:
> *"Users should be able to order food through the application."*

While simple on the surface, this requirement omits critical operational flows:
- What happens if the restaurant is closed?
- What happens if selected items go out of stock during checkout?
- What happens if payment fails or times out?
- What are the cancellation and refund rules?

Traditional static analysis, regex, and keyword-based AI simulations fail to catch these issues because they lack contextual reasoning about software workflows and domain dynamics.

---

## 2. Project Objective

The **AI Requirement Gap Detector** provides software engineering teams, product managers, and business analysts with an automated review assistant. It leverages a real **Generative AI model** to reason about natural-language software requirements and organize findings into nine sections before a single line of code is written.

---

## 3. How the System Works

```
+-----------------------------------------------------------+
|                      Streamlit UI                         |
|   (User enters natural language software requirement)     |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                  Input Validation Layer                   |
|        (Guards against empty/whitespace input)            |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                     AI Analyzer                           |
|  - Injects System Prompt (prompts.py)                     |
|  - Enforces JSON Schema (RESPONSE_SCHEMA)                 |
|  - Calls Google GenAI (gemini-3.5-flash / fallback)       |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                Response Validation (Pydantic)             |
|  - Strips markdown fences                                 |
|  - Validates JSON format & required keys                  |
|  - Sanitizes array items to clean strings                 |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                   Formatted UI Display                    |
|   🔴 HIGH PRIORITY GAPS                                   |
|   🟡 MEDIUM PRIORITY GAPS                                 |
|   🟢 LOW PRIORITY GAPS                                    |
|   ⚠️ MISSING DETAILS                                      |
|   🔍 AMBIGUITY DETECTION                                  |
|   🧪 EDGE-CASE DETECTION                                  |
|   ❓ CLARIFICATION QUESTIONS                              |
|   ✨ IMPROVED REQUIREMENT                                 |
|   💡 RECOMMENDATIONS                                      |
+-----------------------------------------------------------+
```

1. **Input Submission**: The user enters a software requirement into the Streamlit interface.
2. **Client-Side Guardrails**: Input is checked for presence and whitespace. Empty inputs halt execution with a friendly alert without calling the API.
3. **Generative AI Reasoning**: The requirement is paired with a specialized system prompt and dispatched to Google GenAI with strict JSON schema enforcement (`types.GenerateContentConfig`).
4. **Resilient Failover**: If high traffic triggers a 503 spike, the analyzer automatically retries against an optimized fallback model (`gemini-3.5-flash-lite`).
5. **Pydantic Validation**: The raw JSON payload is parsed and verified by `response_validator.py`, which validates the nine response fields and sanitizes list items.
6. **Polished Display**: Results are presented in nine distinct, ordered sections, with ambiguities and clarification questions rendered in a structured format.

---

## 4. Key Features

- **Real Generative AI Analysis**: Uses genuine LLM reasoning rather than hardcoded heuristics, keyword matching, or NLP parsing trees.
- **Nine-Section Analysis**:
  - 🔴 **HIGH PRIORITY GAPS**: Core transaction failures, unavailable dependencies, or blocker states.
  - 🟡 **MEDIUM PRIORITY GAPS**: Important edge cases (cancellation, modification, timeout handling).
  - 🟢 **LOW PRIORITY GAPS**: Convenience features (re-ordering, history, notification preferences).
  - ⚠️ **MISSING DETAILS**: Explicit parameters missing from the description (payment methods, fee structures, file limits).
  - 🔍 **AMBIGUITY DETECTION**: Vague terms with explanations and suggested clarifications.
  - 🧪 **EDGE-CASE DETECTION**: Exceptional or boundary conditions to consider.
  - ❓ **CLARIFICATION QUESTIONS**: Numbered questions to resolve uncertainty.
  - ✨ **IMPROVED REQUIREMENT**: An AI-suggested, more specific version of the requirement.
  - 💡 **RECOMMENDATIONS**: Actionable next steps to specify the requirement prior to development.
- **Light, Responsive Interface**: A centered Streamlit layout with a light background, readable input, and separate pastel-accented result cards.
- **Input Guardrail**: Submitting a blank requirement displays a centered warning and does not start analysis.
- **Deterministic Structured JSON**: Direct schema enforcement at the API level guarantees reliable parsing.
- **Defensive Error Handling**: Typed exception handling for missing keys, invalid credentials, rate limits, and network errors.

---

## 5. Technology Stack

- **Language**: Python 3.10+
- **Frontend / UI**: [Streamlit](https://streamlit.io/) with small, inline CSS enhancements
- **Generative AI API**: Official Google GenAI SDK (`google-genai`) with Gemini models
- **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **Configuration**: [python-dotenv](https://pypi.org/project/python-dotenv/)
- **Data Exchange**: JSON

*(No separate JavaScript frontend, heavy ML framework, or database is required.)*

---

## 6. Project Structure

```
AI-Requirement-Gap-Detector/
│
├── app.py                  # Streamlit interface, user controls & results display
├── ai_analyzer.py          # AI API communication, fallback handling & model execution
├── prompts.py              # System prompt and structured JSON schema definition
├── response_validator.py   # Pydantic schema validation & response sanitization
├── requirements.txt        # Project dependencies
├── .env                    # Local API credentials (git-ignored)
├── .env.example            # Environment template
├── .gitignore              # Version control ignore rules
└── README.md               # Project documentation & interview guide
```

---

## 7. Installation & Environment Setup

### 1. Clone or Open the Repository
```powershell
cd "c:\Users\surek\AI REQUIREMENT GAP DETECTOR"
```

### 2. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the root directory (refer to `.env.example`):
```env
AI_API_KEY=your_actual_gemini_api_key_here
```
*(The system supports both `AI_API_KEY` and `GEMINI_API_KEY` environment variables).*

---

## 8. How to Run

Launch the Streamlit web application:
```powershell
python -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 9. AI Integration Explanation

- **Contextual Reasoning**: The model assesses requirements through a software architecture perspective rather than searching for hardcoded keywords.
- **JSON Schema Enforcement**: Using `google.genai.types.GenerateContentConfig(response_mime_type="application/json", response_schema=RESPONSE_SCHEMA)`, the LLM is constrained to output JSON matching the application's nine-field response structure.
- **Temperature Tuning**: Set to `temperature=0.2` to minimize hallucinations and maximize rigorous, analytical consistency.

---

## 10. Limitations

1. **Single-Sentence Ambiguity**: Very brief requirements lack domain constraints (e.g., B2B vs B2C), requiring broader gap suggestions.
2. **API Quota Constraints**: Relies on third-party API availability, though mitigated by automatic fallback to fast lite models.
3. **No Project Repository Access**: Analyzes individual requirements in isolation rather than cross-referencing an entire existing codebase or Jira backlog.

---

## 11. Future Enhancements

- **Jira / GitHub Issues Integration**: Directly import requirements from issue trackers.
- **Export Reports**: Download gap analysis as PDF or Markdown for sprint planning.
- **Domain Profiles**: Allow users to toggle regulatory presets (e.g., HIPAA for healthcare, PCI-DSS for fintech).

---
