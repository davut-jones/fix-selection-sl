import streamlit as st
import pandas as pd
import altair as alt

def render_view(df_filtered):

    # page text
    st.write("\n\n")
    st.markdown(
        '<span style="font-size: 1.1rem; font-weight: 400;">High-level summaries of call issues, outcomes, and key metrics to understand the landscape</span>',
        unsafe_allow_html=True
    )
    st.divider()

    ###############################
    ### section 1 - kpi summary ###
    ###############################

    # ensure numeric types for calculations
    df_filtered["outcome_cost"] = pd.to_numeric(df_filtered["outcome_cost"], errors="coerce")
    df_filtered["sc_call_next_7d_flag"] = pd.to_numeric(df_filtered["sc_call_next_7d_flag"], errors="coerce")
    df_filtered["bb_churn_next_30d"] = pd.to_numeric(df_filtered["bb_churn_next_30d"], errors="coerce")
    df_filtered["bb_churn_next_60d"] = pd.to_numeric(df_filtered["bb_churn_next_60d"], errors="coerce")

    # kpi summary
    total_filtered_calls = len(df_filtered)

    repeat_calls = df_filtered["sc_call_next_7d_flag"].sum()
    repeat_rate = (repeat_calls / total_filtered_calls) if total_filtered_calls else 0

    churn_30 = df_filtered["bb_churn_next_30d"].sum()
    churn_rate_30 = (churn_30 / total_filtered_calls) if total_filtered_calls else 0

    avg_outcome_cost = df_filtered["outcome_cost"].mean()

    # page text
    st.write("\n\n")
    st.subheader("All Calls")
    st.write("\n\n")

    # metric cards
    def metric_card_colorful(col, label, value, bg_color):
        with col:
            st.markdown(f"""
            <div style="
                background-color: {bg_color};
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                margin-bottom: 10px;
            ">
                <div style='font-size: 14px; color: #1F2937; font-weight: 500; margin-bottom: 5px;'>{label}</div>
                <div style='font-size: 32px; font-weight: bold; color: #111827;'>{value}</div>
            </div>
            """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    metric_card_colorful(col1, "Total Calls", f"{total_filtered_calls:,}", bg_color="#E0F2FE")   # soft blue
    metric_card_colorful(col2, "Repeat Call Rate (7d)", f"{repeat_rate:.1%}", bg_color="#FEF3C7")  # amber
    metric_card_colorful(col3, "Churn Rate (30d)", f"{churn_rate_30:.1%}", bg_color="#FEE2E2")     # soft red
    metric_card_colorful(col4, "Avg. Outcome Cost (£)", f"£{avg_outcome_cost:,.0f}", bg_color="#EDE9FE")  # lavender / purple

    st.divider()

    #######################################
    ### section 2 - label summary table ###
    #######################################

    st.write("\n\n")
    st.subheader("Label Summary")
    st.write("\n\n")

    df_label_summary = (
        df_filtered.groupby("label")
        .agg(
            volume=("label", "size"),
            avg_outcome_cost=("outcome_cost", "mean"),
            total_outcome_cost=("outcome_cost", "sum"),
            call_rate_7d=("sc_call_next_7d_flag", "mean"),
            churn_rate_30d=("bb_churn_next_30d", "mean"),
        )
        .reset_index()
        .sort_values("volume", ascending=False)
        .reset_index(drop=True) 
    )

    # percentage calculations (numeric)
    total_all = st.session_state.get("df_label_total_rows", len(df_filtered))
    df_label_summary["pct_filtered"] = df_label_summary["volume"] / df_label_summary["volume"].sum()
    df_label_summary["pct_all_calls"] = df_label_summary["volume"] / total_all

    # save numeric copy for charts
    chart_label_df = df_label_summary.copy()

    # display formatting only
    df_label_display = df_label_summary.copy()
    df_label_display = df_label_display.rename(columns={
        "label": "Label",
        "volume": "Calls",
        "avg_outcome_cost": "Avg. Outcome Cost (£)",
        "total_outcome_cost": "Total Outcome Cost (£)",
        "pct_filtered": "% of Filtered",
        "pct_all_calls": "% of All Calls",
        "call_rate_7d": "Repeat Call Rate (7d)",
        "churn_rate_30d": "BB Churn Rate (30d)",
    })

    # format numeric columns for display
    display_format = {
        "Calls": "{:,}",
        "Avg. Outcome Cost (£)": "£{:,.0f}",
        "Total Outcome Cost (£)": "£{:,.0f}",
        "% of Filtered": "{:.1%}",
        "% of All Calls": "{:.1%}",
        "Repeat Call Rate (7d)": "{:.1%}",
        "BB Churn Rate (30d)": "{:.1%}",
    }

    # display dataframe with tooltips
    st.dataframe(
        df_label_display.style.format(display_format),
        use_container_width=True,
        column_config={
            "Label": st.column_config.TextColumn(
                help="Call issue label assigned by the model"
            ),
            "Calls": st.column_config.NumberColumn(
                help="Number of calls associated with this label in the current filter"
            ),
            "Avg. Outcome Cost (£)": st.column_config.NumberColumn(
                help="Average estimated cost of the selected outcome for these calls"
            ),
            "Repeat Call Rate (7d)": st.column_config.NumberColumn(
                help="Percentage of calls followed by another call within 7 days"
            ),
            "BB Churn Rate (30d)": st.column_config.NumberColumn(
                help="Percentage of customers who churned within 30 days of the call"
            ),
            "% of Filtered": st.column_config.NumberColumn(
                help="Proportion of all currently filtered calls represented by this label"
            ),
            "% of All Calls": st.column_config.NumberColumn(
                help="Proportion of all calls in the full dataset represented by this label"
            ),
        }
    )
    st.write("\n\n\n\n")

    # chart checkbox
    show_label_chart = st.checkbox("Show label distribution chart", value=True)
    if show_label_chart:
        chart_df = chart_label_df.copy()
        chart = (
            alt.Chart(chart_df)
            .mark_bar(color="#5A67D8")
            .encode(
                y=alt.Y("label:N", sort="-x", title=None, axis=alt.Axis(labelLimit=0)),
                x=alt.X("pct_filtered:Q", title="% of Filtered Calls"),
                tooltip=[
                    alt.Tooltip("label:N", title="Label"),
                    alt.Tooltip("pct_filtered:Q", title="% of Filtered", format=".1%")
                ]
            )
            .properties(height=45 * len(chart_df))
        )
        st.altair_chart(chart, use_container_width=True)

    st.divider()

    #########################################
    ### section 2 - outcome summary table ###
    #########################################

    st.write("\n\n")
    st.subheader("Outcome Summary")
    st.write("\n\n")

    df_outcome_summary = (
        df_filtered.groupby("selected_outcome_cleaned")
        .agg(
            volume=("selected_outcome_cleaned", "size"),
            avg_outcome_cost=("outcome_cost", "mean"),
            total_outcome_cost=("outcome_cost", "sum"),
            call_rate_7d=("sc_call_next_7d_flag", "mean"),
            churn_rate_30d=("bb_churn_next_30d", "mean"),
        )
        .reset_index()
        .sort_values("volume", ascending=False)
        .reset_index(drop=True)
    )

    # percentage calculations (numeric)
    df_outcome_summary["pct_filtered"] = (
        df_outcome_summary["volume"] / df_outcome_summary["volume"].sum()
    )
    df_outcome_summary["pct_all_calls"] = (
        df_outcome_summary["volume"] / total_all
    )

    # save numeric copy for charts
    chart_outcome_df = df_outcome_summary.copy()

    # display formatting only
    df_outcome_display = df_outcome_summary.rename(columns={
        "selected_outcome_cleaned": "Outcome",
        "volume": "Calls",
        "avg_outcome_cost": "Avg. Outcome Cost (£)",
        "total_outcome_cost": "Total Outcome Cost (£)",
        "pct_filtered": "% of Filtered",
        "pct_all_calls": "% of All Calls",
        "call_rate_7d": "Repeat Call Rate (7d)",
        "churn_rate_30d": "BB Churn Rate (30d)",
    })

    # display dataframe with tooltips
    st.dataframe(
        df_outcome_display.style.format(display_format),
        use_container_width=True,
        column_config={
            "Outcome": st.column_config.TextColumn(
                help="Outcome selected or applied as a result of the call"
            ),
            "Calls": st.column_config.NumberColumn(
                help="Number of calls associated with this outcome in the current filter"
            ),
            "Avg. Outcome Cost (£)": st.column_config.NumberColumn(
                help="Average estimated cost of this outcome"
            ),
            "Total Outcome Cost (£)": st.column_config.NumberColumn(
                help="Total estimated cost across all calls with this outcome"
            ),
            "Repeat Call Rate (7d)": st.column_config.NumberColumn(
                help="Percentage of calls followed by another call within 7 days"
            ),
            "BB Churn Rate (30d)": st.column_config.NumberColumn(
                help="Percentage of customers who churned within 30 days of the call"
            ),
            "% of Filtered": st.column_config.NumberColumn(
                help="Proportion of all currently filtered calls represented by this outcome"
            ),
            "% of All Calls": st.column_config.NumberColumn(
                help="Proportion of all calls in the full dataset represented by this outcome"
            ),
        }
    )

    st.write("\n\n\n\n")

    # chart checkbox
    show_outcome_chart = st.checkbox("Show outcome distribution chart", value=True)
    if show_outcome_chart:
        chart_df = chart_outcome_df.copy()
        chart = (
            alt.Chart(chart_df)
            .mark_bar(color="#5A67D8")
            .encode(
                y=alt.Y(
                    "selected_outcome_cleaned:N",
                    sort="-x",
                    title=None,
                    axis=alt.Axis(labelLimit=0)
                ),
                x=alt.X(
                    "pct_filtered:Q",
                    title="% of Filtered Calls"
                ),
                tooltip=[
                    alt.Tooltip("selected_outcome_cleaned:N", title="Outcome"),
                    alt.Tooltip("pct_filtered:Q", title="% of Filtered", format=".1%")
                ]
            )
            .properties(height=35 * len(chart_df))
        )
        st.altair_chart(chart, use_container_width=True)

    st.divider()
