import streamlit as st
import pandas as pd
import altair as alt
from utils.colours import build_global_color_scale


def render_view(df_filtered):

    # fixed colour palette
    all_outcomes = st.session_state["global_outcomes"]
    color_scale = build_global_color_scale(all_outcomes)

    color=alt.Color("Selected outcome:N", scale=color_scale)

    # Persist view mode across reruns
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "Single table"

    # page text
    st.write("\n\n")
    st.write("For each call issue label evaluate selected outcome performance via repeat calls and churn")
    st.divider()

    # ensure numeric types for calculations
    df_working = df_filtered.copy()
    df_working["outcome_cost"] = pd.to_numeric(df_working["outcome_cost"], errors="coerce")
    df_working["sc_call_next_7d_flag"] = pd.to_numeric(df_working["sc_call_next_7d_flag"], errors="coerce")
    df_working["bb_churn_next_30d"] = pd.to_numeric(df_working["bb_churn_next_30d"], errors="coerce")
    df_working["bb_churn_next_60d"] = pd.to_numeric(df_working["bb_churn_next_60d"], errors="coerce")

    ######################################
    ### Chart 1 - Outcome Distribution ###
    ######################################

    st.subheader("Outcome Distribution by Label")

    # info box for chart
    st.info(
        "Each bar totals 100% after filtering and shows the outcome mix within each label."
    )

    # aggregate for label and selected_outcome view
    df_grouped = (
        df_working.groupby(["label", "selected_outcome_cleaned"])
        .agg(
            volume=("selected_outcome_cleaned", "size"),
            repeat_rate_7d=("sc_call_next_7d_flag", "mean"),
            churn_rate_30d=("bb_churn_next_30d", "mean"),
            churn_rate_60d=("bb_churn_next_60d", "mean"),
            avg_outcome_cost=("outcome_cost", "mean"),
            total_outcome_cost=("outcome_cost", "sum"),
        )
        .reset_index()
    )

    # % of filtered total
    df_grouped["pct_total_volume"] = df_grouped["volume"] / df_grouped["volume"].sum()

    # % of all unfiltered calls
    total_all = st.session_state.get("df_label_total_rows", len(df_working))
    df_grouped["pct_total_all"] = df_grouped["volume"] / total_all

    # chart data
    chart_df = df_grouped.copy()

    # calculate % within each label (so each bar totals 100%)
    chart_df["pct_within_label"] = (
        chart_df.groupby("label")["volume"]
        .transform(lambda x: x / x.sum())
        * 100
    )

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            y=alt.Y(
                "label:N",
                sort="-x",
                title=None
            ),
            x=alt.X(
                "pct_within_label:Q",
                title="% of Label (after filtering)",
                scale=alt.Scale(domain=[0, 100])
            ),
            color=alt.Color("selected_outcome_cleaned:N", title="Selected outcome", scale=color_scale),
            tooltip=[
                alt.Tooltip("label:N"),
                alt.Tooltip("selected_outcome_cleaned:N", title="Selected outcome"),
                alt.Tooltip("pct_within_label:Q", title="% of label", format=".1f")
            ]
        )
        .properties(height=45 * len(chart_df["label"].unique()))
    )

    st.altair_chart(chart, use_container_width=True)

    st.divider()


    ###################################
    ### Chart 2 - Outcome Breakdown ###
    ###################################

    st.subheader("Outcome Breakdown Table")

    # info box for table
    st.info(
        "This table shows the outcome mix for each label, along with repeat call and churn performance."
    )

    # calculate rates (keep only rates, remove raw sums)
    df_grouped["repeat_rate_7d"] = df_grouped["repeat_rate_7d"]
    df_grouped["churn_rate_30d"] = df_grouped["churn_rate_30d"]
    df_grouped["churn_rate_60d"] = df_grouped["churn_rate_60d"]

    # formatting
    df_grouped["avg_outcome_cost"] = df_grouped["avg_outcome_cost"].map(lambda x: f"£{x:,.0f}")
    df_grouped["total_outcome_cost"] = df_grouped["total_outcome_cost"].map(lambda x: f"£{x:,.0f}")
    df_grouped["pct_total_volume"] = df_grouped["pct_total_volume"].map(lambda x: f"{x:.1%}")
    df_grouped["pct_total_all"] = df_grouped["pct_total_all"].map(lambda x: f"{x:.1%}")
    df_grouped["repeat_rate_7d"] = df_grouped["repeat_rate_7d"].map(lambda x: f"{x:.1%}")
    df_grouped["churn_rate_30d"] = df_grouped["churn_rate_30d"].map(lambda x: f"{x:.1%}")
    df_grouped["churn_rate_60d"] = df_grouped["churn_rate_60d"].map(lambda x: f"{x:.1%}")

    # rename columns
    df_grouped = df_grouped.rename(columns={
        "label": "Call issue label",
        "selected_outcome_cleaned": "Selected outcome",
        "volume": "Volume",
        "avg_outcome_cost": "Avg. Outcome Cost (£)",
        "total_outcome_cost": "Total Outcome Cost (£)",
        "pct_total_volume": "% of Filtered",
        "pct_total_all": "% of All Calls",
        "repeat_rate_7d": "Repeat rate (7d)",
        "churn_rate_30d": "Churn Rate (30d)",
        "churn_rate_60d": "Churn Rate (60d)"
    })

    # reset index
    df_grouped = df_grouped.sort_values(by="Volume", ascending=False).reset_index(drop=True)

    # view toggle
    view_mode = st.radio(
        "Choose view type:",
        options=["Single table", "Table per call issue label"],
        index=0,
        key="view_mode"
    )

    # single table view
    if view_mode == "Single table":
        st.dataframe(df_grouped, width='stretch')

    # expandable per label view
    else:
        labels = df_grouped["Call issue label"].unique()
        for label in labels:
            with st.expander(label):
                df_label_group = df_grouped[df_grouped["Call issue label"] == label]
                st.dataframe(df_label_group, width='stretch')

    # remaining rows after filtering
    st.caption(f"{len(df_working):,} rows remaining after filtering")

    st.divider()


    ###################################
    ### Section 3 - Risk Tiering ###
    ###################################

    st.subheader("Risk Tiering by Outcome")

    # info box for risk tiering
    st.info(
        "Assign importance sliders to the KPIs below. The system calculates a percentile-based risk score per outcome and groups them into Low, Medium and High risk tiers."
    )

    # KPI importance sliders (0–100)
    col1, col2, col3 = st.columns(3)

    with col1:
        weight_repeat = st.slider(
            "Repeat call importance",
            min_value=0,
            max_value=100,
            value=33,
            key="weight_repeat"
        )

    with col2:
        weight_churn = st.slider(
            "Churn importance",
            min_value=0,
            max_value=100,
            value=33,
            key="weight_churn"
        )

    with col3:
        weight_cost = st.slider(
            "Cost importance",
            min_value=0,
            max_value=100,
            value=34,
            key="weight_cost"
        )

    # warning if weights don't add to 100
    if weight_repeat + weight_churn + weight_cost != 100:
        st.warning(
            "Weights do not add up to 100. They will be normalised automatically, but please adjust if you want the exact proportions."
        )

    # risk tier thresholds
    t_col1, t_col2 = st.columns(2)

    with t_col1:
        low_threshold = st.slider(
            "Low / Medium boundary",
            min_value=0.0,
            max_value=1.0,
            value=0.33,
            step=0.01,
            key="low_threshold"
        )

    with t_col2:
        med_threshold = st.slider(
            "Medium / High boundary",
            min_value=0.0,
            max_value=1.0,
            value=0.66,
            step=0.01,
            key="med_threshold"
        )

    st.write("\n\n\n\n")

    # normalise weights to sum to 1
    weight_sum = weight_repeat + weight_churn + weight_cost
    if weight_sum == 0:
        weight_sum = 1

    w_repeat = weight_repeat / weight_sum
    w_churn = weight_churn / weight_sum
    w_cost = weight_cost / weight_sum

    # calculate risk score
    risk_df = df_grouped.copy()

    # convert formatted % back to numeric
    risk_df["Repeat rate (7d)"] = risk_df["Repeat rate (7d)"].str.rstrip("%").astype(float)
    risk_df["Churn Rate (30d)"] = risk_df["Churn Rate (30d)"].str.rstrip("%").astype(float)

    # cost conversion
    risk_df["Avg. Outcome Cost (£)"] = (
        risk_df["Avg. Outcome Cost (£)"]
        .str.replace("£", "")
        .str.replace(",", "")
        .astype(float)
    )

    # percentile scores (0–1) instead of max normalization
    risk_df["repeat_score"] = risk_df["Repeat rate (7d)"].rank(pct=True)
    risk_df["churn_score"] = risk_df["Churn Rate (30d)"].rank(pct=True)
    risk_df["cost_score"] = risk_df["Avg. Outcome Cost (£)"].rank(pct=True)

    # weighted risk score
    risk_df["risk_score"] = (
        risk_df["repeat_score"] * w_repeat +
        risk_df["churn_score"] * w_churn +
        risk_df["cost_score"] * w_cost
    )

    # assign tiers using thresholds
    risk_df["risk_tier"] = pd.cut(
        risk_df["risk_score"],
        bins=[-0.01, low_threshold, med_threshold, 1.01],
        labels=["Low", "Medium", "High"]
    )

    # =========================
    # View 1 - Compact (single label)
    # =========================

    selected_label = st.selectbox(
        "Choose label:",
        options=sorted(risk_df["Call issue label"].unique()),
        key="risk_label_select"
    )

    label_df = risk_df[risk_df["Call issue label"] == selected_label]

    risk_chart_single = (
        alt.Chart(label_df)
        .mark_circle(size=120)
        .encode(
            x=alt.X("risk_score:Q", title="Risk score (0–1)"),
            y=alt.Y("Selected outcome:N", title=None, sort="-x"),
            color=alt.Color("risk_tier:N", title="Risk tier"),
            tooltip=[
                alt.Tooltip("Selected outcome:N", title="Outcome"),
                alt.Tooltip("risk_score:Q", title="Risk score", format=".2f"),
                alt.Tooltip("risk_tier:N", title="Risk tier")
            ]
        )
        .properties(height=25 * len(label_df["Selected outcome"].unique()))
    )

    st.altair_chart(risk_chart_single, use_container_width=True)

    st.divider()

    # =========================
    # View 2 - Full (all labels)
    # =========================

    risk_chart_full = (
        alt.Chart(risk_df)
        .mark_circle(size=120)
        .encode(
            x=alt.X("risk_score:Q", title="Risk score (0–1)"),
            y=alt.Y("Call issue label:N", title=None, sort="-x"),
            color=alt.Color("risk_tier:N", title="Risk tier"),
            tooltip=[
                alt.Tooltip("Call issue label:N", title="Label"),
                alt.Tooltip("Selected outcome:N", title="Outcome"),
                alt.Tooltip("risk_score:Q", title="Risk score", format=".2f"),
                alt.Tooltip("risk_tier:N", title="Risk tier")
            ]
        )
        .properties(height=45 * len(risk_df["Call issue label"].unique()))
    )

    st.altair_chart(risk_chart_full, use_container_width=True)

    st.divider()
