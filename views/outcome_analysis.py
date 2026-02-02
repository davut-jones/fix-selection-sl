import streamlit as st
import pandas as pd
import altair as alt
from utils.colours import build_global_color_scale

def render_view(df_filtered):

    ########################################
    ### initialization & setup ###
    ########################################

    # page intro text
    st.write("\n\n")
    st.markdown(
        '<span style="font-size: 1.1rem; font-weight: 400;">For each call issue label evaluate selected outcome performance via repeat calls and BB churn</span>',
        unsafe_allow_html=True
    )
    st.divider()

    # build colour scale
    all_outcomes = st.session_state["global_outcomes"]
    color_scale = build_global_color_scale(all_outcomes)

    # persist view mode across reruns
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "Single table"

    # ensure numeric types before calculations
    df_working = df_filtered.copy()
    df_working["outcome_cost"] = pd.to_numeric(df_working["outcome_cost"], errors="coerce")
    df_working["sc_call_next_7d_flag"] = pd.to_numeric(df_working["sc_call_next_7d_flag"], errors="coerce")
    df_working["bb_churn_next_30d"] = pd.to_numeric(df_working["bb_churn_next_30d"], errors="coerce")
    df_working["bb_churn_next_60d"] = pd.to_numeric(df_working["bb_churn_next_60d"], errors="coerce")

    ########################################
    ### section 1 - outcome distribution ###
    ########################################

    # section title
    st.subheader("Outcome Distribution by Label")

    # info box
    st.write("\n\n")
    st.info("Each bar totals 100% after filtering and shows the outcome mix within each label for those selected.")
    st.write("\n\n")

    # aggregate outcomes by label
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

    # calculate percentages
    df_grouped["pct_total_volume"] = df_grouped["volume"] / df_grouped["volume"].sum()
    total_all = st.session_state.get("df_label_total_rows", len(df_working))
    df_grouped["pct_total_all"] = df_grouped["volume"] / total_all

    # prepare data for charting
    chart_df = df_grouped.copy()
    chart_df["pct_within_label"] = chart_df.groupby("label")["volume"].transform(lambda x: x / x.sum() * 100)

    label_order = [
        "Wi-Fi Status", "Unreliable Wi-Fi", "Slow Wi-Fi",
        "Poor Coverage", "Other", "Unclear"
    ]

    # build outcome distribution chart
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

    # section title
    st.subheader("Outcome Breakdown by Label")

    # info box
    st.write("\n\n")
    st.info("This table shows the outcome mix for each label, along with repeat calls, BB churn and total outcome cost.")
    st.write("\n\n")

    # prepare data for display
    df_outcome_display = df_grouped.copy()
    df_outcome_display["Calls"] = df_outcome_display["volume"]

    # rename columns for display
    df_outcome_display = df_outcome_display.rename(columns={
        "label": "Label",
        "selected_outcome_cleaned": "Outcome",
        "avg_outcome_cost": "Avg. Outcome Cost (£)",
        "total_outcome_cost": "Total Outcome Cost (£)",
        "repeat_rate_7d": "Repeat Call Rate (7d)",
        "churn_rate_30d": "BB Churn Rate (30d)",
        "pct_total_volume": "% of Filtered",
        "pct_total_all": "% of All Calls",
        # "churn_rate_60d" remains in df but not displayed
    })

    # select and order columns for display
    df_outcome_display = df_outcome_display[
        ["Label", "Outcome", "Calls", "Avg. Outcome Cost (£)", "Total Outcome Cost (£)",
         "Repeat Call Rate (7d)", "BB Churn Rate (30d)", "% of Filtered", "% of All Calls"]
    ]

    # sort outcomes by call volume
    df_outcome_display = df_outcome_display.sort_values("Calls", ascending=False).reset_index(drop=True)

    # define display formatting
    display_format = {
        "Calls": "{:,}",
        "Avg. Outcome Cost (£)": "£{:,.0f}",
        "Total Outcome Cost (£)": "£{:,.0f}",
        "Repeat Call Rate (7d)": "{:.1%}",
        "BB Churn Rate (30d)": "{:.1%}",
        "% of Filtered": "{:.1%}",
        "% of All Calls": "{:.1%}",
    }

    # view mode toggle
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

    # section title
    st.subheader("Risk Tiering by Outcome")

    # info box
    st.write("\n\n")
    st.info(
        "Outcomes ranked across three risk metrics: Repeat Call Rate (7d), BB Churn (30d), and Cost. Risk scores are calculated across all outcomes and labels. Adjust metric importance and tier boundaries to refine tiers."
    )
    st.write("\n\n")

    # define reset callbacks
    def reset_weights():
        st.session_state.weight_repeat = 33
        st.session_state.weight_churn = 33
        st.session_state.weight_cost = 34

    def reset_boundaries():
        st.session_state.low_threshold = 33
        st.session_state.med_threshold = 66

    # pre-calculate scores for boundary reference (before expander)
    temp_risk_df = df_grouped.copy().rename(columns={
        "label": "Label",
        "selected_outcome_cleaned": "Outcome",
        "repeat_rate_7d": "Repeat Call Rate (7d)",
        "churn_rate_30d": "BB Churn Rate (30d)",
        "avg_outcome_cost": "Avg. Outcome Cost (£)"
    })
    temp_risk_df["repeat_pct"] = (temp_risk_df["Repeat Call Rate (7d)"].rank(pct=True) * 100).round(1)
    temp_risk_df["churn_pct"] = (temp_risk_df["BB Churn Rate (30d)"].rank(pct=True) * 100).round(1)
    temp_risk_df["cost_pct"] = (temp_risk_df["Avg. Outcome Cost (£)"].rank(pct=True) * 100).round(1)

    # configure metric weights and boundaries
    # user can adjust importance of each metric and set tier thresholds
    with st.expander("Configure boundaries & weights", expanded=False):
        
        # initialize session state for boundaries if not already set
        if "low_threshold" not in st.session_state:
            st.session_state.low_threshold = 33
        if "med_threshold" not in st.session_state:
            st.session_state.med_threshold = 66
        
        st.markdown("#### Risk Tier Boundaries")
        st.caption("Set the score thresholds that define Low, Medium, and High risk tiers")
        st.write("")
        
        # tier boundary sliders (0-100 score scale)
        t_col1, t_col2, t_col3 = st.columns([1, 1, 0.5])
        with t_col1:
            low_threshold = st.slider(
                "Low – medium risk boundary:",
                0, 100,
                key="low_threshold",
                step=1,
                format="%d"
            )
        
        with t_col2:
            med_threshold = st.slider(
                "Medium – high risk boundary:",
                0, 100,
                key="med_threshold",
                step=1,
                format="%d"
            )
        
        with t_col3:
            st.button("Reset boundaries", on_click=reset_boundaries, key="reset_boundaries_btn")

        if low_threshold >= med_threshold:
            st.error("Low-medium boundary must be lower than medium-high boundary.")
            st.stop()

        # display metric ranges at boundaries with stacked bars
        st.write("")
        
        # use session state values directly to ensure they update
        low_threshold_val = st.session_state.low_threshold
        med_threshold_val = st.session_state.med_threshold
        
        low_tier_repeat = temp_risk_df[temp_risk_df["repeat_pct"] <= low_threshold_val]["Repeat Call Rate (7d)"].max()
        low_tier_churn = temp_risk_df[temp_risk_df["churn_pct"] <= low_threshold_val]["BB Churn Rate (30d)"].max()
        low_tier_cost = temp_risk_df[temp_risk_df["cost_pct"] <= low_threshold_val]["Avg. Outcome Cost (£)"].max()
        
        med_tier_repeat = temp_risk_df[temp_risk_df["repeat_pct"] <= med_threshold_val]["Repeat Call Rate (7d)"].max()
        med_tier_churn = temp_risk_df[temp_risk_df["churn_pct"] <= med_threshold_val]["BB Churn Rate (30d)"].max()
        med_tier_cost = temp_risk_df[temp_risk_df["cost_pct"] <= med_threshold_val]["Avg. Outcome Cost (£)"].max()
        
        # get min and max values for each metric
        min_repeat = temp_risk_df["Repeat Call Rate (7d)"].min()
        max_repeat = temp_risk_df["Repeat Call Rate (7d)"].max()
        min_churn = temp_risk_df["BB Churn Rate (30d)"].min()
        max_churn = temp_risk_df["BB Churn Rate (30d)"].max()
        min_cost = temp_risk_df["Avg. Outcome Cost (£)"].min()
        max_cost = temp_risk_df["Avg. Outcome Cost (£)"].max()
        
        boundary_display = (
            f'<div style="background-color: #f9f9f9; padding: 16px 20px 12px 20px; border-radius: 8px; border: 1px solid #e0e0e0;">'
            f'<div style="font-size: 14px; font-weight: 600; color: #333; margin-bottom: 8px;">Current Risk Boundaries:</div>'
            f'<div style="margin-bottom: 12px;"><div style="font-size: 13px; color: #555; margin-bottom: 4px;">Repeat Call Rate (7d)</div>'
            f'<div style="position: relative; height: 28px;"><div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; background-color: #e0e0e0;"><div style="background-color: #4d9e4d; width: {low_threshold_val}%; flex-shrink: 0;"></div><div style="background-color: #f8953e; width: {med_threshold_val - low_threshold_val}%; flex-shrink: 0;"></div><div style="background-color: #d44646; width: {100 - med_threshold_val}%; flex-shrink: 0;"></div></div>'
            f'<span style="position: absolute; left: 0%; top: 14px; text-align: left; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{min_repeat:.1%}</span>'
            f'<span style="position: absolute; left: {low_threshold_val}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{low_tier_repeat:.1%}</span>'
            f'<span style="position: absolute; left: {med_threshold_val}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{med_tier_repeat:.1%}</span>'
            f'<span style="position: absolute; right: 0%; top: 14px; text-align: right; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{max_repeat:.1%}</span></div></div>'
            f'<div style="margin-bottom: 12px;"><div style="font-size: 13px; color: #555; margin-bottom: 4px;">BB Churn Rate (30d)</div>'
            f'<div style="position: relative; height: 28px;"><div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; background-color: #e0e0e0;"><div style="background-color: #4d9e4d; width: {low_threshold_val}%; flex-shrink: 0;"></div><div style="background-color: #f8953e; width: {med_threshold_val - low_threshold_val}%; flex-shrink: 0;"></div><div style="background-color: #d44646; width: {100 - med_threshold_val}%; flex-shrink: 0;"></div></div>'
            f'<span style="position: absolute; left: 0%; top: 14px; text-align: left; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{min_churn:.1%}</span>'
            f'<span style="position: absolute; left: {low_threshold_val}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{low_tier_churn:.1%}</span>'
            f'<span style="position: absolute; left: {med_threshold_val}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{med_tier_churn:.1%}</span>'
            f'<span style="position: absolute; right: 0%; top: 14px; text-align: right; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{max_churn:.1%}</span></div></div>'
            f'<div><div style="font-size: 13px; color: #555; margin-bottom: 4px;">Avg. Outcome Cost (£)</div>'
            f'<div style="position: relative; height: 28px;"><div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; background-color: #e0e0e0;"><div style="background-color: #4d9e4d; width: {low_threshold_val}%; flex-shrink: 0;"></div><div style="background-color: #f8953e; width: {med_threshold_val - low_threshold_val}%; flex-shrink: 0;"></div><div style="background-color: #d44646; width: {100 - med_threshold_val}%; flex-shrink: 0;"></div></div>'
            f'<span style="position: absolute; left: 0%; top: 14px; text-align: left; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">£{min_cost:.0f}</span>'
            f'<span style="position: absolute; left: {low_threshold_val}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">£{low_tier_cost:.0f}</span>'
            f'<span style="position: absolute; left: {med_threshold_val}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">£{med_tier_cost:.0f}</span>'
            f'<span style="position: absolute; right: 0%; top: 14px; text-align: right; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">£{max_cost:.0f}</span></div></div>'
            f'<div style="font-size: 11px; color: #999; margin-top: 8px; font-style: italic;">Green = Low risk | Amber = Medium risk | Red = High risk</div></div>'
        )
        
        st.markdown(boundary_display, unsafe_allow_html=True)
        
        st.write("\n\n")
        
        st.markdown("#### Metric Importance Weights")
        st.caption("Adjust how much each metric contributes to the overall risk score")
        st.write("")
        
        # initialize session state for weights if not already set
        if "weight_repeat" not in st.session_state:
            st.session_state.weight_repeat = 33
        if "weight_churn" not in st.session_state:
            st.session_state.weight_churn = 33
        if "weight_cost" not in st.session_state:
            st.session_state.weight_cost = 34
        
        # weight sliders
        col1, col2, col3, col4 = st.columns([1, 1, 1, 0.5])
        with col1:
            weight_repeat = st.slider(
                "Repeat call rate importance:",
                0, 100,
                key="weight_repeat"
            )
        with col2:
            weight_churn = st.slider(
                "BB Churn rate importance:",
                0, 100,
                key="weight_churn"
            )
        with col3:
            weight_cost = st.slider(
                "Outcome cost importance:",
                0, 100,
                key="weight_cost"
            )
        with col4:
            st.button("Reset weights", on_click=reset_weights, key="reset_weights_btn")

        if weight_repeat + weight_churn + weight_cost != 100:
            st.caption("⚠️ Weights will be normalised automatically to sum to 100%")
        
        # calculate normalised weights for display
        weight_sum = weight_repeat + weight_churn + weight_cost or 1
        w_repeat_norm = (weight_repeat / weight_sum) * 100
        w_churn_norm = (weight_churn / weight_sum) * 100
        w_cost_norm = (weight_cost / weight_sum) * 100
        
        st.write("")
        st.markdown(
            f'<div style="background-color: #f9f9f9; padding: 16px; border-radius: 8px; border: 1px solid #e0e0e0;">'
            f'<div style="font-size: 14px; font-weight: 600; color: #333; margin-bottom: 10px;">Current Weight Distribution:</div>'
            f'<div style="margin-bottom: 8px;">'
            f'  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">'
            f'    <span style="font-size: 13px; color: #555;">Repeat Call Rate (7d)</span>'
            f'    <span style="font-size: 13px; font-weight: 600; color: #ff7f0e;">{w_repeat_norm:.1f}%</span>'
            f'  </div>'
            f'  <div style="background-color: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">'
            f'    <div style="background-color: #ff7f0e; height: 100%; width: {w_repeat_norm}%;"></div>'
            f'  </div>'
            f'</div>'
            f'<div style="margin-bottom: 8px;">'
            f'  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">'
            f'    <span style="font-size: 13px; color: #555;">BB Churn Rate (30d)</span>'
            f'    <span style="font-size: 13px; font-weight: 600; color: #d62728;">{w_churn_norm:.1f}%</span>'
            f'  </div>'
            f'  <div style="background-color: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">'
            f'    <div style="background-color: #d62728; height: 100%; width: {w_churn_norm}%;"></div>'
            f'  </div>'
            f'</div>'
            f'<div style="margin-bottom: 4px;">'
            f'  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">'
            f'    <span style="font-size: 13px; color: #555;">Avg. Outcome Cost (£)</span>'
            f'    <span style="font-size: 13px; font-weight: 600; color: #9467bd;">{w_cost_norm:.1f}%</span>'
            f'  </div>'
            f'  <div style="background-color: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">'
            f'    <div style="background-color: #9467bd; height: 100%; width: {w_cost_norm}%;"></div>'
            f'  </div>'
            f'</div>'
            f'<div style="font-size: 12px; color: #777; margin-top: 12px; font-style: italic;">'
            f'Overall Risk Score = ({w_repeat_norm:.1f}% × Repeat Score) + ({w_churn_norm:.1f}% × Churn Score) + ({w_cost_norm:.1f}% × Cost Score)'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        st.write("\n\n")

    # normalize weights to sum to 100%
    weight_sum = weight_repeat + weight_churn + weight_cost or 1
    w_repeat = weight_repeat / weight_sum
    w_churn = weight_churn / weight_sum
    w_cost = weight_cost / weight_sum

    # build risk dataframe with scoring
    risk_df = df_grouped.copy().rename(columns={
        "label": "Label",
        "selected_outcome_cleaned": "Outcome",
        "repeat_rate_7d": "Repeat Call Rate (7d)",
        "churn_rate_30d": "BB Churn Rate (30d)",
        "avg_outcome_cost": "Avg. Outcome Cost (£)"
    })

    # calculate percentile scores for each metric
    risk_df["repeat_score"] = risk_df["Repeat Call Rate (7d)"].rank(pct=True)
    risk_df["churn_score"] = risk_df["BB Churn Rate (30d)"].rank(pct=True)
    risk_df["cost_score"] = risk_df["Avg. Outcome Cost (£)"].rank(pct=True)

    # calculate weighted overall risk score
    risk_df["risk_score"] = (
        risk_df["repeat_score"] * w_repeat +
        risk_df["churn_score"] * w_churn +
        risk_df["cost_score"] * w_cost
    )

    # convert scores to percentage format (0-100 scale)
    risk_df["risk_pct"] = (risk_df["risk_score"] * 100).round(1)
    risk_df["repeat_pct"] = (risk_df["repeat_score"] * 100).round(1)
    risk_df["churn_pct"] = (risk_df["churn_score"] * 100).round(1)
    risk_df["cost_pct"] = (risk_df["cost_score"] * 100).round(1)

    # categorize overall risk into tiers (using 0-100 score scale)
    risk_df["risk_tier"] = pd.cut(
        risk_df["risk_pct"],
        bins=[0, low_threshold, med_threshold, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )

    # categorize individual metrics into tiers (using 0-100 score scale)
    risk_df["repeat_tier"] = pd.cut(
        risk_df["repeat_pct"],
        bins=[0, low_threshold, med_threshold, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )
    risk_df["churn_tier"] = pd.cut(
        risk_df["churn_pct"],
        bins=[0, low_threshold, med_threshold, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )
    risk_df["cost_tier"] = pd.cut(
        risk_df["cost_pct"],
        bins=[0, low_threshold, med_threshold, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )

    # define color palette for risk tiers
    # tier_color_map = {
    #     "Low": "#98df8a",
    #     "Medium": "#ffbb78",
    #     "High": "#ff9896"
    # }
    tier_color_map = {
        "Low": "#4d9e4d",
        "Medium": "#f8953e",
        "High": "#d44646"
    }

    st.write("\n\n")

    # label filter and selection
    label_order = [
        "Wi-Fi Status", "Unreliable Wi-Fi", "Slow Wi-Fi",
        "Poor Coverage", "Other", "Unclear"
    ]

    single_labels = [lbl for lbl in label_order if lbl in risk_df["Label"].unique()]
    default_label = "Wi-Fi Status" if "Wi-Fi Status" in single_labels else single_labels[0]

    # label selectbox
    selected_label = st.selectbox(
        "Select a call issue label:",
        options=single_labels,
        index=single_labels.index(default_label) if default_label in single_labels else 0,
        key="risk_label_select"
    )
    st.write("")

    # risk tier legend
    # centered display with color indicators
    legend_html = '<div style="display: flex; justify-content: center; gap: 32px; margin-bottom: 16px; font-size: 16px; align-items: center; font-weight: 600;">'
    legend_html += '<div style="display: flex; align-items: center; gap: 8px;"><div style="width: 16px; height: 16px; background-color: #4d9e4d; border-radius: 2px;"></div><span>Low risk</span></div>'
    legend_html += '<div style="display: flex; align-items: center; gap: 8px;"><div style="width: 16px; height: 16px; background-color: #f8953e; border-radius: 2px;"></div><span>Medium risk</span></div>'
    legend_html += '<div style="display: flex; align-items: center; gap: 8px;"><div style="width: 16px; height: 16px; background-color: #d44646; border-radius: 2px;"></div><span>High risk</span></div>'
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)
    st.write("")

    # filter risk data by selected label
    display_df = risk_df[risk_df["Label"] == selected_label].sort_values("risk_pct", ascending=False)

    # display metric ranges at boundaries
    st.write("")

    # display column headers
    col_header_outcome, col_header_cards, col_header_overall = st.columns([1, 2.2, 0.65], gap="small")
    with col_header_cards:
        header_cols = st.columns(3, gap="small")
        with header_cols[0]:
            st.markdown('<div style="font-size: 16px; font-weight: 700; text-align: center; color: #333;">Repeat Call Risk Score | Actual<br><span style="font-size: 11px; opacity: 0.8;"></div>', unsafe_allow_html=True)
        with header_cols[1]:
            st.markdown('<div style="font-size: 16px; font-weight: 700; text-align: center; color: #333;">BB Churn Risk Score | Actual<br><span style="font-size: 11px; opacity: 0.8;"></div>', unsafe_allow_html=True)
        with header_cols[2]:
            st.markdown('<div style="font-size: 16px; font-weight: 700; text-align: center; color: #333;">Cost Risk Score | Actual<br><span style="font-size: 11px; opacity: 0.8;"></div>', unsafe_allow_html=True)
    with col_header_overall:
        st.markdown('<div style="font-size: 16px; font-weight: 700; text-align: center; color: #333;">Overall Risk Score</div>', unsafe_allow_html=True)
    st.write("")

    # render outcome risk cards
    # format call counts with 'k' notation for 4+ digits
    def format_calls(volume):
        if volume >= 1000:
            return f"{volume/1000:.1f}k"
        else:
            return str(int(volume))
    
    # iterate through outcomes and render risk cards
    for idx, row in display_df.iterrows():
        col_outcome, col_cards, col_overall = st.columns([1, 2.2, 0.65], gap="small", vertical_alignment="center")
        
        with col_outcome:
            call_count = format_calls(row['volume'])
            st.markdown(f"<div style='font-size: 16px;'><b>{row['Outcome']}</b> ({call_count} calls)</div>", unsafe_allow_html=True)
        
        with col_cards:
            card_cols = st.columns(3, gap="small", vertical_alignment="center")
            
            # repeat call risk card
            with card_cols[0]:
                repeat_color = tier_color_map[row["repeat_tier"]]
                st.markdown(
                    f'<div style="background-color: {repeat_color}; padding: 6px 4px; border-radius: 4px; text-align: center; color: white; height: 100%; display: flex; align-items: center; justify-content: center;">'
                    f'<div style="font-size: 16px; font-weight: 700; line-height: 1.3;">{row["repeat_pct"]:.0f} <span style="font-weight: 400;">| {row["Repeat Call Rate (7d)"]:.1%}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            # churn risk card
            with card_cols[1]:
                churn_color = tier_color_map[row["churn_tier"]]
                st.markdown(
                    f'<div style="background-color: {churn_color}; padding: 6px 4px; border-radius: 4px; text-align: center; color: white; height: 100%; display: flex; align-items: center; justify-content: center;">'
                    f'<div style="font-size: 16px; font-weight: 700; line-height: 1.3;">{row["churn_pct"]:.0f} <span style="font-weight: 400;">| {row["BB Churn Rate (30d)"]:.1%}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            # cost risk card
            with card_cols[2]:
                cost_color = tier_color_map[row["cost_tier"]]
                st.markdown(
                    f'<div style="background-color: {cost_color}; padding: 6px 4px; border-radius: 4px; text-align: center; color: white; height: 100%; display: flex; align-items: center; justify-content: center;">'
                    f'<div style="font-size: 16px; font-weight: 700; line-height: 1.3;">{row["cost_pct"]:.0f} <span style="font-weight: 400;">| £{row["Avg. Outcome Cost (£)"]:.0f}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            # overall risk card
            with col_overall:
                overall_color = tier_color_map[row["risk_tier"]]
                asterisk = "*" if row["volume"] < 250 else ""
                st.markdown(
                    f'<div style="background-color: {overall_color}; padding: 6px 4px; border-radius: 4px; text-align: center; color: white; border: 2px solid #333; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;">'
                    f'<div style="font-size: 16px; font-weight: 700; line-height: 1.2;">{row["risk_pct"]:.0f}{asterisk}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        
        st.markdown("<div style='margin: 0px 0;'></div>", unsafe_allow_html=True)

    # footnote for small sample sizes
    # displayed when outcomes have fewer than 250 calls
    if (display_df["volume"] < 250).any():
        st.markdown(
            "<div style='text-align: right; font-size: 12px; opacity: 0.7; margin-top: 8px;'>"
            "<span style='color: #666;'>* Small sample size (less than 250 calls) — use with caution</span>"
            "</div>",
            unsafe_allow_html=True
        )

    # export risk scores to csv
    export_df = display_df[[
        "Outcome", "volume", 
        "Repeat Call Rate (7d)", "repeat_pct", "repeat_tier", 
        "BB Churn Rate (30d)", "churn_pct", "churn_tier", 
        "Avg. Outcome Cost (£)", "cost_pct", "cost_tier", 
        "risk_pct", "risk_tier"
    ]].copy()
    
    export_df = export_df.rename(columns={
        "Outcome": "Outcome",
        "volume": "Call Volume",
        "Repeat Call Rate (7d)": "Repeat Call Rate",
        "repeat_pct": "Repeat Call Risk Score",
        "repeat_tier": "Repeat Call Risk Tier",
        "BB Churn Rate (30d)": "BB Churn Rate",
        "churn_pct": "BB Churn Risk Score",
        "churn_tier": "BB Churn Risk Tier",
        "Avg. Outcome Cost (£)": "Avg. Outcome Cost",
        "cost_pct": "Cost Risk Score",
        "cost_tier": "Cost Risk Tier",
        "risk_pct": "Overall Risk Score",
        "risk_tier": "Overall Risk Tier"
    })
    
    csv_data = export_df.to_csv(index=False)
    st.write("\n\n")
    st.download_button(
        label="Export Risk Scores",
        data=csv_data,
        file_name=f"risk_scores_{selected_label.lower().replace(' ', '_')}.csv",
        mime="text/csv"
    )

    st.divider()