import streamlit as st
import pandas as pd
import altair as alt

def render_view(df_filtered):

    #########################
    ### section 0 - page text ###
    #########################

    st.write("\n\n")
    st.markdown(
        '<span style="font-size: 1.1rem; font-weight: 400;">High-level summaries of call issues, outcomes, and key metrics to understand the landscape</span>',
        unsafe_allow_html=True
    )
    st.divider()

    #########################
    ### section 1 - KPI summary ###
    #########################

    # ensure numeric
    numeric_cols = ["outcome_cost", "sc_call_next_7d_flag", "bb_churn_next_30d", "bb_churn_next_60d"]
    for col in numeric_cols:
        df_filtered[col] = pd.to_numeric(df_filtered[col], errors="coerce")

    # ensure datetime
    df_filtered["call_date"] = pd.to_datetime(df_filtered["call_date"], errors="coerce")

    # calculate KPIs
    total_calls = len(df_filtered)
    repeat_rate = df_filtered["sc_call_next_7d_flag"].mean() if total_calls else 0
    churn_rate_30 = df_filtered["bb_churn_next_30d"].mean() if total_calls else 0
    avg_cost = df_filtered["outcome_cost"].mean()

    # KPI cards
    def metric_card_colorful(col, label, value, bg_color):
        with col:
            st.markdown(f"""
            <div style="background-color: {bg_color}; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 10px;">
                <div style='font-size: 14px; color: #1F2937; font-weight: 500; margin-bottom: 5px;'>{label}</div>
                <div style='font-size: 32px; font-weight: bold; color: #111827;'>{value}</div>
            </div>
            """, unsafe_allow_html=True)

    # order: Calls (blue), Avg Cost (purple), Repeat (yellow), Churn (red)
    col1, col2, col3, col4 = st.columns(4)
    metric_card_colorful(col1, "Calls", f"{total_calls:,}", bg_color="#E0F2FE")  # blue
    metric_card_colorful(col2, "Avg Outcome Cost (£)", f"£{avg_cost:,.0f}", bg_color="#EDE9FE")  # purple
    metric_card_colorful(col3, "Repeat Call Rate (7d)", f"{repeat_rate:.1%}", bg_color="#FEF3C7")  # yellow
    metric_card_colorful(col4, "Churn Rate (30d)", f"{churn_rate_30:.1%}", bg_color="#FEE2E2")  # red

    st.divider()

    #########################
    ### section 2 - label summary table ###
    #########################

    st.subheader("Label Summary")

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

    total_all = len(df_filtered)
    df_label_summary["pct_filtered"] = df_label_summary["volume"] / df_label_summary["volume"].sum()
    df_label_summary["pct_all_calls"] = df_label_summary["volume"] / total_all

    chart_label_df = df_label_summary.copy()

    df_label_display = df_label_summary.rename(columns={
        "label": "Label",
        "volume": "Calls",
        "avg_outcome_cost": "Avg. Outcome Cost (£)",
        "total_outcome_cost": "Total Outcome Cost (£)",
        "pct_filtered": "% of Filtered",
        "pct_all_calls": "% of All Calls",
        "call_rate_7d": "Repeat Call Rate (7d)",
        "churn_rate_30d": "BB Churn Rate (30d)",
    })

    display_format = {
        "Calls": "{:,}",
        "Avg. Outcome Cost (£)": "£{:,.0f}",
        "Total Outcome Cost (£)": "£{:,.0f}",
        "% of Filtered": "{:.1%}",
        "% of All Calls": "{:.1%}",
        "Repeat Call Rate (7d)": "{:.1%}",
        "BB Churn Rate (30d)": "{:.1%}",
    }

    st.dataframe(
        df_label_display.style.format(display_format),
        use_container_width=True,
        column_config={
            "Label": st.column_config.TextColumn(help="Call issue label assigned by the model"),
            "Calls": st.column_config.NumberColumn(help="Number of calls associated with this label"),
            "Avg. Outcome Cost (£)": st.column_config.NumberColumn(help="Average estimated cost"),
            "Total Outcome Cost (£)": st.column_config.NumberColumn(help="Total estimated cost"),
            "Repeat Call Rate (7d)": st.column_config.NumberColumn(help="Percentage of calls followed by another call within 7 days"),
            "BB Churn Rate (30d)": st.column_config.NumberColumn(help="Percentage of customers who churned within 30 days"),
            "% of Filtered": st.column_config.NumberColumn(help="Proportion of filtered calls"),
            "% of All Calls": st.column_config.NumberColumn(help="Proportion of all calls"),
        }
    )

    st.caption(f"{chart_label_df.volume.sum():,} calls remaining after global filters applied")

    # Metrics-over-time toggle
    show_label_metrics = st.checkbox("Show label metrics over time", value=False, key="label_metrics")
    if show_label_metrics:

        # selectors: metric, grain, split
        col_metric, col_grain, col_split = st.columns(3)
        metric_choice = col_metric.selectbox(
            "Metric:",
            ["Calls", "Avg Outcome Cost (£)", "Repeat Call Rate (7d)", "Churn Rate (30d)"],
            index=0,
            key="label_metric_choice"
        )
        grain_choice = col_grain.selectbox(
            "Time Grain:",
            ["Weekly", "Monthly"],
            index=0,
            key="label_grain_choice"
        )
        split_choice = col_split.selectbox(
            "Split by Label (optional):",
            ["None"],
            index=0,
            key="label_split_choice"
        )

        freq = "W" if grain_choice == "Weekly" else "M"

        df_time = df_filtered.copy()
        df_time["period"] = df_time["call_date"].dt.to_period(freq).dt.start_time

        y_col_map = {
            "Calls": "volume",
            "Avg Outcome Cost (£)": "avg_outcome_cost",
            "Repeat Call Rate (7d)": "call_rate_7d",
            "Churn Rate (30d)": "churn_rate_30d"
        }

        # aggregate
        df_agg = df_time.groupby("period").agg(
            volume=("label", "size"),
            avg_outcome_cost=("outcome_cost", "mean"),
            call_rate_7d=("sc_call_next_7d_flag", "mean"),
            churn_rate_30d=("bb_churn_next_30d", "mean"),
        ).reset_index()
        df_agg["avg_outcome_cost"] = df_agg["avg_outcome_cost"].round(0)

        # assign colors (calls, avg, repeat, churn)
        color_map = {
            "Calls": "#1E40AF",  # blue
            "Avg Outcome Cost (£)": "#6B21A8",  # purple
            "Repeat Call Rate (7d)": "#D97706",  # yellow/orange
            "Churn Rate (30d)": "#B91C1C"  # red
        }

        line_color = color_map[metric_choice]

        # plot line + points
        line = alt.Chart(df_agg).mark_line(strokeWidth=4, color=line_color).encode(
            x=alt.X("period:T", title="Period", axis=alt.Axis(format="%d %b")),
            y=alt.Y(f"{y_col_map[metric_choice]}:Q",
                    title=metric_choice,
                    axis=alt.Axis(format=".0%" if "Rate" in metric_choice else "~s")),
            tooltip=[
                alt.Tooltip("period:T", title="Period"),
                alt.Tooltip(f"{y_col_map[metric_choice]}:Q", title=metric_choice,
                            format=",.0f" if "Outcome" in metric_choice or "Calls" in metric_choice else ".1%")
            ]
        )

        points = alt.Chart(df_agg).mark_point(size=60, color=line_color).encode(
            x="period:T",
            y=f"{y_col_map[metric_choice]}:Q",
            tooltip=[
                alt.Tooltip("period:T", title="Period"),
                alt.Tooltip(f"{y_col_map[metric_choice]}:Q", title=metric_choice,
                            format=",.0f" if "Outcome" in metric_choice or "Calls" in metric_choice else ".1%")
            ]
        )

        chart = line + points
        st.altair_chart(chart, use_container_width=True, theme="streamlit", height=300)

    st.divider()

    #########################
    ### section 3 - outcome summary table ###
    #########################

    st.subheader("Outcome Summary")

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

    df_outcome_summary["pct_filtered"] = df_outcome_summary["volume"] / df_outcome_summary["volume"].sum()
    df_outcome_summary["pct_all_calls"] = df_outcome_summary["volume"] / total_all

    chart_outcome_df = df_outcome_summary.copy()

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

    st.dataframe(
        df_outcome_display.style.format(display_format),
        use_container_width=True,
        column_config={
            "Outcome": st.column_config.TextColumn(help="Outcome selected or applied as a result of the call"),
            "Calls": st.column_config.NumberColumn(help="Number of calls associated with this outcome"),
            "Avg. Outcome Cost (£)": st.column_config.NumberColumn(help="Average estimated cost"),
            "Total Outcome Cost (£)": st.column_config.NumberColumn(help="Total estimated cost"),
            "Repeat Call Rate (7d)": st.column_config.NumberColumn(help="Percentage of calls followed by another call within 7 days"),
            "BB Churn Rate (30d)": st.column_config.NumberColumn(help="Percentage of customers who churned within 30 days"),
            "% of Filtered": st.column_config.NumberColumn(help="Proportion of filtered calls"),
            "% of All Calls": st.column_config.NumberColumn(help="Proportion of all calls"),
        }
    )

    st.caption(f"{chart_outcome_df.volume.sum():,} calls remaining after global filters applied")

    # Metrics-over-time toggle for outcomes
    show_outcome_metrics = st.checkbox("Show outcome metrics over time", value=False, key="outcome_metrics")
    if show_outcome_metrics:
        # default metric: Calls, grain: weekly, split by outcome optional
        col_metric, col_grain, col_split = st.columns(3)
        metric_choice = col_metric.selectbox(
            "Metric:",
            ["Calls", "Avg Outcome Cost (£)", "Repeat Call Rate (7d)", "Churn Rate (30d)"],
            index=0,
            key="outcome_metric_choice"
        )
        grain_choice = col_grain.selectbox(
            "Time Grain:",
            ["Weekly", "Monthly"],
            index=0,
            key="outcome_grain_choice"
        )
        split_choice = col_split.selectbox(
            "Split by Outcome (optional):",
            ["None"],
            index=0,
            key="outcome_split_choice"
        )

        freq = "W" if grain_choice == "Weekly" else "M"

        df_time = df_filtered.copy()
        df_time["period"] = df_time["call_date"].dt.to_period(freq).dt.start_time

        df_agg = df_time.groupby("period").agg(
            volume=("selected_outcome_cleaned", "size"),
            avg_outcome_cost=("outcome_cost", "mean"),
            call_rate_7d=("sc_call_next_7d_flag", "mean"),
            churn_rate_30d=("bb_churn_next_30d", "mean"),
        ).reset_index()
        df_agg["avg_outcome_cost"] = df_agg["avg_outcome_cost"].round(0)

        y_col_map = {
            "Calls": "volume",
            "Avg Outcome Cost (£)": "avg_outcome_cost",
            "Repeat Call Rate (7d)": "call_rate_7d",
            "Churn Rate (30d)": "churn_rate_30d"
        }
        color_map = {
            "Calls": "#1E40AF",  # blue
            "Avg Outcome Cost (£)": "#6B21A8",  # purple
            "Repeat Call Rate (7d)": "#D97706",  # yellow/orange
            "Churn Rate (30d)": "#B91C1C"  # red
        }
        line_color = color_map[metric_choice]

        line = alt.Chart(df_agg).mark_line(strokeWidth=4, color=line_color).encode(
            x=alt.X("period:T", title="Period", axis=alt.Axis(format="%d %b")),
            y=alt.Y(f"{y_col_map[metric_choice]}:Q",
                    title=metric_choice,
                    axis=alt.Axis(format=".0%" if "Rate" in metric_choice else "~s")),
            tooltip=[
                alt.Tooltip("period:T", title="Period"),
                alt.Tooltip(f"{y_col_map[metric_choice]}:Q", title=metric_choice,
                            format=",.0f" if "Outcome" in metric_choice or "Calls" in metric_choice else ".1%")
            ]
        )

        points = alt.Chart(df_agg).mark_point(size=60, color=line_color).encode(
            x="period:T",
            y=f"{y_col_map[metric_choice]}:Q",
            tooltip=[
                alt.Tooltip("period:T", title="Period"),
                alt.Tooltip(f"{y_col_map[metric_choice]}:Q", title=metric_choice,
                            format=",.0f" if "Outcome" in metric_choice or "Calls" in metric_choice else ".1%")
            ]
        )

        chart = line + points
        st.altair_chart(chart, use_container_width=True, theme="streamlit", height=300)

    st.divider()
