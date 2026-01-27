import streamlit as st
from streamlit_tags import st_tags
import pandas as pd

def render_view(df_filtered):

    # page text
    st.write("\n\n")
    st.markdown(
        '<span style="font-size: 1.1rem; font-weight: 400;">Raw data is displayed below for manual validation and debugging.</span>',
        unsafe_allow_html=True
    )
    st.divider()

    #####################################
    ### section 1 - raw data (QA) ###
    #####################################

    st.subheader("Raw Data (for validation only)")

    st.info(
        "This section is for manual inspection and validation only. "
        "It shows the exact rows behind the dashboards (labels, evidence, outcomes, repeat calls, churn, and filters). "
        "Use this to spot-check edge cases, verify label quality, and debug any anomalies."
    )

    # ---- combined filters ----
    st.markdown("### Filters")

    # ---- streamlit-tags multi-search ----
    tag_suggestions = sorted(
        list(df_filtered["label"].dropna().unique()) +
        list(df_filtered["selected_outcome_cleaned"].dropna().unique())
    )

    tags = st_tags(
        label="Search by label or outcome (add multiple tags)",
        text="Add tags...",
        value=[],
        suggestions=tag_suggestions,
        key="raw_tags"
    )

    if tags:
        df_filtered = df_filtered[
            df_filtered["label"].isin(tags) |
            df_filtered["selected_outcome_cleaned"].isin(tags)
        ]

    # ---- Yes/No dropdown for repeat calls ----
    if "sc_call_next_7d_flag" in df_filtered.columns:
        repeat_filter = st.selectbox(
            "Repeat call in next 7 days?",
            options=["All", "Yes", "No"],
            key="raw_repeat"
        )

        if repeat_filter == "Yes":
            df_filtered = df_filtered[df_filtered["sc_call_next_7d_flag"] == 1]
        elif repeat_filter == "No":
            df_filtered = df_filtered[df_filtered["sc_call_next_7d_flag"] == 0]

    # ---- Yes/No dropdown for churn ----
    if "bb_churn_next_30d" in df_filtered.columns:
        churn_filter = st.selectbox(
            "Churn within 30 days?",
            options=["All", "Yes", "No"],
            key="raw_churn"
        )

        if churn_filter == "Yes":
            df_filtered = df_filtered[df_filtered["bb_churn_next_30d"] == 1]
        elif churn_filter == "No":
            df_filtered = df_filtered[df_filtered["bb_churn_next_30d"] == 0]

    # key columns used across the dashboard
    raw_columns = [
        "label",
        "long_reason",
        "evidence",
        "confidence",
        "selected_outcome_cleaned",
        "outcome_cost",
        "outcome_ts",
        "sc_call_next_7d_flag",
        "sc_call_next_7d_days",
        "bb_churn_next_30d",
        "bb_churn_next_60d",
        "call_date"
    ]

    raw_columns = [c for c in raw_columns if c in df_filtered.columns]

    # show raw data table
    st.dataframe(df_filtered[raw_columns], width=True)

    # caption for remaining calls
    st.caption(f"{len(df_filtered):,} calls remaining after filters applied")

    st.divider()
