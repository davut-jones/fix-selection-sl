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

    # ensure numeric types
    df_working = df_filtered.copy()
    df_working["outcome_cost"] = pd.to_numeric(df_working["outcome_cost"], errors="coerce")
    df_working["sc_call_next_7d_flag"] = pd.to_numeric(df_working["sc_call_next_7d_flag"], errors="coerce")
    df_working["bb_churn_next_30d"] = pd.to_numeric(df_working["bb_churn_next_30d"], errors="coerce")
    df_working["bb_churn_next_60d"] = pd.to_numeric(df_working["bb_churn_next_60d"], errors="coerce")

    ########################################
    ### section 1 - outcome distribution ###
    ########################################

    st.subheader("Outcome Distribution by Label")

    st.write("\n\n")
    st.info("Each bar totals 100% after filtering and shows the outcome mix within each label for those selected.")
    st.write("\n\n")

    # aggregate
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

    # pct calculations
    df_grouped["pct_total_volume"] = df_grouped["volume"] / df_grouped["volume"].sum()
    total_all = st.session_state.get("df_label_total_rows", len(df_working))
    df_grouped["pct_total_all"] = df_grouped["volume"] / total_all

    # chart df
    chart_df = df_grouped.copy()
    chart_df["pct_within_label"] = chart_df.groupby("label")["volume"].transform(lambda x: x / x.sum() * 100)

    label_order = [
        "Wi-Fi Status", "Unreliable Wi-Fi", "Slow Wi-Fi",
        "Poor Coverage", "Other", "Unclear"
    ]

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            y=alt.Y("label:N", sort=alt.SortArray(label_order), title=None),
            x=alt.X("pct_within_label:Q", title="% of Label (after filtering)", scale=alt.Scale(domain=[0,100])),
            color=alt.Color("selected_outcome_cleaned:N", title="Outcome", scale=color_scale),
            tooltip=[
                alt.Tooltip("label:N"),
                alt.Tooltip("selected_outcome_cleaned:N", title="Outcome"),
                alt.Tooltip("pct_within_label:Q", title="% of label", format=".1f")
            ]
        )
        .properties(height=45 * len(chart_df["label"].unique()))
    )

    st.altair_chart(chart, width='stretch')
    st.caption(f"{chart_df['volume'].sum():,} calls remaining after global filters applied")
    st.divider()

    #####################################
    ### section 2 - outcome breakdown ###
    #####################################

    st.subheader("Outcome Breakdown by Label")
    st.write("\n\n")
    st.info("This table shows the outcome mix for each label, along with repeat calls, churn and total outcome cost.")
    st.write("\n\n")

    # copy df_grouped to display table
    df_outcome_display = df_grouped.copy()

    # create 'Calls' from 'volume'
    df_outcome_display["Calls"] = df_outcome_display["volume"]

    # rename other columns exactly
    df_outcome_display = df_outcome_display.rename(columns={
        "label": "Label",
        "selected_outcome_cleaned": "Outcome",
        "avg_outcome_cost": "Avg. Outcome Cost (£)",
        "total_outcome_cost": "Total Outcome Cost (£)",
        "repeat_rate_7d": "Repeat Call Rate (7d)",
        "churn_rate_30d": "Churn Rate (30d)",
        "pct_total_volume": "% of Filtered",
        "pct_total_all": "% of All Calls",
        # "churn_rate_60d" remains in df but not displayed
    })

    # select & order columns exactly
    df_outcome_display = df_outcome_display[
        ["Label", "Outcome", "Calls", "Avg. Outcome Cost (£)", "Total Outcome Cost (£)",
         "Repeat Call Rate (7d)", "Churn Rate (30d)", "% of Filtered", "% of All Calls"]
    ]

    # sort by Calls descending
    df_outcome_display = df_outcome_display.sort_values("Calls", ascending=False).reset_index(drop=True)

    # display format
    display_format = {
        "Calls": "{:,}",
        "Avg. Outcome Cost (£)": "£{:,.0f}",
        "Total Outcome Cost (£)": "£{:,.0f}",
        "Repeat Call Rate (7d)": "{:.1%}",
        "Churn Rate (30d)": "{:.1%}",
        "% of Filtered": "{:.1%}",
        "% of All Calls": "{:.1%}",
    }

    # view toggle
    view_mode = st.radio(
        "Choose view:",
        options=["Single table", "Table per call issue label"],
        index=0,
        key="view_mode"
    )
    st.write("\n\n")

    if view_mode == "Single table":
        st.dataframe(
            df_outcome_display.style.format(display_format),
            width='stretch',
            column_config={col: st.column_config.NumberColumn() if col not in ["Label", "Outcome"] else st.column_config.TextColumn() for col in df_outcome_display.columns}
        )
    else:
        ordered_labels = [lbl for lbl in label_order if lbl in df_outcome_display["Label"].unique()]

        for label in ordered_labels:
            with st.expander(label):
                df_label_view = (
                    df_outcome_display[df_outcome_display["Label"] == label]
                    .sort_values("Calls", ascending=False)
                )

                st.dataframe(
                    df_label_view.style.format(display_format),
                    width="stretch",
                    column_config={
                        col: (
                            st.column_config.TextColumn()
                            if col in ["Label", "Outcome"]
                            else st.column_config.NumberColumn()
                        )
                        for col in df_label_view.columns
                    }
                )


    st.caption(f"{df_outcome_display['Calls'].sum():,} calls remaining after global filters applied")
    st.divider()

    ################################
    ### section 3 - risk tiering ###
    ################################

    st.subheader("Risk Tiering by Outcome")
    st.write("\n\n")
    st.info(
        "Assign importance weights to the KPIs below. Percentile-based risk score per outcome grouped "
        "into **Low**, **Medium** and **High** risk tiers. 0% represents the lowest risk outcome and 100% the highest risk outcome."
    )
    st.write("\n\n")

    # -----------------------------
    # Reset callbacks
    # -----------------------------
    def reset_weights():
        st.session_state.weight_repeat = 33
        st.session_state.weight_churn = 33
        st.session_state.weight_cost = 34

    def reset_boundaries():
        st.session_state.low_threshold = 0.33
        st.session_state.med_threshold = 0.66

    # -----------------------------
    # KPI importance sliders
    # -----------------------------
    col1, col2, col3, col4 = st.columns([1, 1, 1, 0.5])
    with col1:
        weight_repeat = st.slider(
            "Repeat call rate (7d) importance:",
            0, 100, st.session_state.get("weight_repeat", 33),
            key="weight_repeat"
        )
    with col2:
        weight_churn = st.slider(
            "Churn rate (30d) importance:",
            0, 100, st.session_state.get("weight_churn", 33),
            key="weight_churn"
        )
    with col3:
        weight_cost = st.slider(
            "Outcome cost importance:",
            0, 100, st.session_state.get("weight_cost", 34),
            key="weight_cost"
        )
    with col4:
        st.button("Reset weights", on_click=reset_weights)

    if weight_repeat + weight_churn + weight_cost != 100:
        st.warning(
            "Weights do not add up to 100. They will be normalised automatically."
        )

    # -----------------------------
    # Risk tier thresholds
    # -----------------------------
    t_col1, t_col2, t_col3 = st.columns([1, 1, 0.5])
    with t_col1:
        low_threshold = st.slider(
            "Low – medium boundary:",
            0.0, 1.0,
            st.session_state.get("low_threshold", 0.33),
            step=0.01,
            key="low_threshold"
        )
    with t_col2:
        med_threshold = st.slider(
            "Medium – high boundary:",
            0.0, 1.0,
            st.session_state.get("med_threshold", 0.66),
            step=0.01,
            key="med_threshold"
        )
    with t_col3:
        st.button("Reset boundaries", on_click=reset_boundaries)

    if low_threshold >= med_threshold:
        st.warning("Low-medium boundary must be lower than medium-high boundary.")
        st.divider()
        st.stop()

    # -----------------------------
    # Normalise weights
    # -----------------------------
    weight_sum = weight_repeat + weight_churn + weight_cost or 1
    w_repeat = weight_repeat / weight_sum
    w_churn = weight_churn / weight_sum
    w_cost = weight_cost / weight_sum

    # -----------------------------
    # Build risk dataframe
    # -----------------------------
    risk_df = df_grouped.copy().rename(columns={
        "label": "Label",
        "selected_outcome_cleaned": "Outcome",
        "repeat_rate_7d": "Repeat Call Rate (7d)",
        "churn_rate_30d": "Churn Rate (30d)",
        "avg_outcome_cost": "Avg. Outcome Cost (£)"
    })

    risk_df["repeat_score"] = risk_df["Repeat Call Rate (7d)"].rank(pct=True)
    risk_df["churn_score"] = risk_df["Churn Rate (30d)"].rank(pct=True)
    risk_df["cost_score"] = risk_df["Avg. Outcome Cost (£)"].rank(pct=True)

    risk_df["risk_score"] = (
        risk_df["repeat_score"] * w_repeat +
        risk_df["churn_score"] * w_churn +
        risk_df["cost_score"] * w_cost
    )

    risk_df["risk_tier"] = pd.cut(
        risk_df["risk_score"],
        bins=[-0.01, low_threshold, med_threshold, 1.01],
        labels=["Low", "Medium", "High"]
    )
    risk_df["risk_pct"] = (risk_df["risk_score"] * 100).round(1)

    tier_color_scale = alt.Scale(
        domain=["Low", "Medium", "High"],
        range=["#2ECC71", "#FFB300", "#E74C3C"]
    )

    # -----------------------------
    # View controls (ALWAYS rendered)
    # -----------------------------
    view_toggle = st.radio(
        "Choose view:",
        options=["All labels", "Single label"],
        index=0,
        key="risk_view_toggle"
    )
    st.write("\n\n")

    single_labels = [lbl for lbl in label_order if lbl in risk_df["Label"].unique()]
    default_label = "Wi-Fi Status"

    selected_label = st.selectbox(
        "Choose label:",
        options=single_labels,
        index=single_labels.index(default_label) if default_label in single_labels else 0,
        disabled=view_toggle != "Single label",
        key="risk_label_select"
    )
    st.write("\n\n")

    # -----------------------------
    # Chart (fixed container + height)
    # -----------------------------
    chart_container = st.container()
    chart_height = 500

    with chart_container:
        if view_toggle == "Single label":
            plot_df = risk_df[risk_df["Label"] == selected_label]

            chart = (
                alt.Chart(plot_df)
                .mark_circle(size=120)
                .encode(
                    x=alt.X("risk_pct:Q", title="Risk score (0–100%)", scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y(
                        "Outcome:N",
                        sort="-x",
                        title=None,
                        axis=alt.Axis(labelLimit=400, labelFontSize=12)
                    ),
                    color=alt.Color("risk_tier:N", title="Risk tier", scale=tier_color_scale),
                    tooltip=[
                        alt.Tooltip("Outcome:N"),
                        alt.Tooltip("risk_pct:Q", format=".1f"),
                        alt.Tooltip("risk_tier:N"),
                        alt.Tooltip("Repeat Call Rate (7d):Q", format=".1%"),
                        alt.Tooltip("Churn Rate (30d):Q", format=".1%"),
                        alt.Tooltip("Avg. Outcome Cost (£):Q")
                    ]
                )
                .properties(height=chart_height)
            )
        else:
            chart = (
                alt.Chart(risk_df)
                .mark_circle(size=120)
                .encode(
                    x=alt.X("risk_pct:Q", title="Risk score (0–100%)", scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y("Label:N", sort=alt.SortArray(label_order), title=None),
                    color=alt.Color("risk_tier:N", title="Risk tier", scale=tier_color_scale),
                    tooltip=[
                        alt.Tooltip("Label:N"),
                        alt.Tooltip("Outcome:N"),
                        alt.Tooltip("risk_pct:Q", format=".1f"),
                        alt.Tooltip("risk_tier:N"),
                        alt.Tooltip("Repeat Call Rate (7d):Q", format=".1%"),
                        alt.Tooltip("Churn Rate (30d):Q", format=".1%"),
                        alt.Tooltip("Avg. Outcome Cost (£):Q")
                    ]
                )
                .properties(height=chart_height)
            )

        st.altair_chart(chart, width="stretch")

    st.divider()
