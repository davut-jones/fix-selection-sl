import streamlit as st
import pandas as pd
import altair as alt
from utils.colours import build_global_color_scale

def render_view(df_filtered):

    # page text
    st.write("\n\n")
    st.markdown(
        '<span style="font-size: 1.1rem; font-weight: 400;">For each call issue label evaluate selected outcome performance via repeat calls and churn</span>',
        unsafe_allow_html=True
    )
    st.divider()

    # fixed colour palette
    all_outcomes = st.session_state["global_outcomes"]
    color_scale = build_global_color_scale(all_outcomes)

    # persist view mode across reruns
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "Single table"

    # ensure numeric types for calculations
    df_working = df_filtered.copy()
    df_working["outcome_cost"] = pd.to_numeric(df_working["outcome_cost"], errors="coerce")
    df_working["sc_call_next_7d_flag"] = pd.to_numeric(df_working["sc_call_next_7d_flag"], errors="coerce")
    df_working["bb_churn_next_30d"] = pd.to_numeric(df_working["bb_churn_next_30d"], errors="coerce")
    df_working["bb_churn_next_60d"] = pd.to_numeric(df_working["bb_churn_next_60d"], errors="coerce")


    ########################################
    ### section 1 - outcome distribution ###
    ########################################

    st.subheader("Outcome Distribution by Label")

    # info box for chart
    st.write("\n\n")
    st.info("Each bar totals 100% after filtering and shows the outcome mix within each label for those selected.")
    st.write("\n\n")

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

    # order labels
    label_order = [
        "Wi-Fi Status",
        "Unreliable Wi-Fi",
        "Slow Wi-Fi",
        "Poor Coverage",
        "Other",
        "Unclear"
    ]

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            y=alt.Y(
                "label:N",
                sort=alt.SortArray(label_order),
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

    st.altair_chart(chart, width='stretch')

    # remaining rows after filtering
    st.caption(f"{chart_df.volume.sum():,} calls remaining after global filters applied")

    st.divider()


    #####################################
    ### section 2 - outcome breakdown ###
    #####################################

    st.subheader("Outcome Breakdown Table")

    # info box for table
    st.write("\n\n")
    st.info("This table shows the outcome mix for each label, along with repeat call and churn performance.")
    st.write("\n\n")

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
    st.caption(f"{df_grouped['Volume'].sum():,} calls remaining after global filters applied")

    st.divider()


    ################################
    ### section 3 - risk tiering ###
    ################################

    st.subheader("Risk Tiering by Outcome")

    # info box for risk tiering
    st.write("\n\n")
    st.info(
        "Assign importance weights to the KPIs below. "
        "Percentile-based risk score per outcome grouped "
        "into **Low**, **Medium** and **High** risk tiers. "
        "0% represents the lowest risk outcome and 100% the highest risk outcome."
    )
    st.write("\n\n")

    # ---------------------------
    # Reset callbacks
    # ---------------------------
    def reset_weights():
        st.session_state.weight_repeat = 33
        st.session_state.weight_churn = 33
        st.session_state.weight_cost = 34

    def reset_boundaries():
        st.session_state.low_threshold = 0.33
        st.session_state.med_threshold = 0.66

    # ---------------------------
    # KPI importance sliders (0–100)
    # ---------------------------
    col1, col2, col3, col4 = st.columns([1, 1, 1, 0.5])

    with col1:
        weight_repeat = st.slider(
            "Repeat call rate (7d) importance:",
            min_value=0,
            max_value=100,
            value=st.session_state.get("weight_repeat", 33),
            key="weight_repeat"
        )

    with col2:
        weight_churn = st.slider(
            "Churn rate (30d) importance:",
            min_value=0,
            max_value=100,
            value=st.session_state.get("weight_churn", 33),
            key="weight_churn"
        )

    with col3:
        weight_cost = st.slider(
            "Outcome cost importance:",
            min_value=0,
            max_value=100,
            value=st.session_state.get("weight_cost", 34),
            key="weight_cost"
        )

    with col4:
        st.button("Reset weights", on_click=reset_weights)

    # warning if weights don't add to 100
    if weight_repeat + weight_churn + weight_cost != 100:
        st.warning(
            "Weights do not add up to 100. They will be normalised automatically, "
            "but please adjust if you want the exact proportions."
        )

    # ---------------------------
    # risk tier thresholds
    # ---------------------------
    t_col1, t_col2, t_col3 = st.columns([1, 1, 0.5])

    with t_col1:
        low_threshold = st.slider(
            "Low - medium boundary:",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get("low_threshold", 0.33),
            step=0.01,
            key="low_threshold"
        )

    with t_col2:
        med_threshold = st.slider(
            "Medium - high boundary:",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get("med_threshold", 0.66),
            step=0.01,
            key="med_threshold"
        )

    with t_col3:
        st.button("Reset boundaries", on_click=reset_boundaries)

    st.write("\n\n")


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

    # percentile scores (0–1)
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

    # convert score to 0-100% for display
    risk_df["risk_pct"] = (risk_df["risk_score"] * 100).round(1)

    # fixed colour scale for tiers
    tier_color_scale = alt.Scale(
        domain=["Low", "Medium", "High"],
        range=["#2ECC71", "#FFB300", "#E74C3C"]  # green, amber, red
    )

    # view toggle (single label vs all labels)
    view_toggle = st.radio(
        "Choose view:",
        options=["Single label", "All labels"],
        index=0,
        key="risk_view_toggle"
    )

    ### single label view ###

    if view_toggle == "Single label":

        single_labels = [lbl for lbl in label_order if lbl in risk_df["Call issue label"].unique()]
        default_label = "Wi-Fi Status"
        selected_label = st.selectbox(
            "Choose label:",
            options=single_labels,
            index=single_labels.index(default_label) if default_label in single_labels else 0,
            key="risk_label_select"
        )

        label_df = risk_df[risk_df["Call issue label"] == selected_label]

        height_single = min(300, 25 * len(label_df["Selected outcome"].unique()))

        risk_chart_single = (
            alt.Chart(label_df)
            .mark_circle(size=120)
            .encode(
                x=alt.X(
                    "risk_pct:Q",
                    title="Risk score (0–100%)",
                    scale=alt.Scale(domain=[0, 100])
                ),
                y=alt.Y(
                    "Selected outcome:N",
                    title=None,
                    sort="-x",
                    axis=alt.Axis(labelLimit=400, labelFontSize=12)
                ),
                color=alt.Color("risk_tier:N", title="Risk tier", scale=tier_color_scale),
                tooltip=[
                    alt.Tooltip("Selected outcome:N", title="Outcome"),
                    alt.Tooltip("risk_pct:Q", title="Risk score", format=".1f"),
                    alt.Tooltip("risk_tier:N", title="Risk tier"),
                    alt.Tooltip("Repeat rate (7d):Q", title="Repeat rate (7d)", format=".1%"),
                    alt.Tooltip("Churn Rate (30d):Q", title="Churn rate (30d)", format=".1%"),
                    alt.Tooltip("Avg. Outcome Cost (£):Q", title="Avg. outcome cost (£)")
                ]
            )
            .properties(height=height_single)
        )

        st.altair_chart(risk_chart_single, width='stretch')

    ### all labels view ###

    else:

        risk_chart_full = (
            alt.Chart(risk_df)
            .mark_circle(size=120)
            .encode(
                x=alt.X(
                    "risk_pct:Q",
                    title="Risk score (0–100%)",
                    scale=alt.Scale(domain=[0, 100])
                ),
                y=alt.Y(
                    "Call issue label:N",
                    title=None,
                    sort=alt.SortArray(label_order)
                ),
                color=alt.Color("risk_tier:N", title="Risk tier", scale=tier_color_scale),
                tooltip=[
                    alt.Tooltip("Call issue label:N", title="Label"),
                    alt.Tooltip("Selected outcome:N", title="Outcome"),
                    alt.Tooltip("risk_pct:Q", title="Risk score", format=".1f"),
                    alt.Tooltip("risk_tier:N", title="Risk tier"),
                    alt.Tooltip("Repeat rate (7d):Q", title="Repeat rate (7d)", format=".1%"),
                    alt.Tooltip("Churn Rate (30d):Q", title="Churn rate (30d)", format=".1%"),
                    alt.Tooltip("Avg. Outcome Cost (£):Q", title="Avg. outcome cost (£)")
                ]
            )
            .properties(height=45 * len(label_order))
        )

        st.altair_chart(risk_chart_full, width='stretch')

    st.divider()