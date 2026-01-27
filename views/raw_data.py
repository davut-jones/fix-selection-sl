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


    # ---- text search for long_reason and evidence ----
    st.markdown("### Search text (long_reason + evidence)")

    search_text = st.text_input(
        "Search (case-insensitive)",
        value="",
        key="raw_search_text"
    )

    if search_text:
        df_filtered = df_filtered[
            df_filtered["long_reason"].astype(str).str.contains(search_text, case=False, na=False) |
            df_filtered["evidence"].astype(str).str.contains(search_text, case=False, na=False)
        ]


    # ---- dropdown filters for categorical columns ----
    st.markdown("### Categorical filters")

    categorical_cols = [
        "label",
        "selected_outcome_cleaned",
        "call_date"
    ]

    for col in categorical_cols:
        if col in df_filtered.columns:
            unique_vals = sorted(df_filtered[col].dropna().unique())
            selected = st.multiselect(
                f"Filter {col}",
                options=unique_vals,
                default=unique_vals,
                key=f"raw_cat_{col}"
            )
            df_filtered = df_filtered[df_filtered[col].isin(selected)]


    # ---- range filters for numeric columns ----
    st.markdown("### Numeric filters")

    numeric_cols = [
        "outcome_cost",
        "sc_call_next_7d_flag",
        "sc_call_next_7d_days",
        "bb_churn_next_30d",
        "bb_churn_next_60d"
    ]

    for col in numeric_cols:
        if col in df_filtered.columns:
            min_val = float(df_filtered[col].min())
            max_val = float(df_filtered[col].max())

            range_min, range_max = st.slider(
                f"{col} range",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                key=f"raw_num_{col}"
            )

            df_filtered = df_filtered[
                (df_filtered[col] >= range_min) &
                (df_filtered[col] <= range_max)
            ]


    # ---- tag search using streamlit-tags ----
    st.markdown("### Tag filter (multiple values)")

    tags = st_tags(
        label="Filter by tags (e.g. label names or outcomes)",
        text="Add tags...",
        value=[],
        suggestions=list(df_filtered["label"].dropna().unique()),
        key="raw_tags"
    )

    if tags:
        df_filtered = df_filtered[
            df_filtered["label"].isin(tags) |
            df_filtered["selected_outcome_cleaned"].isin(tags)
        ]


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
    st.dataframe(df_filtered[raw_columns], use_container_width=True)

    # caption for remaining calls
    st.caption(f"{len(df_filtered):,} calls remaining after filters applied")

    st.divider()
