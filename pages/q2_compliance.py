import streamlit as st
import json
import os
from src.compliance_detector import detect_compliance_regex, detect_compliance_llm

st.set_page_config(page_title="Q2: Compliance Violation", layout="wide")

st.title("Q2: Privacy & Compliance Violation")
st.markdown("Detect if the agent shared sensitive information before verifying customer identity.")
st.markdown("---")

# Sidebar controls

st.sidebar.header("Settings")

approach = st.sidebar.selectbox(
    "Select Approach",
    ["Regex (Pattern Matching)", "LLM (Groq)"]
)

st.sidebar.selectbox(
    "Select Entity",
    ["Privacy & Compliance Violation"]
)

uploaded_file = st.sidebar.file_uploader("Upload a call JSON file", type=["json"])

# Main panel

if uploaded_file is None:
    st.info("Upload a call JSON file from the sidebar to begin.")
    st.stop()

try:
    call_data = json.load(uploaded_file)
except Exception as e:
    st.error(f"Failed to read file: {e}")
    st.stop()

if not call_data:
    st.error("Uploaded file is empty.")
    st.stop()

st.subheader(f"File: `{uploaded_file.name}`")
st.caption(f"{len(call_data)} utterances loaded")

# Run detection

with st.spinner("Analyzing..."):
    if "Regex" in approach:
        result = detect_compliance_regex(call_data)
    else:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            st.warning("GROQ_API_KEY not set. Falling back to Regex.")
            result = detect_compliance_regex(call_data)
        else:
            try:
                result = detect_compliance_llm(call_data, api_key)
                if result is None:
                    raise Exception("LLM returned no result")
            except Exception as e:
                st.error(f"LLM failed: {str(e)}")
                st.warning("Falling back to Regex detection...")
                result = detect_compliance_regex(call_data)

# Display results

st.markdown("---")
st.subheader("Result")


if result["violation_detected"]:
    st.error("COMPLIANCE VIOLATION DETECTED: Sensitive info shared before identity verification")
else:
    st.success("No Compliance Violation Detected")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Sensitive Info Disclosed (Before Verification)")
    violations = result.get("violations") or result.get("violation_lines") or []
    if violations:
        for v in violations:
            if isinstance(v, dict):
                st.error(f"\"{v.get('text', v)}\"")
                if 'stime' in v:
                    st.caption(f"At {v['stime']}s | Matched: {', '.join(v['matched'])}")
                elif 'reason' in v:
                    st.caption(f"Reason: {v['reason']}")
            else:
                st.error(f"\"{v}\"")
    else:
        st.info("No sensitive disclosures found before verification.")

with col2:
    st.markdown("#### Identity Verification Lines")
    verifications = result.get("verification_utterances") or result.get("verification_lines") or []
    if verifications:
        for v in verifications:
            if isinstance(v, dict):
                st.success(f"\"{v.get('text', v)}\"")
                if 'stime' in v:
                    st.caption(f"At {v['stime']}s | Matched: {', '.join(v['matched'])}")
            else:
                st.success(f"\"{v}\"")
    else:
        st.warning("No identity verification detected in this call.")

# LLM reasoning
if "LLM" in approach and result.get("reasoning"):
    st.markdown("---")
    st.markdown("#### LLM Reasoning")
    st.info(result["reasoning"])

# Full transcript

st.markdown("---")
with st.expander("View Full Transcript"):
    for utt in call_data:
        speaker = utt['speaker']
        text = utt['text']
        time = f"{utt['stime']}s — {utt['etime']}s"
        if speaker == "Agent":
            st.markdown(f"**Agent** `{time}`  \n{text}")
        else:
            st.markdown(f"**Customer** `{time}`  \n{text}")
        st.markdown("")