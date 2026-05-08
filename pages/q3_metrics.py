import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from src.loader import load_all_calls
from src.metrics import compute_all_metrics, compute_call_duration, compute_overtalk, compute_silence

st.set_page_config(page_title="Q3: Call Quality Metrics", page_icon="", layout="wide")

st.title("Q3: Call Quality Metrics")
st.markdown("Overtalk and silence analysis across all calls.")
st.markdown("---")

# Load all calls

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    st.error(f"Data directory '{DATA_DIR}' not found. Make sure your JSON files are in /data.")
    st.stop()

with st.spinner("Loading all calls..."):
    calls = load_all_calls(DATA_DIR)
    metrics = compute_all_metrics(calls)
    df = pd.DataFrame(metrics)

# Summary stats

st.subheader("Summary Statistics")


col0, col1, col2, col3, col4, col5, col6 = st.columns(7)
col0.metric("Total Calls", len(df))
col1.metric("Avg Overtalk %", f"{df['overtalk_pct'].mean():.2f}%")
col2.metric("Max Overtalk %", f"{df['overtalk_pct'].max():.2f}%")
col3.metric("Avg Silence %", f"{df['silence_pct'].mean():.2f}%")
col4.metric("Max Silence %", f"{df['silence_pct'].max():.2f}%")
col5.metric("High Overtalk Calls", f"{(df['overtalk_pct'] > 10).sum()}")
col6.metric("High Silence Calls", f"{(df['silence_pct'] > 5).sum()}")

st.markdown("---")

 # Tabs
 
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Distribution",
    "Per Call Bar Chart",
    "Scatter Plot",
    "Scorecard",
    "Call Timeline",
    "Raw Data Table"
])

 #Tab1: Distribution
 
