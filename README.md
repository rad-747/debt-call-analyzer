# Debt Collection Call Analyzer

A Streamlit based dashboard for analyzing debt collection call transcripts using Regex and LLM based techniques.

The project focuses on:
- Profanity detection
- Compliance violation detection
- Call quality metrics analysis

---

## Features

### Q1: Profanity Detection
- Detects abusive or profane language
- Supports Regex based detection
- Supports LLM based contextual moderation using Groq API

### Q2: Compliance Violation Detection
- Detects sensitive information shared before identity verification
- Identifies potential compliance risks in calls

### Q3: Call Quality Metrics
- Measures overtalk percentage
- Measures silence percentage
- Interactive visualizations and analytics dashboard

---

## Technologies Used

- Python
- Streamlit
- Pandas
- Plotly
- Groq API
- Llama 3.3 70B
- Regex
- JSON transcript processing

---

## Live Demo

[Open Streamlit App](https://debt-call-analyzer-kjws4hsuvz5qtvn2kk9qta.streamlit.app)

---

## How to Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/rad-747/debt-call-analyzer.git
cd debt-call-analyzer
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add environment variables

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_api_key_here
```

### 5. Run the Streamlit app

```bash
streamlit run app.py
```

---

## Project Structure

```text
debt_call_analyzer_vs/

├── app.py
├── requirements.txt
├── README.md
├── .gitignore

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
```

---

## Dataset

The application processes JSON based debt collection call transcripts containing:
- Speaker labels
- Timestamps
- Utterances
- Call metadata

---

## Author

Radhika Panchal
