import streamlit as st
import pandas as pd

def render_view(df_filtered):

    # page text
    st.write("\n\n")
    st.markdown(
        '<span style="font-size: 1.1rem; font-weight: 400;">Raw data is displayed below for manual validation of labels and other data</span>',
        unsafe_allow_html=True
    )
    st.divider()

    ############################
    ### section 1 - raw data ###
    ############################

    st.subheader("Manual Inspection of Raw Data")

    st.write("\n\n")
    st.info(
        "This table is intended for manual inspection and validation. "
        "It shows the exact rows behind the dashboards, including labels, evidence, outcomes, "
        "and customer behaviours like repeat calls and churn."
    )
    st.write("\n\n")

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

    # create 3 columns for filters side by side
    col1, col2, col3 = st.columns(3)

    # search across all columns
    with col1:
        search_term = st.text_input(
            "Text search across all columns (click cells to read full text):",
            value="",
            key="raw_search"
        )
        
        if search_term:
            # search across all columns in the dataframe
            mask = df_filtered.astype(str).apply(lambda row: row.str.contains(search_term, case=False).any(), axis=1)
            df_filtered = df_filtered[mask]

    # yes / no dropdown for repeat calls ----
    with col2:
        if "sc_call_next_7d_flag" in df_filtered.columns:
            repeat_filter = st.selectbox(
                "Repeat call in next 7 days?:",
                options=["All", "Yes", "No"],
                key="raw_repeat"
            )

            if repeat_filter == "Yes":
                df_filtered = df_filtered[df_filtered["sc_call_next_7d_flag"] == 1]
            elif repeat_filter == "No":
                df_filtered = df_filtered[df_filtered["sc_call_next_7d_flag"] == 0]

    # yes / no dropdown for churn ----
    with col3:
        if "bb_churn_next_30d" in df_filtered.columns:
            churn_filter = st.selectbox(
                "Churn within 30 days?:",
                options=["All", "Yes", "No"],
                key="raw_churn"
            )

            if churn_filter == "Yes":
                df_filtered = df_filtered[df_filtered["bb_churn_next_30d"] == 1]
            elif churn_filter == "No":
                df_filtered = df_filtered[df_filtered["bb_churn_next_30d"] == 0]

    st.write("\n\n")

    # prepare dataframe for display
    df_display = df_filtered[raw_columns].reset_index(drop=True)

    # rename columns to human-readable names
    df_display = df_display.rename(columns={
        "label": "Label",
        "long_reason": "Reason",
        "evidence": "Evidence",
        "confidence": "Confidence",
        "selected_outcome_cleaned": "Outcome",
        "outcome_cost": "Outcome Cost (£)",
        "outcome_ts": "Outcome Timestamp",
        "sc_call_next_7d_flag": "Repeat Call (7d)",
        "sc_call_next_7d_days": "Days to Repeat",
        "bb_churn_next_30d": "Churn (30d)",
        "bb_churn_next_60d": "Churn (60d)",
        "call_date": "Call Date"
    })

    # show raw data table with column configuration for readability
    st.dataframe(
        df_display,
        width='stretch',
        column_config={
            "Reason": st.column_config.TextColumn(width="large"),
            "Evidence": st.column_config.TextColumn(width="large"),
        }
    )

    # caption for remaining calls
    st.caption(f"{len(df_filtered):,} calls remaining after filters applied")

    st.divider()