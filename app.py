from dotenv import load_dotenv
load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="Debt Call Analyzer",
    layout="wide"
)

st.title("Debt Collection Call Analyzer")
st.markdown("---")

st.markdown("""
### What this tool does

Upload any call transcript (JSON file) and analyze it for:

| Question | What we detect |
|---|---|
| **Q1: Profanity Detection** | Profane or abusive language by agent or customer |
| **Q2: Compliance Violation** | Sensitive info shared before identity verification |
| **Q3: Call Quality Metrics** | Overtalk and silence percentages across all calls |

---

### How to use it

Use the **sidebar** to navigate between the three analysis pages.

Each page lets you:
- Upload a single call file
- Choose your detection approach (Regex or LLM)
- See the result instantly

---
""")

st.info("👈 Select a page from the sidebar to get started.")