import streamlit as st
import pandas as pd

pd.set_option("styler.render.max_elements", 500000)

def render_view(df_filtered):

    st.markdown(
        '<span style="font-size: 1.1rem; font-weight: 400;">Raw data is displayed below for manual validation of labels and other data</span>',
        unsafe_allow_html=True
    )
    st.divider()
    st.subheader("Manual Inspection of Raw Data")
    st.info(
        "This table is intended for manual inspection and validation. "
        "It shows the exact rows behind the dashboards, including labels, evidence, outcomes, "
        "and customer behaviours like repeat calls and churn."
    )

    # --- filter inputs ---
    raw_columns = [
        "label",
        "long_reason",
        "evidence",
        "confidence",
        "selected_outcome_cleaned",
        "outcome_cost",
        "outcome_ts",
        "sc_call_next_7d_flag",
        "bb_churn_next_30d",
    ]
    raw_columns = [c for c in raw_columns if c in df_filtered.columns]

    col1, col2, col3 = st.columns(3)

    with col1:
        search_term = st.text_input("Text search across all columns:", value="", key="raw_search")
        if search_term:
            mask = df_filtered.astype(str).apply(lambda row: row.str.contains(search_term, case=False).any(), axis=1)
            df_filtered = df_filtered[mask]

    with col2:
        if "sc_call_next_7d_flag" in df_filtered.columns:
            repeat_filter = st.selectbox("Repeat call in next 7 days?:", ["All", "Yes", "No"], key="raw_repeat")
            if repeat_filter == "Yes":
                df_filtered = df_filtered[df_filtered["sc_call_next_7d_flag"] == 1]
            elif repeat_filter == "No":
                df_filtered = df_filtered[df_filtered["sc_call_next_7d_flag"] == 0]

    with col3:
        if "bb_churn_next_30d" in df_filtered.columns:
            churn_filter = st.selectbox("Churn within 30 days?:", ["All", "Yes", "No"], key="raw_churn")
            if churn_filter == "Yes":
                df_filtered = df_filtered[df_filtered["bb_churn_next_30d"] == 1]
            elif churn_filter == "No":
                df_filtered = df_filtered[df_filtered["bb_churn_next_30d"] == 0]

    # --- prepare dataframe for display ---
    df_display = df_filtered[raw_columns].copy()

    if "confidence" in df_display.columns:
        df_display["confidence"] = df_display["confidence"].fillna(0).astype(int)

    # rename for display only
    df_display = df_display.rename(columns={
        "label": "Label",
        "long_reason": "Reason",
        "evidence": "Evidence",
        "confidence": "Confidence",
        "selected_outcome_cleaned": "Outcome",
        "outcome_cost": "Outcome Cost (£)",
        "sc_call_next_7d_flag": "Repeat Call (7d)",
        "bb_churn_next_30d": "Churn (30d)",
        "outcome_ts": "Outcome Timestamp"
    })

    display_columns = [
        "Label", "Outcome", "Reason", "Evidence", "Confidence",
        "Outcome Cost (£)", "Repeat Call (7d)", "Churn (30d)",
        "Outcome Timestamp"
    ]

    # --- sort numeric column like the outcomes table ---
    df_display_sorted = df_display.sort_values(
        ["Label", "Outcome Cost (£)"], ascending=[False, True]
    ).reset_index(drop=True)

    # --- define display formatting ---
    display_format = {
        "Outcome Cost (£)": "£{:,.0f}",
        "Repeat Call (7d)": lambda v: "Yes" if v == 1 else "No",
        "Churn (30d)": lambda v: "Yes" if v == 1 else "No"
    }

    # --- render with numeric sorting preserved ---
    st.dataframe(
        df_display_sorted[display_columns].style.format(display_format),
        use_container_width=True,
        column_config={
            "Label": st.column_config.TextColumn(),
            "Outcome": st.column_config.TextColumn(),
            "Reason": st.column_config.TextColumn(),
            "Evidence": st.column_config.TextColumn(),
            "Confidence": st.column_config.NumberColumn(),
            "Outcome Cost (£)": st.column_config.NumberColumn(),
            "Repeat Call (7d)": st.column_config.TextColumn(),
            "Churn (30d)": st.column_config.TextColumn(),
            "Outcome Timestamp": st.column_config.TextColumn(),
        }
    )

    st.caption(f"{len(df_filtered):,} calls remaining after filters applied")
    st.divider()
