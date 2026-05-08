# Debt Call Analyzer

A Streamlit application for analyzing debt collection call transcripts using Regex and LLM-based detection techniques.

The system helps identify:
- Profanity and abusive language
- Dismissive or unprofessional communication
- Compliance violations
- Identity verification issues
- Customer vs Agent behavior patterns

## Features

### Profanity Detection
Detects:
- Profanity
- Abusive language
- Dismissive language
- Unprofessional phrases

Supports:
- Regex-based detection
- LLM-based contextual analysis using Groq

### Compliance Analysis
Checks whether agents disclose sensitive customer information before proper identity verification.

The app validates:
- Identity verification flow
- Sequence of verification vs disclosure
- Sensitive information exposure
- Compliance-safe responses

### Metrics Dashboard
Displays:
- Agent vs customer metrics
- Call-level summaries
- Detection insights
- Flagged utterances

## Tech Stack

- Python
- Streamlit
- Groq API
- Llama 3.3 70B
- Regex
- JSON transcript processing

## Project Structure

```text
debt_call_analyzer_vs/

├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env

├── pages/
│   ├── q1_profanity.py
│   ├── q2_compliance.py
│   └── q3_metrics.py

├── src/
│   ├── profanity_detector.py
│   ├── compliance_detector.py
│   ├── loader.py
│   └── metrics.py

└── data/