with tab1:
    st.markdown("### Distribution of Overtalk & Silence Across Calls")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.histogram(
            df, x="overtalk_pct", nbins=30,
            title="Overtalk % Distribution",
            labels={"overtalk_pct": "Overtalk %"},
            color_discrete_sequence=["#EF553B"]
        )
        fig.update_layout(bargap=0.1)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.histogram(
            df, x="silence_pct", nbins=30,
            title="Silence % Distribution",
            labels={"silence_pct": "Silence %"},
            color_discrete_sequence=["#636EFA"]
        )
        fig.update_layout(bargap=0.1)
        st.plotly_chart(fig, use_container_width=True)

    # Box plots
    st.markdown("### Box Plot: Spread & Outliers")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.box(
            df, y="overtalk_pct",
            title="Overtalk %: Median, Quartiles & Outliers",
            labels={"overtalk_pct": "Overtalk %"},
            color_discrete_sequence=["#EF553B"]
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.box(
            df, y="silence_pct",
            title="Silence %: Median, Quartiles & Outliers",
            labels={"silence_pct": "Silence %"},
            color_discrete_sequence=["#636EFA"]
        )
        st.plotly_chart(fig, use_container_width=True)

 #Tab2: Per call bar chart
 
with tab2:
    st.markdown("### Top Calls by Overtalk & Silence")
    n = st.slider("Show top N calls", min_value=10, max_value=50, value=20)
    col1, col2 = st.columns(2)

    with col1:
        top_overtalk = df.nlargest(n, "overtalk_pct").copy()
        top_overtalk["short_id"] = top_overtalk["call_id"].str[:8] + "..."
        fig = px.bar(
    top_overtalk,
    x="short_id",
    y="overtalk_pct",
    title=f"Top {n} Calls: Highest Overtalk %",
    labels={"short_id": "Call ID", "overtalk_pct": "Overtalk %"},
    color_discrete_sequence=["#EF553B"]
) 
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        top_silence = df.nlargest(n, "silence_pct").copy()
        top_silence["short_id"] = top_silence["call_id"].str[:8] + "..."
        fig = px.bar(
    top_silence,
    x="short_id",
    y="silence_pct",
    title=f"Top {n} Calls: Highest Silence %",
    labels={"short_id": "Call ID", "silence_pct": "Silence %"},
    color_discrete_sequence=["#636EFA"]
)
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

 #Tab3: Scatter plot
 
with tab3:
    st.markdown("### Overtalk vs Silence per Call")
    st.caption("Each dot is one call. Ideal calls cluster near bottom-left (low overtalk, low silence).")

    df["short_id"] = df["call_id"].str[:8] + "..."
    fig = px.scatter(
        df,
        x="overtalk_pct", y="silence_pct",
        hover_name="short_id",
        hover_data={"duration_secs": True, "overtalk_secs": True, "silence_secs": True},
        title="Overtalk % vs Silence % per Call",
        labels={"overtalk_pct": "Overtalk %", "silence_pct": "Silence %"},
        color="overtalk_pct",
        color_continuous_scale="RdYlGn_r",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Duration vs Overtalk
    st.markdown("### Call Duration vs Overtalk %")
    st.caption("Do longer calls have more overtalk?")
    fig = px.scatter(
        df,
        x="duration_secs", y="overtalk_pct",
        hover_name="short_id",
        title="Call Duration vs Overtalk %",
        labels={"duration_secs": "Duration (s)", "overtalk_pct": "Overtalk %"},
        color="overtalk_pct",
        color_continuous_scale="Reds",
        trendline="ols"
    )
    st.plotly_chart(fig, use_container_width=True)

 #Tab4: Scorecard with flags
 
with tab4:
    st.markdown("### Call Quality Scorecard")
    st.caption("Flags calls based on overtalk and silence thresholds.")

    # Thresholds
    col1, col2 = st.columns(2)
    with col1:
        ot_threshold = st.slider("Overtalk threshold (high)", 5, 40, 20, key="ot_thresh")
    with col2:
        si_threshold = st.slider("Silence threshold (high)", 2, 15, 8, key="si_thresh")

    # Build scorecard df
    scorecard = df[["call_id", "duration_secs", "overtalk_pct", "silence_pct"]].copy()
    scorecard["short_id"] = scorecard["call_id"].str[:8]

    def overtalk_flag(pct):
        if pct >= ot_threshold: return "High"
        elif pct >= ot_threshold / 2: return "Medium"
        return "Low"

    def silence_flag(pct):
        if pct >= si_threshold: return "High"
        elif pct >= si_threshold / 2: return "Medium"
        return "Low"

    scorecard["Overtalk Flag"] = scorecard["overtalk_pct"].apply(overtalk_flag)
    scorecard["Silence Flag"]  = scorecard["silence_pct"].apply(silence_flag)

    # Summary counts
    col1, col2, col3 = st.columns(3)
    col1.metric("High Overtalk Calls", len(scorecard[scorecard["Overtalk Flag"] == "High"]))
    col2.metric("Medium Overtalk Calls", len(scorecard[scorecard["Overtalk Flag"] == "Medium"]))
    col3.metric("Low Overtalk Calls", len(scorecard[scorecard["Overtalk Flag"] == "Low"]))

    col1, col2, col3 = st.columns(3)
    col1.metric("High Silence Calls", len(scorecard[scorecard["Silence Flag"] == "High"]))
    col2.metric("Medium Silence Calls", len(scorecard[scorecard["Silence Flag"] == "Medium"]))
    col3.metric("Low Silence Calls", len(scorecard[scorecard["Silence Flag"] == "Low"]))

    st.markdown("---")

    # Filter options
    filter_ot = st.multiselect("Filter by Overtalk Flag", ["High", "Medium", "Low"], default=["High", "Medium"])
    filtered = scorecard[scorecard["Overtalk Flag"].isin(filter_ot)]

    st.dataframe(
        filtered[["short_id", "duration_secs", "overtalk_pct", "Overtalk Flag", "silence_pct", "Silence Flag"]]
        .sort_values("overtalk_pct", ascending=False)
        .reset_index(drop=True),
        use_container_width=True
    )

 #Tab5: Per-call timeline
 
with tab5:
    st.markdown("### Per-Call Timeline")
    st.caption("Select a call to visualize Agent speech, Customer speech, Overtalk, and Silence.")

    # Call selector
    call_ids = sorted(calls.keys())
    selected_id = st.selectbox(
        "Select a call",
        call_ids,
        format_func=lambda x: x[:8] + "..."
    )

    selected_call = calls[selected_id]
    selected_call_sorted = sorted(selected_call, key=lambda u: u['stime'])

    duration = compute_call_duration(selected_call)
    ot_secs, ot_pct = compute_overtalk(selected_call)
    si_secs, si_pct = compute_silence(selected_call)

    # Show metrics for selected call
    col1, col2, col3 = st.columns(3)
    col1.metric("Duration", f"{duration:.1f}s")
    col2.metric("Overtalk", f"{ot_pct:.1f}%  ({ot_secs}s)")
    col3.metric("Silence",  f"{si_pct:.1f}%  ({si_secs}s)")

    # Build timeline figure
    fig = go.Figure()

    # Agent utterances— row y=2
    for u in selected_call_sorted:
        if u['speaker'] == 'Agent':
            fig.add_trace(go.Bar(
                x=[u['etime'] - u['stime']],
                y=["Agent"],
                base=u['stime'],
                orientation='h',
                marker_color='#4C9BE8',
                name='Agent',
                showlegend=False,
                hovertemplate=f"Agent<br>{u['stime']}s → {u['etime']}s<br>{u['text'][:60]}<extra></extra>"
            ))

    # Customer utterances- row y=1
    for u in selected_call_sorted:
        if u['speaker'] == 'Customer':
            fig.add_trace(go.Bar(
                x=[u['etime'] - u['stime']],
                y=["Customer"],
                base=u['stime'],
                orientation='h',
                marker_color='#F4A34C',
                name='Customer',
                showlegend=False,
                hovertemplate=f"Customer<br>{u['stime']}s → {u['etime']}s<br>{u['text'][:60]}<extra></extra>"
            ))

    # Overtalk- row y=0 (Overlap)
    agent_segs = [(u['stime'], u['etime']) for u in selected_call_sorted if u['speaker'] == 'Agent']
    cust_segs  = [(u['stime'], u['etime']) for u in selected_call_sorted if u['speaker'] == 'Customer']

    for a in agent_segs:
        for b in cust_segs:
            s = max(a[0], b[0])
            e = min(a[1], b[1])
            if e - s > 0:
                fig.add_trace(go.Bar(
                    x=[e - s],
                    y=["Overtalk"],
                    base=s,
                    orientation='h',
                    marker_color='#EF553B',
                    name='Overtalk',
                    showlegend=False,
                    hovertemplate=f"Overtalk<br>{s:.1f}s → {e:.1f}s<br>Duration: {e-s:.1f}s<extra></extra>"
                ))

    # Silence gaps- row y=3 (Silence)
    all_sorted_ivs = sorted([(u['stime'], u['etime']) for u in selected_call_sorted])
    for i in range(len(all_sorted_ivs) - 1):
        gap_start = all_sorted_ivs[i][1]
        gap_end   = all_sorted_ivs[i + 1][0]
        if gap_end - gap_start > 0:
            fig.add_trace(go.Bar(
                x=[gap_end - gap_start],
                y=["Silence"],
                base=gap_start,
                orientation='h',
                marker_color='#888888',
                name='Silence',
                showlegend=False,
                hovertemplate=f"Silence<br>{gap_start:.1f}s → {gap_end:.1f}s<br>Duration: {gap_end-gap_start:.1f}s<extra></extra>"
            ))

    # Legend traces (dummy, for display only)
    for label, color in [("Agent", "#4C9BE8"), ("Customer", "#F4A34C"),
                          ("Overtalk", "#EF553B"), ("Silence", "#888888")]:
        fig.add_trace(go.Bar(
            x=[0], y=["Agent"], base=0,
            orientation='h',
            marker_color=color,
            name=label,
            showlegend=True
        ))

    fig.update_layout(
        barmode='overlay',
        title=f"Call Timeline — {selected_id[:8]}...",
        xaxis_title="Time (seconds)",
        yaxis=dict(categoryorder='array', categoryarray=["Silence", "Overtalk", "Customer", "Agent"]),
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Transcript below timeline
    with st.expander("View Transcript for this call"):
        for u in selected_call_sorted:
            time = f"{u['stime']}s — {u['etime']}s"
            if u['speaker'] == 'Agent':
                st.markdown(f"**Agent** `{time}`  \n{u['text']}")
            else:
                st.markdown(f"**Customer** `{time}`  \n{u['text']}")
            st.markdown("")

 #Tab6: Raw data table
 
with tab6:
    st.markdown("### Full Metrics Table")
    display_df = df[["call_id", "duration_secs", "overtalk_secs", "overtalk_pct", "silence_secs", "silence_pct"]].copy()
    display_df["call_id"] = display_df["call_id"].str[:8]
    st.dataframe(
        display_df.sort_values("overtalk_pct", ascending=False).reset_index(drop=True),
        use_container_width=True
    )