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

    # kpi cards
    def custom_metric(col, label, value):
        with col:
            st.markdown(f"""
            <div style='text-align: center; padding: 10px;'>
                <div style='font-size: 14px; color: #666;'>{label}</div>
                <div style='font-size: 28px; font-weight: bold; color: #5A67D8;'>{value}</div>
            </div>
            """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    custom_metric(col1, "Total Calls", f"{total_filtered_calls:,}")
    custom_metric(col2, "Repeat Call Rate (7d)", f"{repeat_rate:.1%}")
    custom_metric(col3, "Churn Rate (30d)", f"{churn_rate_30:.1%}")
    custom_metric(col4, "Avg. Outcome Cost (£)", f"£{avg_outcome_cost:,.0f}")

    st.divider()


    #######################################
    ### section 1 - label summary table ###
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
    )

    # add percentage columns
    total_all = st.session_state.get("df_label_total_rows", len(df_filtered))
    df_label_summary["pct_filtered"] = df_label_summary["volume"] / df_label_summary["volume"].sum()
    df_label_summary["pct_all_calls"] = df_label_summary["volume"] / total_all

    # rename columns
    df_label_summary = df_label_summary.rename(columns={
        "label": "Label",
        "volume": "Volume",
        "avg_outcome_cost": "Avg. Outcome Cost (£)",
        "total_outcome_cost": "Total Outcome Cost (£)",
        "pct_filtered": "% of Filtered",
        "pct_all_calls": "% of All Calls",
        "call_rate_7d": "Call Rate (7d)",
        "churn_rate_30d": "Churn Rate (30d)",
    })

    # format columns
    df_label_summary["Avg. Outcome Cost (£)"] = df_label_summary["Avg. Outcome Cost (£)"].map(lambda x: f"£{x:,.0f}")
    df_label_summary["Total Outcome Cost (£)"] = df_label_summary["Total Outcome Cost (£)"].map(lambda x: f"£{x:,.0f}")
    df_label_summary["% of Filtered"] = df_label_summary["% of Filtered"].map(lambda x: f"{x:.1%}")
    df_label_summary["% of All Calls"] = df_label_summary["% of All Calls"].map(lambda x: f"{x:.1%}")
    df_label_summary["Call Rate (7d)"] = df_label_summary["Call Rate (7d)"].map(lambda x: f"{x:.1%}")
    df_label_summary["Churn Rate (30d)"] = df_label_summary["Churn Rate (30d)"].map(lambda x: f"{x:.1%}")


    # reset index for table
    df_label_summary = df_label_summary.reset_index(drop=True)

    st.dataframe(df_label_summary, width='stretch')
    st.write("\n\n\n\n")

    show_label_chart = st.checkbox(
        "Show label distribution chart",
        value=True
    )

    if show_label_chart:

        # prepare chart data
        chart_df = df_label_summary.copy()
        chart_df["pct_filtered_numeric"] = (
            chart_df["% of Filtered"]
            .str.rstrip("%")
            .astype(float)
        )

        # build chart
        chart = (
            alt.Chart(chart_df)
            .mark_bar(color="#5A67D8")
            .encode(
                y=alt.Y(
                    "Label:N",
                    sort="-x",
                    title=None,
                    axis=alt.Axis(labelLimit=0)
                ),
                x=alt.X(
                    "pct_filtered_numeric:Q",
                    title="% of Filtered Calls"
                ),
                tooltip=[
                    alt.Tooltip("Label:N"),
                    alt.Tooltip(
                        "pct_filtered_numeric:Q",
                        title="% of Filtered",
                        format=".1f"
                    )
                ],
            )
            .properties(height=45 * len(chart_df))
        )

        st.altair_chart(chart, width='stretch')


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
    )

    # add percentage columns
    total_all = st.session_state.get("df_label_total_rows", len(df_filtered))
    df_outcome_summary["pct_filtered"] = df_outcome_summary["volume"] / df_outcome_summary["volume"].sum()
    df_outcome_summary["pct_all_calls"] = df_outcome_summary["volume"] / total_all

    # rename columns
    df_outcome_summary = df_outcome_summary.rename(columns={
        "selected_outcome_cleaned": "Outcome",
        "volume": "Volume",
        "avg_outcome_cost": "Avg. Outcome Cost (£)",
        "total_outcome_cost": "Total Outcome Cost (£)",
        "pct_filtered": "% of Filtered",
        "pct_all_calls": "% of All Calls",
        "call_rate_7d": "Call Rate (7d)",
        "churn_rate_30d": "Churn Rate (30d)",
    })

    # format columns
    df_outcome_summary["Avg. Outcome Cost (£)"] = df_outcome_summary["Avg. Outcome Cost (£)"].map(lambda x: f"£{x:,.0f}")
    df_outcome_summary["Total Outcome Cost (£)"] = df_outcome_summary["Total Outcome Cost (£)"].map(lambda x: f"£{x:,.0f}")
    df_outcome_summary["% of Filtered"] = df_outcome_summary["% of Filtered"].map(lambda x: f"{x:.1%}")
    df_outcome_summary["% of All Calls"] = df_outcome_summary["% of All Calls"].map(lambda x: f"{x:.1%}")
    df_outcome_summary["Call Rate (7d)"] = df_outcome_summary["Call Rate (7d)"].map(lambda x: f"{x:.1%}")
    df_outcome_summary["Churn Rate (30d)"] = df_outcome_summary["Churn Rate (30d)"].map(lambda x: f"{x:.1%}")


    # reset index for table
    df_outcome_summary = df_outcome_summary.reset_index(drop=True)

    st.dataframe(df_outcome_summary, width='stretch')
    st.write("\n\n\n\n")

    show_outcome_chart = st.checkbox(
        "Show outcome distribution chart",
        value=True
    )

    if show_outcome_chart:

        # prepare chart data
        chart_df = df_outcome_summary.copy()
        chart_df["pct_filtered_numeric"] = (
            chart_df["% of Filtered"]
            .str.rstrip("%")
            .astype(float)
        )

        # build chart
        chart = (
            alt.Chart(chart_df)
            .mark_bar(color="#5A67D8")
            .encode(
                y=alt.Y(
                    "Outcome:N",
                    sort="-x",
                    title=None,
                    axis=alt.Axis(labelLimit=0)
                ),
                x=alt.X(
                    "pct_filtered_numeric:Q",
                    title="% of Filtered Calls"
                ),
                tooltip=[
                    alt.Tooltip("Outcome:N"),
                    alt.Tooltip(
                        "pct_filtered_numeric:Q",
                        title="% of Filtered",
                        format=".1f"
                    )
                ],
            )
            .properties(height=35 * len(chart_df))
        )

        st.altair_chart(chart, width='stretch')

    st.divider()