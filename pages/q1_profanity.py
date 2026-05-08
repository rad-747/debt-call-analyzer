import streamlit as st
import json
import os
from src.profanity_detector import detect_profanity_regex, detect_profanity_llm

st.set_page_config(page_title="Q1: Profanity Detection", layout="wide")

st.title("Q1: Profanity Detection")
st.markdown("Detect profane or abusive language used by the Agent or Customer.")
st.markdown("---")

# Sidebar controls

st.sidebar.header("Settings")

approach = st.sidebar.selectbox(
    "Select Approach",
    ["Regex (Pattern Matching)", "LLM (Groq)"]
)

entity = st.sidebar.selectbox(
    "Select Entity to Analyze",
    ["Both Agent & Customer", "Agent Only", "Customer Only"]
)

uploaded_file = st.sidebar.file_uploader("Upload a call JSON file", type=["json"])

# Main panel

if uploaded_file is None:
    st.info("Upload a call JSON file from the sidebar to begin :)")
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
        result = detect_profanity_regex(call_data)

    else:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            st.warning("GROQ_API_KEY not set. Falling back to Regex.")
            result = detect_profanity_regex(call_data)
        else:
            try:
                result = detect_profanity_llm(call_data, api_key)
                if result is None:
                    raise Exception("LLM returned no result")
            except Exception as e:
                st.error(f"LLM failed: {str(e)}")
                st.warning("Falling back to Regex detection...")
                result = detect_profanity_regex(call_data)

# Display results

st.markdown("---")
st.subheader("Result")

col1, col2 = st.columns(2)

# Agent result
if entity in ["Both Agent & Customer", "Agent Only"]:
    with col1:
        st.markdown("#### Agent")
        agent_flag = result.get("agent_profanity_detected", False)
        if agent_flag:
            st.error("Profanity DETECTED")
        else:
            st.success("No Profanity Detected")

        flagged = result.get("agent_flagged_utterances") or result.get("agent_flagged_lines") or []
        if flagged:
            st.markdown("**Flagged lines:**")
            for line in flagged:
                if isinstance(line, dict):
                    st.warning(f"\"{line.get('text', line)}\"")
                    if line.get('matched_patterns'):
                        for match in line['matched_patterns']:
                            st.caption(f"Matched word: `{match['word']}` | Pattern: `{match['pattern']}`")
                    elif line.get('reason'):
                        category = line.get("category", "profanity")
                        st.caption(f"Category: `{category}` | Reason: {line['reason']}")
                else:
                    st.warning(f"\"{line}\"")

# Customer result
if entity in ["Both Agent & Customer", "Customer Only"]:
    with col2:
        st.markdown("#### Customer")
        customer_flag = result.get("customer_profanity_detected", False)
        if customer_flag:
            st.error("Profanity / Abusive Language DETECTED")
        else:
            st.success("No Profanity Detected")

        flagged = result.get("customer_flagged_utterances") or result.get("customer_flagged_lines") or []
        if flagged:
            st.markdown("**Flagged lines:**")
            for line in flagged:
                if isinstance(line, dict):
                    st.warning(f"\"{line.get('text', line)}\"")
                    if line.get('matched_patterns'):
                        for match in line['matched_patterns']:
                            st.caption(f"Matched word: `{match['word']}` | Pattern: `{match['pattern']}`")
                    elif line.get('reason'):
                        category = line.get("category", "profanity")
                        st.caption(f"Category: `{category}` | Reason: {line['reason']}")
                else:
                    st.warning(f"\"{line}\"")
# LLM reasoning
if "LLM" in approach and result.get("reasoning"):
    st.markdown("---")
    st.markdown("#### LLM Reasoning")
    st.markdown(result["reasoning"])

# Show full transcript

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