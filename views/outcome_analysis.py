import streamlit as st
import pandas as pd
import altair as alt
from utils.colours import build_global_color_scale
import numpy as np

def render_view(df_filtered):

    ##############################
    ### initialization & setup ###
    ##############################

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

    ########################################
    ### section 1 - outcome distribution ###
    ########################################

    # section title
    st.subheader("Selected Outcome Distribution by Label")

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
    st.subheader("Selected Outcome Breakdown by Label")

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
    st.subheader("Risk Tiering by Selected Outcome")

    # info box
    st.write("\n\n")
    st.info(
        "Outcomes ranked across three risk metrics: Repeat Call Rate (7d), BB Churn (30d), and Cost. Risk scores are calculated across all outcomes and labels. Adjust tier boundaries and metric weights to refine tiers."
    )
    st.write("\n\n")

    # apply confidence filter for this section
    # get confidence value from session state (will be set by slider widget below)
    min_confidence = st.session_state.get("outcome_analysis_confidence", 1)
    
    # filter data by confidence and recalculate grouped data for risk analysis
    df_working_risk = df_working.copy()
    df_working_risk["confidence"] = df_working_risk["confidence"].fillna(1)
    df_working_risk = df_working_risk[df_working_risk["confidence"] >= min_confidence]
    
    # calculate suggested indicator (where selected == suggested)
    df_working_risk["is_suggested"] = (
        df_working_risk["selected_outcome_cleaned"] == df_working_risk["suggested_outcome_cleaned"]
    ).astype(int)
    
    # recalculate grouped data with confidence filter applied
    df_grouped_risk = (
        df_working_risk.groupby(["label", "selected_outcome_cleaned"])
        .agg(
            volume=("selected_outcome_cleaned", "size"),
            repeat_rate_7d=("sc_call_next_7d_flag", "mean"),
            churn_rate_30d=("bb_churn_next_30d", "mean"),
            avg_outcome_cost=("outcome_cost", "mean"),
            total_outcome_cost=("outcome_cost", "sum"),
            suggested_rate=("is_suggested", "mean"),
        )
        .reset_index()
    )

    # define reset callbacks
    def reset_weights():
        st.session_state.weight_repeat = 33
        st.session_state.weight_churn = 33
        st.session_state.weight_cost = 34

    def reset_boundaries():
        st.session_state.low_threshold = 33
        st.session_state.med_threshold = 66

    # pre-calculate scores for boundary reference (before expander)
    temp_risk_df = df_grouped_risk.copy().rename(columns={
        "label": "Label",
        "selected_outcome_cleaned": "Outcome",
        "repeat_rate_7d": "Repeat Call Rate (7d)",
        "churn_rate_30d": "BB Churn Rate (30d)",
        "avg_outcome_cost": "Avg. Outcome Cost (£)"
    })
    
    # define percent_rank function for temp dataframe
    def percent_rank_temp(series):
        ranks = series.rank(method="min")
        n = len(series)
        if n == 1:
            return pd.Series([0.0], index=series.index)
        return (ranks - 1) / (n - 1)
    
    temp_risk_df["repeat_pct"] = (100 * percent_rank_temp(temp_risk_df["Repeat Call Rate (7d)"])).round(0)
    temp_risk_df["churn_pct"] = (100 * percent_rank_temp(temp_risk_df["BB Churn Rate (30d)"])).round(0)
    temp_risk_df["cost_pct"] = (100 * percent_rank_temp(temp_risk_df["Avg. Outcome Cost (£)"])).round(0)

    # configure metric weights and boundaries
    # user can adjust importance of each metric and set tier thresholds
    with st.expander("Configure boundaries & weights", expanded=False):
        
        # initialize session state for metric-specific boundaries
        if "repeat_low" not in st.session_state:
            st.session_state.repeat_low = 33
        if "repeat_med" not in st.session_state:
            st.session_state.repeat_med = 66
        if "churn_low" not in st.session_state:
            st.session_state.churn_low = 33
        if "churn_med" not in st.session_state:
            st.session_state.churn_med = 66
        if "cost_low" not in st.session_state:
            st.session_state.cost_low = 33
        if "cost_med" not in st.session_state:
            st.session_state.cost_med = 66
        
        st.markdown("#### Risk Tier Boundaries")
        st.caption("Set the thresholds for each metric that define **low**, **medium**, and **high** risk tiers")
        st.write("")
        
        # Define reset function for all boundaries
        def reset_all_boundaries():
            st.session_state.repeat_low = 33
            st.session_state.repeat_med = 66
            st.session_state.churn_low = 33
            st.session_state.churn_med = 66
            st.session_state.cost_low = 33
            st.session_state.cost_med = 66
        
        # All 6 sliders on one line with reset button and padding between pairs
        slider_cols = st.columns([0.2, 1, 1, 0.2, 1, 1, 0.2, 1, 1, 0.2, 0.8, 0.2])
        
        with slider_cols[1]:
            repeat_low = st.slider("**Repeat Call Rate** - Low -> Med:", 0, 100, key="repeat_low", step=1, format="%d")
        
        with slider_cols[2]:
            repeat_med = st.slider("**Repeat Call Rate** - Med -> High", 0, 100, key="repeat_med", step=1, format="%d")
        
        with slider_cols[4]:
            churn_low = st.slider("**BB Churn Rate** - Low -> Med", 0, 100, key="churn_low", step=1, format="%d")
        
        with slider_cols[5]:
            churn_med = st.slider("**BB Churn Rate** - Med -> High", 0, 100, key="churn_med", step=1, format="%d")
        
        with slider_cols[7]:
            cost_low = st.slider("**Outcome Cost** - Low -> Med", 0, 100, key="cost_low", step=1, format="%d")
        
        with slider_cols[8]:
            cost_med = st.slider("**Outcome Cost** - Med -> High", 0, 100, key="cost_med", step=1, format="%d")
        
        with slider_cols[10]:
            st.button("Reset boundaries", on_click=reset_all_boundaries, key="reset_all_btn")
        
        # Validation checks with full metric names
        if repeat_low >= repeat_med:
            st.error("Repeat Call Rate (7d): Low-Med boundary must be lower than Med-High boundary.")
            st.stop()
        
        if churn_low >= churn_med:
            st.error("BB Churn Rate (30d): Low-Med boundary must be lower than Med-High boundary.")
            st.stop()
        
        if cost_low >= cost_med:
            st.error("Avg. Outcome Cost (£): Low-Med boundary must be lower than Med-High boundary.")
            st.stop()
        
        st.write("")
        
        # extract session state values
        repeat_low_val = st.session_state.repeat_low
        repeat_med_val = st.session_state.repeat_med
        churn_low_val = st.session_state.churn_low
        churn_med_val = st.session_state.churn_med
        cost_low_val = st.session_state.cost_low
        cost_med_val = st.session_state.cost_med
        
        # calculate tier values for each metric using metric-specific boundaries
        repeat_low_tier = temp_risk_df[temp_risk_df["repeat_pct"] <= repeat_low_val]["Repeat Call Rate (7d)"].max()
        repeat_med_tier = temp_risk_df[temp_risk_df["repeat_pct"] <= repeat_med_val]["Repeat Call Rate (7d)"].max()
        
        churn_low_tier = temp_risk_df[temp_risk_df["churn_pct"] <= churn_low_val]["BB Churn Rate (30d)"].max()
        churn_med_tier = temp_risk_df[temp_risk_df["churn_pct"] <= churn_med_val]["BB Churn Rate (30d)"].max()
        
        cost_low_tier = temp_risk_df[temp_risk_df["cost_pct"] <= cost_low_val]["Avg. Outcome Cost (£)"].max()
        cost_med_tier = temp_risk_df[temp_risk_df["cost_pct"] <= cost_med_val]["Avg. Outcome Cost (£)"].max()
        
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
            f'<div style="position: relative; height: 28px;"><div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; background-color: #e0e0e0;"><div style="background-color: #4d9e4d; width: {repeat_low_val}%; flex-shrink: 0;"></div><div style="background-color: #f8953e; width: {repeat_med_val - repeat_low_val}%; flex-shrink: 0;"></div><div style="background-color: #d44646; width: {100 - repeat_med_val}%; flex-shrink: 0;"></div></div>'
            f'<span style="position: absolute; left: 0%; top: 14px; text-align: left; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{min_repeat:.1%}</span>'
            f'<span style="position: absolute; left: {repeat_low_val}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{repeat_low_tier:.1%}</span>'
            f'<span style="position: absolute; left: {repeat_med_val}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{repeat_med_tier:.1%}</span>'
            f'<span style="position: absolute; right: 0%; top: 14px; text-align: right; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{max_repeat:.1%}</span></div></div>'
            f'<div style="margin-bottom: 12px;"><div style="font-size: 13px; color: #555; margin-bottom: 4px;">BB Churn Rate (30d)</div>'
            f'<div style="position: relative; height: 28px;"><div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; background-color: #e0e0e0;"><div style="background-color: #4d9e4d; width: {churn_low_val}%; flex-shrink: 0;"></div><div style="background-color: #f8953e; width: {churn_med_val - churn_low_val}%; flex-shrink: 0;"></div><div style="background-color: #d44646; width: {100 - churn_med_val}%; flex-shrink: 0;"></div></div>'
            f'<span style="position: absolute; left: 0%; top: 14px; text-align: left; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{min_churn:.1%}</span>'
            f'<span style="position: absolute; left: {churn_low_val}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{churn_low_tier:.1%}</span>'
            f'<span style="position: absolute; left: {churn_med_val}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{churn_med_tier:.1%}</span>'
            f'<span style="position: absolute; right: 0%; top: 14px; text-align: right; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{max_churn:.1%}</span></div></div>'
            f'<div><div style="font-size: 13px; color: #555; margin-bottom: 4px;">Avg. Outcome Cost (£)</div>'
            f'<div style="position: relative; height: 28px;"><div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; background-color: #e0e0e0;"><div style="background-color: #4d9e4d; width: {cost_low_val}%; flex-shrink: 0;"></div><div style="background-color: #f8953e; width: {cost_med_val - cost_low_val}%; flex-shrink: 0;"></div><div style="background-color: #d44646; width: {100 - cost_med_val}%; flex-shrink: 0;"></div></div>'
            f'<span style="position: absolute; left: 0%; top: 14px; text-align: left; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">£{min_cost:.0f}</span>'
            f'<span style="position: absolute; left: {cost_low_val}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">£{cost_low_tier:.0f}</span>'
            f'<span style="position: absolute; left: {cost_med_val}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">£{cost_med_tier:.0f}</span>'
            f'<span style="position: absolute; right: 0%; top: 14px; text-align: right; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">£{max_cost:.0f}</span></div></div>'
            f'<div style="font-size: 10px; color: #999; margin-top: 8px; font-style: italic;">Green = Low risk | Amber = Medium risk | Red = High risk</div></div>'
        )
        
        st.markdown(boundary_display, unsafe_allow_html=True)
        
        st.write("\n\n")
        
        st.markdown("#### Metric Importance Weights")
        st.caption("Adjust how much each metric contributes to the **overall risk score and combined boundaries**")
        st.write("")
        
        # initialize session state for weights if not already set
        if "weight_repeat" not in st.session_state:
            st.session_state.weight_repeat = 33
        if "weight_churn" not in st.session_state:
            st.session_state.weight_churn = 33
        if "weight_cost" not in st.session_state:
            st.session_state.weight_cost = 34
        
        # weight sliders with spacing
        weight_cols = st.columns([0.2, 1, 0.2, 1, 0.2, 1, 0.2, 0.6])
        with weight_cols[1]:
            weight_repeat = st.slider(
                "**Repeat Call Rate** - importance:",
                0, 100,
                key="weight_repeat"
            )
        with weight_cols[3]:
            weight_churn = st.slider(
                "**BB Churn Rate** - importance:",
                0, 100,
                key="weight_churn"
            )
        with weight_cols[5]:
            weight_cost = st.slider(
                "**Outcome Cost** - importance:",
                0, 100,
                key="weight_cost"
            )
        with weight_cols[7]:
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
            f'    <span style="font-size: 13px; font-weight: 600; color: #ff7f0e;">{w_repeat_norm:.0f}%</span>'
            f'  </div>'
            f'  <div style="background-color: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">'
            f'    <div style="background-color: #ff7f0e; height: 100%; width: {w_repeat_norm}%;"></div>'
            f'  </div>'
            f'</div>'
            f'<div style="margin-bottom: 8px;">'
            f'  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">'
            f'    <span style="font-size: 13px; color: #555;">BB Churn Rate (30d)</span>'
            f'    <span style="font-size: 13px; font-weight: 600; color: #d62728;">{w_churn_norm:.0f}%</span>'
            f'  </div>'
            f'  <div style="background-color: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">'
            f'    <div style="background-color: #d62728; height: 100%; width: {w_churn_norm}%;"></div>'
            f'  </div>'
            f'</div>'
            f'<div style="margin-bottom: 4px;">'
            f'  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">'
            f'    <span style="font-size: 13px; color: #555;">Avg. Outcome Cost (£)</span>'
            f'    <span style="font-size: 13px; font-weight: 600; color: #9467bd;">{w_cost_norm:.0f}%</span>'
            f'  </div>'
            f'  <div style="background-color: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">'
            f'    <div style="background-color: #9467bd; height: 100%; width: {w_cost_norm}%;"></div>'
            f'  </div>'
            f'</div>'
            f'<div style="font-size: 10px; color: #777; margin-top: 12px; font-style: italic;">'
            f'Overall Risk Score = ({w_repeat_norm:.0f}% × Repeat Score) + ({w_churn_norm:.0f}% × Churn Score) + ({w_cost_norm:.0f}% × Cost Score)'
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

    # define percent_rank function (matches BigQuery PERCENT_RANK)
    def percent_rank(series):
        ranks = series.rank(method="min")
        n = len(series)
        if n == 1:
            return pd.Series([0.0], index=series.index)
        return (ranks - 1) / (n - 1)

    # build risk dataframe with scoring
    risk_df = df_grouped_risk.copy().rename(columns={
        "label": "Label",
        "selected_outcome_cleaned": "Outcome",
        "repeat_rate_7d": "Repeat Call Rate (7d)",
        "churn_rate_30d": "BB Churn Rate (30d)",
        "avg_outcome_cost": "Avg. Outcome Cost (£)"
    })

    # calculate percentile scores for each metric
    risk_df["repeat_score"] = (100 * percent_rank(risk_df["Repeat Call Rate (7d)"])).round(0)
    risk_df["churn_score"] = (100 * percent_rank(risk_df["BB Churn Rate (30d)"])).round(0)
    risk_df["cost_score"] = (100 * percent_rank(risk_df["Avg. Outcome Cost (£)"])).round(0)

    # calculate weighted overall risk score
    risk_df["risk_score"] = np.floor(
        (risk_df["repeat_score"] * w_repeat) +
        (risk_df["churn_score"] * w_churn) +
        (risk_df["cost_score"] * w_cost)
    ).astype(int)

    # convert scores to percentage format (0-100 scale) - already at 0-100 from percent_rank
    risk_df["risk_pct"] = risk_df["risk_score"]
    risk_df["repeat_pct"] = risk_df["repeat_score"]
    risk_df["churn_pct"] = risk_df["churn_score"]
    risk_df["cost_pct"] = risk_df["cost_score"]

    # Calculate overall risk tier using weighted boundaries
    avg_low = ((repeat_low_val * w_repeat) + (churn_low_val * w_churn) + (cost_low_val * w_cost))
    avg_med = ((repeat_med_val * w_repeat) + (churn_med_val * w_churn) + (cost_med_val * w_cost))
    
    # categorize overall risk into tiers using averaged boundaries
    risk_df["risk_tier"] = pd.cut(
        risk_df["risk_pct"],
        bins=[0, avg_low, avg_med, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )

    # categorize individual metrics into tiers using metric-specific boundaries
    risk_df["repeat_tier"] = pd.cut(
        risk_df["repeat_pct"],
        bins=[0, repeat_low_val, repeat_med_val, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )
    risk_df["churn_tier"] = pd.cut(
        risk_df["churn_pct"],
        bins=[0, churn_low_val, churn_med_val, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )
    risk_df["cost_tier"] = pd.cut(
        risk_df["cost_pct"],
        bins=[0, cost_low_val, cost_med_val, 100],
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

    # confidence filter
    with st.expander("Confidence filtering", expanded=False):
        min_confidence = st.slider(
            "Minimum LLM-derived confidence score:",
            min_value=1,
            max_value=10,
            value=1,
            key="outcome_analysis_confidence"
        )
        st.caption(f"{len(df_working_risk):,} calls remaining after confidence filter (≥{min_confidence})")
    st.write("\n\n")
    
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

    # display overall risk score boundaries
    st.markdown(f"<div style='font-size: 16px; color: #666;'><b>Overall Risk Score boundaries:</b> Low → Med = <b>{avg_low:.0f}</b> | Med → High = <b>{avg_med:.0f}</b></div>", unsafe_allow_html=True)
    st.write("")

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
            suggested_pct = row.get('suggested_rate', 0) * 100
            st.markdown(f"<div style='font-size: 16px;'><b>{row['Outcome']}</b> ({call_count} calls, {suggested_pct:.0f}% suggested)</div>", unsafe_allow_html=True)
        
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
        "Outcome", "volume", "suggested_rate",
        "Repeat Call Rate (7d)", "repeat_pct", "repeat_tier", 
        "BB Churn Rate (30d)", "churn_pct", "churn_tier", 
        "Avg. Outcome Cost (£)", "cost_pct", "cost_tier", 
        "risk_pct", "risk_tier"
    ]].copy()
    
    # calculate volume suggested
    export_df["volume_suggested"] = (export_df["volume"] * export_df["suggested_rate"]).round(0).astype(int)
    
    # round numeric columns
    export_df["Repeat Call Rate (7d)"] = export_df["Repeat Call Rate (7d)"].round(4)
    export_df["BB Churn Rate (30d)"] = export_df["BB Churn Rate (30d)"].round(4)
    export_df["Avg. Outcome Cost (£)"] = export_df["Avg. Outcome Cost (£)"].round(0)
    export_df["repeat_pct"] = export_df["repeat_pct"].round(0)
    export_df["churn_pct"] = export_df["churn_pct"].round(0)
    export_df["cost_pct"] = export_df["cost_pct"].round(0)
    export_df["risk_pct"] = export_df["risk_pct"].round(0)
    export_df["suggested_rate"] = export_df["suggested_rate"].round(4)
    
    export_df = export_df.rename(columns={
        "Outcome": "Outcome",
        "volume": "Call Volume",
        "volume_suggested": "Volume Suggested",
        "suggested_rate": "% Suggested",
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
    
    # reorder columns to put Volume Suggested and % Suggested after Call Volume
    column_order = [
        "Outcome", "Call Volume", "Volume Suggested", "% Suggested",
        "Repeat Call Rate", "Repeat Call Risk Score", "Repeat Call Risk Tier",
        "BB Churn Rate", "BB Churn Risk Score", "BB Churn Risk Tier",
        "Avg. Outcome Cost", "Cost Risk Score", "Cost Risk Tier",
        "Overall Risk Score", "Overall Risk Tier"
    ]
    export_df = export_df[column_order]
    
    csv_data = export_df.to_csv(index=False)
    st.write("\n\n")
    st.download_button(
        label="Export Risk Scores",
        data=csv_data,
        file_name=f"risk_scores_{selected_label.lower().replace(' ', '_')}.csv",
        mime="text/csv"
    )

    st.divider()

    ################################
    ### section 4 - risk tiering ###
    ### suggested outcomes       ###
    ################################

    # section title
    st.subheader("Risk Tiering by Suggested Outcome")

    # info box
    st.write("\n\n")
    st.info(
        "Outcomes ranked across three risk metrics: Repeat Call Rate (7d), BB Churn (30d), and Cost. Risk scores are calculated across all outcomes and labels. Adjust tier boundaries and metric weights to refine tiers."
    )
    st.write("\n\n")

    # apply confidence filter for this section
    # get confidence value from session state (will be set by slider widget below)
    min_confidence_suggested = st.session_state.get("outcome_analysis_confidence_suggested", 1)
    
    # filter data by confidence and recalculate grouped data for risk analysis
    df_working_risk_suggested = df_working.copy()
    df_working_risk_suggested["confidence"] = df_working_risk_suggested["confidence"].fillna(1)
    df_working_risk_suggested = df_working_risk_suggested[df_working_risk_suggested["confidence"] >= min_confidence_suggested]
    
    # calculate selected indicator (where suggested == selected)
    df_working_risk_suggested["is_selected"] = (
        df_working_risk_suggested["suggested_outcome_cleaned"] == df_working_risk_suggested["selected_outcome_cleaned"]
    ).astype(int)
    
    # recalculate grouped data with confidence filter applied - group by suggested outcome
    df_grouped_risk_suggested = (
        df_working_risk_suggested.groupby(["label", "suggested_outcome_cleaned"])
        .agg(
            volume=("suggested_outcome_cleaned", "size"),
            repeat_rate_7d=("sc_call_next_7d_flag", "mean"),
            churn_rate_30d=("bb_churn_next_30d", "mean"),
            avg_outcome_cost=("outcome_cost", "mean"),
            total_outcome_cost=("outcome_cost", "sum"),
            selected_rate=("is_selected", "mean"),
        )
        .reset_index()
    )

    # pre-calculate scores for boundary reference (before expander)
    temp_risk_df_suggested = df_grouped_risk_suggested.copy().rename(columns={
        "label": "Label",
        "suggested_outcome_cleaned": "Outcome",
        "repeat_rate_7d": "Repeat Call Rate (7d)",
        "churn_rate_30d": "BB Churn Rate (30d)",
        "avg_outcome_cost": "Avg. Outcome Cost (£)"
    })
    
    # define percent_rank function for temp dataframe
    def percent_rank_temp_suggested(series):
        ranks = series.rank(method="min")
        n = len(series)
        if n == 1:
            return pd.Series([0.0], index=series.index)
        return (ranks - 1) / (n - 1)
    
    temp_risk_df_suggested["repeat_pct"] = (100 * percent_rank_temp_suggested(temp_risk_df_suggested["Repeat Call Rate (7d)"])).round(0)
    temp_risk_df_suggested["churn_pct"] = (100 * percent_rank_temp_suggested(temp_risk_df_suggested["BB Churn Rate (30d)"])).round(0)
    temp_risk_df_suggested["cost_pct"] = (100 * percent_rank_temp_suggested(temp_risk_df_suggested["Avg. Outcome Cost (£)"])).round(0)

    # configure metric weights and boundaries
    # user can adjust importance of each metric and set tier thresholds
    with st.expander("Configure boundaries & weights", expanded=False):
        
        # initialize session state for metric-specific boundaries
        if "repeat_low_suggested" not in st.session_state:
            st.session_state.repeat_low_suggested = 33
        if "repeat_med_suggested" not in st.session_state:
            st.session_state.repeat_med_suggested = 66
        if "churn_low_suggested" not in st.session_state:
            st.session_state.churn_low_suggested = 33
        if "churn_med_suggested" not in st.session_state:
            st.session_state.churn_med_suggested = 66
        if "cost_low_suggested" not in st.session_state:
            st.session_state.cost_low_suggested = 33
        if "cost_med_suggested" not in st.session_state:
            st.session_state.cost_med_suggested = 66
        
        st.markdown("#### Risk Tier Boundaries")
        st.caption("Set the thresholds for each metric that define **low**, **medium**, and **high** risk tiers")
        st.write("")
        
        # Define reset function for all boundaries
        def reset_all_boundaries_suggested():
            st.session_state.repeat_low_suggested = 33
            st.session_state.repeat_med_suggested = 66
            st.session_state.churn_low_suggested = 33
            st.session_state.churn_med_suggested = 66
            st.session_state.cost_low_suggested = 33
            st.session_state.cost_med_suggested = 66
        
        # All 6 sliders on one line with reset button and padding between pairs
        slider_cols_suggested = st.columns([0.2, 1, 1, 0.2, 1, 1, 0.2, 1, 1, 0.2, 0.8, 0.2])
        
        with slider_cols_suggested[1]:
            repeat_low_suggested = st.slider("**Repeat Call Rate** - Low -> Med:", 0, 100, key="repeat_low_suggested", step=1, format="%d")
        
        with slider_cols_suggested[2]:
            repeat_med_suggested = st.slider("**Repeat Call Rate** - Med -> High", 0, 100, key="repeat_med_suggested", step=1, format="%d")
        
        with slider_cols_suggested[4]:
            churn_low_suggested = st.slider("**BB Churn Rate** - Low -> Med", 0, 100, key="churn_low_suggested", step=1, format="%d")
        
        with slider_cols_suggested[5]:
            churn_med_suggested = st.slider("**BB Churn Rate** - Med -> High", 0, 100, key="churn_med_suggested", step=1, format="%d")
        
        with slider_cols_suggested[7]:
            cost_low_suggested = st.slider("**Outcome Cost** - Low -> Med", 0, 100, key="cost_low_suggested", step=1, format="%d")
        
        with slider_cols_suggested[8]:
            cost_med_suggested = st.slider("**Outcome Cost** - Med -> High", 0, 100, key="cost_med_suggested", step=1, format="%d")
        
        with slider_cols_suggested[10]:
            st.button("Reset boundaries", on_click=reset_all_boundaries_suggested, key="reset_all_btn_suggested")
        
        # Validation checks with full metric names
        if repeat_low_suggested >= repeat_med_suggested:
            st.error("Repeat Call Rate (7d): Low-Med boundary must be lower than Med-High boundary.")
            st.stop()
        
        if churn_low_suggested >= churn_med_suggested:
            st.error("BB Churn Rate (30d): Low-Med boundary must be lower than Med-High boundary.")
            st.stop()
        
        if cost_low_suggested >= cost_med_suggested:
            st.error("Avg. Outcome Cost (£): Low-Med boundary must be lower than Med-High boundary.")
            st.stop()
        
        st.write("")
        
        # extract session state values
        repeat_low_val_suggested = st.session_state.repeat_low_suggested
        repeat_med_val_suggested = st.session_state.repeat_med_suggested
        churn_low_val_suggested = st.session_state.churn_low_suggested
        churn_med_val_suggested = st.session_state.churn_med_suggested
        cost_low_val_suggested = st.session_state.cost_low_suggested
        cost_med_val_suggested = st.session_state.cost_med_suggested
        
        # calculate tier values for each metric using metric-specific boundaries
        repeat_low_tier_suggested = temp_risk_df_suggested[temp_risk_df_suggested["repeat_pct"] <= repeat_low_val_suggested]["Repeat Call Rate (7d)"].max()
        repeat_med_tier_suggested = temp_risk_df_suggested[temp_risk_df_suggested["repeat_pct"] <= repeat_med_val_suggested]["Repeat Call Rate (7d)"].max()
        
        churn_low_tier_suggested = temp_risk_df_suggested[temp_risk_df_suggested["churn_pct"] <= churn_low_val_suggested]["BB Churn Rate (30d)"].max()
        churn_med_tier_suggested = temp_risk_df_suggested[temp_risk_df_suggested["churn_pct"] <= churn_med_val_suggested]["BB Churn Rate (30d)"].max()
        
        cost_low_tier_suggested = temp_risk_df_suggested[temp_risk_df_suggested["cost_pct"] <= cost_low_val_suggested]["Avg. Outcome Cost (£)"].max()
        cost_med_tier_suggested = temp_risk_df_suggested[temp_risk_df_suggested["cost_pct"] <= cost_med_val_suggested]["Avg. Outcome Cost (£)"].max()
        
        # get min and max values for each metric
        min_repeat_suggested = temp_risk_df_suggested["Repeat Call Rate (7d)"].min()
        max_repeat_suggested = temp_risk_df_suggested["Repeat Call Rate (7d)"].max()
        min_churn_suggested = temp_risk_df_suggested["BB Churn Rate (30d)"].min()
        max_churn_suggested = temp_risk_df_suggested["BB Churn Rate (30d)"].max()
        min_cost_suggested = temp_risk_df_suggested["Avg. Outcome Cost (£)"].min()
        max_cost_suggested = temp_risk_df_suggested["Avg. Outcome Cost (£)"].max()
        
        boundary_display_suggested = (
            f'<div style="background-color: #f9f9f9; padding: 16px 20px 12px 20px; border-radius: 8px; border: 1px solid #e0e0e0;">'
            f'<div style="font-size: 14px; font-weight: 600; color: #333; margin-bottom: 8px;">Current Risk Boundaries:</div>'
            f'<div style="margin-bottom: 12px;"><div style="font-size: 13px; color: #555; margin-bottom: 4px;">Repeat Call Rate (7d)</div>'
            f'<div style="position: relative; height: 28px;"><div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; background-color: #e0e0e0;"><div style="background-color: #4d9e4d; width: {repeat_low_val_suggested}%; flex-shrink: 0;"></div><div style="background-color: #f8953e; width: {repeat_med_val_suggested - repeat_low_val_suggested}%; flex-shrink: 0;"></div><div style="background-color: #d44646; width: {100 - repeat_med_val_suggested}%; flex-shrink: 0;"></div></div>'
            f'<span style="position: absolute; left: 0%; top: 14px; text-align: left; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{min_repeat_suggested:.1%}</span>'
            f'<span style="position: absolute; left: {repeat_low_val_suggested}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{repeat_low_tier_suggested:.1%}</span>'
            f'<span style="position: absolute; left: {repeat_med_val_suggested}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{repeat_med_tier_suggested:.1%}</span>'
            f'<span style="position: absolute; right: 0%; top: 14px; text-align: right; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{max_repeat_suggested:.1%}</span></div></div>'
            f'<div style="margin-bottom: 12px;"><div style="font-size: 13px; color: #555; margin-bottom: 4px;">BB Churn Rate (30d)</div>'
            f'<div style="position: relative; height: 28px;"><div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; background-color: #e0e0e0;"><div style="background-color: #4d9e4d; width: {churn_low_val_suggested}%; flex-shrink: 0;"></div><div style="background-color: #f8953e; width: {churn_med_val_suggested - churn_low_val_suggested}%; flex-shrink: 0;"></div><div style="background-color: #d44646; width: {100 - churn_med_val_suggested}%; flex-shrink: 0;"></div></div>'
            f'<span style="position: absolute; left: 0%; top: 14px; text-align: left; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{min_churn_suggested:.1%}</span>'
            f'<span style="position: absolute; left: {churn_low_val_suggested}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{churn_low_tier_suggested:.1%}</span>'
            f'<span style="position: absolute; left: {churn_med_val_suggested}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{churn_med_tier_suggested:.1%}</span>'
            f'<span style="position: absolute; right: 0%; top: 14px; text-align: right; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">{max_churn_suggested:.1%}</span></div></div>'
            f'<div><div style="font-size: 13px; color: #555; margin-bottom: 4px;">Avg. Outcome Cost (£)</div>'
            f'<div style="position: relative; height: 28px;"><div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; background-color: #e0e0e0;"><div style="background-color: #4d9e4d; width: {cost_low_val_suggested}%; flex-shrink: 0;"></div><div style="background-color: #f8953e; width: {cost_med_val_suggested - cost_low_val_suggested}%; flex-shrink: 0;"></div><div style="background-color: #d44646; width: {100 - cost_med_val_suggested}%; flex-shrink: 0;"></div></div>'
            f'<span style="position: absolute; left: 0%; top: 14px; text-align: left; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">£{min_cost_suggested:.0f}</span>'
            f'<span style="position: absolute; left: {cost_low_val_suggested}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">£{cost_low_tier_suggested:.0f}</span>'
            f'<span style="position: absolute; left: {cost_med_val_suggested}%; top: 14px; transform: translateX(-50%); font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">£{cost_med_tier_suggested:.0f}</span>'
            f'<span style="position: absolute; right: 0%; top: 14px; text-align: right; font-size: 11px; font-weight: 600; color: #666; white-space: nowrap;">£{max_cost_suggested:.0f}</span></div></div>'
            f'<div style="font-size: 10px; color: #999; margin-top: 8px; font-style: italic;">Green = Low risk | Amber = Medium risk | Red = High risk</div></div>'
        )
        
        st.markdown(boundary_display_suggested, unsafe_allow_html=True)
        
        st.write("\n\n")
        
        st.markdown("#### Metric Importance Weights")
        st.caption("Adjust how much each metric contributes to the **overall risk score and combined boundaries**")
        st.write("")
        
        # initialize session state for weights if not already set
        if "weight_repeat_suggested" not in st.session_state:
            st.session_state.weight_repeat_suggested = 33
        if "weight_churn_suggested" not in st.session_state:
            st.session_state.weight_churn_suggested = 33
        if "weight_cost_suggested" not in st.session_state:
            st.session_state.weight_cost_suggested = 34
        
        # Define reset function for weights
        def reset_weights_suggested():
            st.session_state.weight_repeat_suggested = 33
            st.session_state.weight_churn_suggested = 33
            st.session_state.weight_cost_suggested = 34
        
        # weight sliders with spacing
        weight_cols_suggested = st.columns([0.2, 1, 0.2, 1, 0.2, 1, 0.2, 0.6])
        with weight_cols_suggested[1]:
            weight_repeat_suggested = st.slider(
                "**Repeat Call Rate** - importance:",
                0, 100,
                key="weight_repeat_suggested"
            )
        with weight_cols_suggested[3]:
            weight_churn_suggested = st.slider(
                "**BB Churn Rate** - importance:",
                0, 100,
                key="weight_churn_suggested"
            )
        with weight_cols_suggested[5]:
            weight_cost_suggested = st.slider(
                "**Outcome Cost** - importance:",
                0, 100,
                key="weight_cost_suggested"
            )
        with weight_cols_suggested[7]:
            st.button("Reset weights", on_click=reset_weights_suggested, key="reset_weights_btn_suggested")

        if weight_repeat_suggested + weight_churn_suggested + weight_cost_suggested != 100:
            st.caption("⚠️ Weights will be normalised automatically to sum to 100%")
        
        # calculate normalised weights for display
        weight_sum_suggested = weight_repeat_suggested + weight_churn_suggested + weight_cost_suggested or 1
        w_repeat_norm_suggested = (weight_repeat_suggested / weight_sum_suggested) * 100
        w_churn_norm_suggested = (weight_churn_suggested / weight_sum_suggested) * 100
        w_cost_norm_suggested = (weight_cost_suggested / weight_sum_suggested) * 100
        
        st.write("")
        st.markdown(
            f'<div style="background-color: #f9f9f9; padding: 16px; border-radius: 8px; border: 1px solid #e0e0e0;">'
            f'<div style="font-size: 14px; font-weight: 600; color: #333; margin-bottom: 10px;">Current Weight Distribution:</div>'
            f'<div style="margin-bottom: 8px;">'
            f'  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">'
            f'    <span style="font-size: 13px; color: #555;">Repeat Call Rate (7d)</span>'
            f'    <span style="font-size: 13px; font-weight: 600; color: #ff7f0e;">{w_repeat_norm_suggested:.0f}%</span>'
            f'  </div>'
            f'  <div style="background-color: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">'
            f'    <div style="background-color: #ff7f0e; height: 100%; width: {w_repeat_norm_suggested}%;"></div>'
            f'  </div>'
            f'</div>'
            f'<div style="margin-bottom: 8px;">'
            f'  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">'
            f'    <span style="font-size: 13px; color: #555;">BB Churn Rate (30d)</span>'
            f'    <span style="font-size: 13px; font-weight: 600; color: #d62728;">{w_churn_norm_suggested:.0f}%</span>'
            f'  </div>'
            f'  <div style="background-color: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">'
            f'    <div style="background-color: #d62728; height: 100%; width: {w_churn_norm_suggested}%;"></div>'
            f'  </div>'
            f'</div>'
            f'<div style="margin-bottom: 4px;">'
            f'  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">'
            f'    <span style="font-size: 13px; color: #555;">Avg. Outcome Cost (£)</span>'
            f'    <span style="font-size: 13px; font-weight: 600; color: #9467bd;">{w_cost_norm_suggested:.0f}%</span>'
            f'  </div>'
            f'  <div style="background-color: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">'
            f'    <div style="background-color: #9467bd; height: 100%; width: {w_cost_norm_suggested}%;"></div>'
            f'  </div>'
            f'</div>'
            f'<div style="font-size: 10px; color: #777; margin-top: 12px; font-style: italic;">'
            f'Overall Risk Score = ({w_repeat_norm_suggested:.0f}% × Repeat Score) + ({w_churn_norm_suggested:.0f}% × Churn Score) + ({w_cost_norm_suggested:.0f}% × Cost Score)'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        st.write("\n\n")

    # normalize weights to sum to 100%
    weight_sum_suggested = weight_repeat_suggested + weight_churn_suggested + weight_cost_suggested or 1
    w_repeat_suggested = weight_repeat_suggested / weight_sum_suggested
    w_churn_suggested = weight_churn_suggested / weight_sum_suggested
    w_cost_suggested = weight_cost_suggested / weight_sum_suggested

    # define percent_rank function (matches BigQuery PERCENT_RANK)
    def percent_rank_suggested(series):
        ranks = series.rank(method="min")
        n = len(series)
        if n == 1:
            return pd.Series([0.0], index=series.index)
        return (ranks - 1) / (n - 1)

    # build risk dataframe with scoring
    risk_df_suggested = df_grouped_risk_suggested.copy().rename(columns={
        "label": "Label",
        "suggested_outcome_cleaned": "Outcome",
        "repeat_rate_7d": "Repeat Call Rate (7d)",
        "churn_rate_30d": "BB Churn Rate (30d)",
        "avg_outcome_cost": "Avg. Outcome Cost (£)"
    })

    # calculate percentile scores for each metric
    risk_df_suggested["repeat_score"] = (100 * percent_rank_suggested(risk_df_suggested["Repeat Call Rate (7d)"])).round(0)
    risk_df_suggested["churn_score"] = (100 * percent_rank_suggested(risk_df_suggested["BB Churn Rate (30d)"])).round(0)
    risk_df_suggested["cost_score"] = (100 * percent_rank_suggested(risk_df_suggested["Avg. Outcome Cost (£)"])).round(0)

    # calculate weighted overall risk score
    risk_df_suggested["risk_score"] = np.floor(
        (risk_df_suggested["repeat_score"] * w_repeat_suggested) +
        (risk_df_suggested["churn_score"] * w_churn_suggested) +
        (risk_df_suggested["cost_score"] * w_cost_suggested)
    ).astype(int)

    # convert scores to percentage format (0-100 scale) - already at 0-100 from percent_rank
    risk_df_suggested["risk_pct"] = risk_df_suggested["risk_score"]
    risk_df_suggested["repeat_pct"] = risk_df_suggested["repeat_score"]
    risk_df_suggested["churn_pct"] = risk_df_suggested["churn_score"]
    risk_df_suggested["cost_pct"] = risk_df_suggested["cost_score"]

    # Calculate overall risk tier using weighted boundaries
    avg_low_suggested = ((repeat_low_val_suggested * w_repeat_suggested) + (churn_low_val_suggested * w_churn_suggested) + (cost_low_val_suggested * w_cost_suggested))
    avg_med_suggested = ((repeat_med_val_suggested * w_repeat_suggested) + (churn_med_val_suggested * w_churn_suggested) + (cost_med_val_suggested * w_cost_suggested))
    
    # categorize overall risk into tiers using averaged boundaries
    risk_df_suggested["risk_tier"] = pd.cut(
        risk_df_suggested["risk_pct"],
        bins=[0, avg_low_suggested, avg_med_suggested, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )

    # categorize individual metrics into tiers using metric-specific boundaries
    risk_df_suggested["repeat_tier"] = pd.cut(
        risk_df_suggested["repeat_pct"],
        bins=[0, repeat_low_val_suggested, repeat_med_val_suggested, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )
    risk_df_suggested["churn_tier"] = pd.cut(
        risk_df_suggested["churn_pct"],
        bins=[0, churn_low_val_suggested, churn_med_val_suggested, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )
    risk_df_suggested["cost_tier"] = pd.cut(
        risk_df_suggested["cost_pct"],
        bins=[0, cost_low_val_suggested, cost_med_val_suggested, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )

    st.write("\n\n")

    # label filter and selection
    single_labels_suggested = [lbl for lbl in label_order if lbl in risk_df_suggested["Label"].unique()]
    default_label_suggested = "Wi-Fi Status" if "Wi-Fi Status" in single_labels_suggested else single_labels_suggested[0]

    # label selectbox
    selected_label_suggested = st.selectbox(
        "Select a call issue label:",
        options=single_labels_suggested,
        index=single_labels_suggested.index(default_label_suggested) if default_label_suggested in single_labels_suggested else 0,
        key="risk_label_select_suggested"
    )
    st.write("")

    # confidence filter
    with st.expander("Confidence filtering", expanded=False):
        min_confidence_suggested = st.slider(
            "Minimum LLM-derived confidence score:",
            min_value=1,
            max_value=10,
            value=1,
            key="outcome_analysis_confidence_suggested"
        )
        st.caption(f"{len(df_working_risk_suggested):,} calls remaining after confidence filter (≥{min_confidence_suggested})")
    st.write("\n\n")
    
    # risk tier legend
    # centered display with color indicators
    legend_html_suggested = '<div style="display: flex; justify-content: center; gap: 32px; margin-bottom: 16px; font-size: 16px; align-items: center; font-weight: 600;">'
    legend_html_suggested += '<div style="display: flex; align-items: center; gap: 8px;"><div style="width: 16px; height: 16px; background-color: #4d9e4d; border-radius: 2px;"></div><span>Low risk</span></div>'
    legend_html_suggested += '<div style="display: flex; align-items: center; gap: 8px;"><div style="width: 16px; height: 16px; background-color: #f8953e; border-radius: 2px;"></div><span>Medium risk</span></div>'
    legend_html_suggested += '<div style="display: flex; align-items: center; gap: 8px;"><div style="width: 16px; height: 16px; background-color: #d44646; border-radius: 2px;"></div><span>High risk</span></div>'
    legend_html_suggested += '</div>'
    st.markdown(legend_html_suggested, unsafe_allow_html=True)
    st.write("")

    # filter risk data by selected label
    display_df_suggested = risk_df_suggested[risk_df_suggested["Label"] == selected_label_suggested].sort_values("risk_pct", ascending=False)

    # display overall risk score boundaries
    st.markdown(f"<div style='font-size: 16px; color: #666;'><b>Overall Risk Score boundaries:</b> Low → Med = <b>{avg_low_suggested:.0f}</b> | Med → High = <b>{avg_med_suggested:.0f}</b></div>", unsafe_allow_html=True)
    st.write("")

    # display metric ranges at boundaries
    st.write("")

    # display column headers
    col_header_outcome_suggested, col_header_cards_suggested, col_header_overall_suggested = st.columns([1, 2.2, 0.65], gap="small")
    with col_header_cards_suggested:
        header_cols_suggested = st.columns(3, gap="small")
        with header_cols_suggested[0]:
            st.markdown('<div style="font-size: 16px; font-weight: 700; text-align: center; color: #333;">Repeat Call Risk Score | Actual<br><span style="font-size: 11px; opacity: 0.8;"></div>', unsafe_allow_html=True)
        with header_cols_suggested[1]:
            st.markdown('<div style="font-size: 16px; font-weight: 700; text-align: center; color: #333;">BB Churn Risk Score | Actual<br><span style="font-size: 11px; opacity: 0.8;"></div>', unsafe_allow_html=True)
        with header_cols_suggested[2]:
            st.markdown('<div style="font-size: 16px; font-weight: 700; text-align: center; color: #333;">Cost Risk Score | Actual<br><span style="font-size: 11px; opacity: 0.8;"></div>', unsafe_allow_html=True)
    with col_header_overall_suggested:
        st.markdown('<div style="font-size: 16px; font-weight: 700; text-align: center; color: #333;">Overall Risk Score</div>', unsafe_allow_html=True)
    st.write("")

    # render outcome risk cards
    # format call counts with 'k' notation for 4+ digits
    def format_calls_suggested(volume):
        if volume >= 1000:
            return f"{volume/1000:.1f}k"
        else:
            return str(int(volume))
    
    # iterate through outcomes and render risk cards
    for idx, row in display_df_suggested.iterrows():
        col_outcome_suggested, col_cards_suggested, col_overall_suggested = st.columns([1, 2.2, 0.65], gap="small", vertical_alignment="center")
        
        with col_outcome_suggested:
            call_count_suggested = format_calls_suggested(row['volume'])
            selected_pct = row.get('selected_rate', 0) * 100
            st.markdown(f"<div style='font-size: 16px;'><b>{row['Outcome']}</b> ({call_count_suggested} calls, {selected_pct:.0f}% selected)</div>", unsafe_allow_html=True)
        
        with col_cards_suggested:
            card_cols_suggested = st.columns(3, gap="small", vertical_alignment="center")
            
            # repeat call risk card
            with card_cols_suggested[0]:
                repeat_color_suggested = tier_color_map[row["repeat_tier"]]
                st.markdown(
                    f'<div style="background-color: {repeat_color_suggested}; padding: 6px 4px; border-radius: 4px; text-align: center; color: white; height: 100%; display: flex; align-items: center; justify-content: center;">'
                    f'<div style="font-size: 16px; font-weight: 700; line-height: 1.3;">{row["repeat_pct"]:.0f} <span style="font-weight: 400;">| {row["Repeat Call Rate (7d)"]:.1%}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            # churn risk card
            with card_cols_suggested[1]:
                churn_color_suggested = tier_color_map[row["churn_tier"]]
                st.markdown(
                    f'<div style="background-color: {churn_color_suggested}; padding: 6px 4px; border-radius: 4px; text-align: center; color: white; height: 100%; display: flex; align-items: center; justify-content: center;">'
                    f'<div style="font-size: 16px; font-weight: 700; line-height: 1.3;">{row["churn_pct"]:.0f} <span style="font-weight: 400;">| {row["BB Churn Rate (30d)"]:.1%}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            # cost risk card
            with card_cols_suggested[2]:
                cost_color_suggested = tier_color_map[row["cost_tier"]]
                st.markdown(
                    f'<div style="background-color: {cost_color_suggested}; padding: 6px 4px; border-radius: 4px; text-align: center; color: white; height: 100%; display: flex; align-items: center; justify-content: center;">'
                    f'<div style="font-size: 16px; font-weight: 700; line-height: 1.3;">{row["cost_pct"]:.0f} <span style="font-weight: 400;">| £{row["Avg. Outcome Cost (£)"]:.0f}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            # overall risk card
            with col_overall_suggested:
                overall_color_suggested = tier_color_map[row["risk_tier"]]
                asterisk_suggested = "*" if row["volume"] < 250 else ""
                st.markdown(
                    f'<div style="background-color: {overall_color_suggested}; padding: 6px 4px; border-radius: 4px; text-align: center; color: white; border: 2px solid #333; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;">'
                    f'<div style="font-size: 16px; font-weight: 700; line-height: 1.2;">{row["risk_pct"]:.0f}{asterisk_suggested}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        
        st.markdown("<div style='margin: 0px 0;'></div>", unsafe_allow_html=True)

    # footnote for small sample sizes
    # displayed when outcomes have fewer than 250 calls
    if (display_df_suggested["volume"] < 250).any():
        st.markdown(
            "<div style='text-align: right; font-size: 12px; opacity: 0.7; margin-top: 8px;'>"
            "<span style='color: #666;'>* Small sample size (less than 250 calls) — use with caution</span>"
            "</div>",
            unsafe_allow_html=True
        )

    # export risk scores to csv
    export_df_suggested = display_df_suggested[[
        "Outcome", "volume", "selected_rate",
        "Repeat Call Rate (7d)", "repeat_pct", "repeat_tier", 
        "BB Churn Rate (30d)", "churn_pct", "churn_tier", 
        "Avg. Outcome Cost (£)", "cost_pct", "cost_tier", 
        "risk_pct", "risk_tier"
    ]].copy()
    
    # calculate volume selected
    export_df_suggested["volume_selected"] = (export_df_suggested["volume"] * export_df_suggested["selected_rate"]).round(0).astype(int)
    
    # round numeric columns
    export_df_suggested["Repeat Call Rate (7d)"] = export_df_suggested["Repeat Call Rate (7d)"].round(4)
    export_df_suggested["BB Churn Rate (30d)"] = export_df_suggested["BB Churn Rate (30d)"].round(4)
    export_df_suggested["Avg. Outcome Cost (£)"] = export_df_suggested["Avg. Outcome Cost (£)"].round(0)
    export_df_suggested["repeat_pct"] = export_df_suggested["repeat_pct"].round(0)
    export_df_suggested["churn_pct"] = export_df_suggested["churn_pct"].round(0)
    export_df_suggested["cost_pct"] = export_df_suggested["cost_pct"].round(0)
    export_df_suggested["risk_pct"] = export_df_suggested["risk_pct"].round(0)
    export_df_suggested["selected_rate"] = export_df_suggested["selected_rate"].round(4)
    
    export_df_suggested = export_df_suggested.rename(columns={
        "Outcome": "Outcome",
        "volume": "Call Volume",
        "volume_selected": "Volume Selected",
        "selected_rate": "% Selected",
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
    
    # reorder columns to put Volume Selected and % Selected after Call Volume
    column_order_suggested = [
        "Outcome", "Call Volume", "Volume Selected", "% Selected",
        "Repeat Call Rate", "Repeat Call Risk Score", "Repeat Call Risk Tier",
        "BB Churn Rate", "BB Churn Risk Score", "BB Churn Risk Tier",
        "Avg. Outcome Cost", "Cost Risk Score", "Cost Risk Tier",
        "Overall Risk Score", "Overall Risk Tier"
    ]
    export_df_suggested = export_df_suggested[column_order_suggested]
    
    csv_data_suggested = export_df_suggested.to_csv(index=False)
    st.write("\n\n")
    st.download_button(
        label="Export Risk Scores",
        data=csv_data_suggested,
        file_name=f"risk_scores_suggested_{selected_label_suggested.lower().replace(' ', '_')}.csv",
        mime="text/csv"
    )

    st.divider()