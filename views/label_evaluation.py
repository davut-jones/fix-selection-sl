import streamlit as st
import pandas as pd
import altair as alt

def render_view(df_filtered):

    # page text
    st.write("\n\n")
    st.markdown(
    '<span style="font-size: 1.1rem; font-weight: 400;">Evaluate the accuracy of LLM-generated labels by comparing them against Enginner notes and CSG call reasons</span>',
    unsafe_allow_html=True
    )
    st.divider()

    # work on a copy to avoid mutating the original dataframe
    df_working = df_filtered.copy()


    ##############################################
    ### section 1 - engineer reasons per label ###
    ##############################################

    st.subheader("Engineer Reported Reasons by Label")
    st.write("\n\n")
    st.warning("Only calls that end in a BBTTE visit have engineer notes. Distributions are for calls with both values. Mapping below.")
    st.write("\n\n")

    # top x filter
    filter_col, _ = st.columns([3, 7])
    with filter_col:
        # top X slider
        top_x = st.slider(
            "Show top X engineer reported reasons for each label:",
            min_value=1,
            max_value=len(df_working['engineer_reported_symptom'].dropna().value_counts()),
            value=5,
            key="eng_top_x"
        )

    st.write("\n\n")

    # remove nulls for reason analysis
    df_eng_reason = df_working[df_working["engineer_reported_symptom"].notna()].copy()

    # get counts
    eng_reason_counts = (
        df_eng_reason.groupby(["label", "engineer_reported_symptom"])
        .size()
        .reset_index(name="count")
    )

    # totals for x-axis (only where reason exists)
    eng_label_totals = (
        df_eng_reason.groupby("label")
        .size()
        .reset_index(name="total_calls")
    )

    # add totals to labels
    eng_label_totals["label_with_total"] = (
        eng_label_totals["label"] + " (" + (eng_label_totals["total_calls"] / 1000).round(1).astype(str) + "k)"
    )

    # calculate percent within label (based on full label denominator)
    eng_reason_counts = eng_reason_counts.merge(eng_label_totals[["label", "total_calls"]], on="label", how="left")
    eng_reason_counts["pct_of_label"] = eng_reason_counts["count"] / eng_reason_counts["total_calls"] * 100

    # label order
    label_order = [
        "Wi-Fi Status",
        "Unreliable Wi-Fi",
        "Slow Wi-Fi",
        "Poor Coverage",
        "Other",
        "Unclear"
    ]

    # determine top X reasons by overall count
    eng_top_reasons = (
        eng_reason_counts.groupby("engineer_reported_symptom")["count"]
        .sum()
        .reset_index()
        .sort_values("count", ascending=False)
        .head(top_x)["engineer_reported_symptom"]
    )

    # filter to only top reasons (no "Other" bucket)
    eng_reason_counts = eng_reason_counts[eng_reason_counts["engineer_reported_symptom"].isin(eng_top_reasons)].copy()

    # merge totals into chart df
    eng_reason_counts = eng_reason_counts.merge(
        eng_label_totals[["label", "label_with_total"]],
        on="label",
        how="left"
    )

    # build chart
    eng_reason_chart = (
        alt.Chart(eng_reason_counts)
        .mark_bar()
        .encode(
            x=alt.X(
                "label_with_total:N",
                title="Label (Total Calls)",
                sort=alt.SortArray(
                    eng_label_totals[
                        eng_label_totals["label"].isin(label_order)
                    ]
                    .assign(
                        label_order=lambda df: df["label"].map(
                            {label: i for i, label in enumerate(label_order)}
                        )
                    )
                    .sort_values(by="label_order")["label_with_total"]
                    .tolist()
                ),
                axis=alt.Axis(labelAngle=0, labelLimit=1000)
            ),
            y=alt.Y("pct_of_label:Q", title="% of Label Calls", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("engineer_reported_symptom:N", title="Engineer Reason"),
            tooltip=[
                alt.Tooltip("label:N", title="Label"),
                alt.Tooltip("engineer_reported_symptom:N", title="Engineer Reason"),
                alt.Tooltip("pct_of_label:Q", title="% of Label", format=".1f"),
                alt.Tooltip("count:Q", title="Count")
            ]
        )
        .properties(height=350)
    )

    st.altair_chart(eng_reason_chart, use_container_width=True)

    # remaining rows after filtering
    st.caption(f"{eng_label_totals.total_calls.sum():,} or {round(eng_label_totals.total_calls.sum() / len(df_filtered) * 100, 1)}% calls with a BTTEE visit and engineer note  after global filters applied")

    st.divider()


    #############################################
    ### section 2 - engineer reason alignment ###
    #############################################

    st.subheader("Engineer Reported Reason Alignment by Label")
    st.write("\n\n")
    st.warning("Alignment is calculated only for calls with a mapped engineer reported reason. Mapping below.")
    st.write("\n\n")

    # confidence filter
    # filter_col, _ = st.columns([3, 7])
    # with filter_col:
    with st.expander("Confidence filtering", expanded=False):
        engineer_min_confidence = st.slider(
            "Minimum LLM-derived confidence score:",
            min_value=1,
            max_value=10,
            value=1,
            key="engineer_alignment_confidence"
        )

    # mapping dictionary
    eng_to_llm_map = {
        "TT Broadband - No Sync": "Wi-Fi Status",
        "TT Broadband -  Connection Dropping out": "Unreliable Wi-Fi",  # has extra space
        "TT Broadband - Slow Speed": "Slow Wi-Fi",
    }

    df_working["mapped_llm_label_eng"] = df_working["engineer_reported_symptom"].map(eng_to_llm_map)

    # compute alignment based on non-null engineer reasons and confidence filter
    alignment_base = df_working[
        (df_working["engineer_reported_symptom"].notna()) &
        (df_working["confidence"] >= engineer_min_confidence)
    ].copy()

    mapped_counts = (
        alignment_base.dropna(subset=["mapped_llm_label_eng"])
        .groupby(["label", "mapped_llm_label_eng"])
        .size()
        .reset_index(name="mapped_count")
    )

    label_totals_reason = (
        alignment_base.groupby("label")
        .size()
        .reset_index(name="label_reason_count")
    )

    if alignment_base.shape[0] < 50:
        st.warning("Low sample size — interpret alignment with caution.")

    alignment_df = mapped_counts.merge(label_totals_reason, on="label", how="left")

    # compute alignment correctly (only matching labels)
    alignment_df["match_flag"] = alignment_df["label"] == alignment_df["mapped_llm_label_eng"]
    alignment_df["match_count"] = alignment_df["mapped_count"] * alignment_df["match_flag"]

    alignment_df = (
        alignment_df.groupby("label")
        .agg(
            mapped_count=("mapped_count", "sum"),
            match_count=("match_count", "sum"),
            label_reason_count=("label_reason_count", "first")
        )
        .reset_index()
    )

    alignment_df["alignment_pct"] = (alignment_df["match_count"] / alignment_df["label_reason_count"]) * 100

    alignment_chart = (
        alt.Chart(alignment_df)
        .mark_bar(color="#5A67D8")
        .encode(
            y=alt.Y("label:N", sort="-x", title=None),
            x=alt.X("alignment_pct:Q", title="Alignment (%)", scale=alt.Scale(domain=[0, 100])),
            tooltip=[
                alt.Tooltip("label:N", title="Label"),
                alt.Tooltip("label_reason_count:Q", title="Calls with Engineer Reason"),
                alt.Tooltip("match_count:Q", title="Mapped Calls"),
                alt.Tooltip("alignment_pct:Q", title="Alignment %", format=".1f")
            ]
        )
        .properties(height=45 * len(alignment_df))
    )

    st.altair_chart(alignment_chart, use_container_width=True)

    with st.expander("Label to Engineer Reported Reason mapping"):
        label_to_eng_map = pd.DataFrame(
            list(eng_to_llm_map.items()),
            columns=["Engineer Reason", "Label"]
        )
        st.table(label_to_eng_map[["Label", "Engineer Reason"]])

    st.divider()


    #########################################
    ### section 3 - csg reasons per label ###
    #########################################

    st.subheader("CSG Call Reasons by Label")
    st.write("\n\n")
    st.warning("Not all calls have a CSG reason. Distributions are for calls with both values.")
    st.write("\n\n")

    # top X filter
    filter_col, _ = st.columns([3, 7])
    with filter_col:
        top_x = st.slider(
            "Top X CSG reasons ::",
            min_value=1,
            max_value=len(df_working['first_csg_call_reason'].dropna().value_counts()),
            value=5
        )
    st.write("\n\n")

    # remove nulls for reason analysis
    df_reason = df_working[df_working["first_csg_call_reason"].notna()].copy()

    # get counts
    reason_counts = (
        df_reason.groupby(["label", "first_csg_call_reason"])
        .size()
        .reset_index(name="count")
    )

    # totals for x-axis (only where reason exists)
    label_totals = (
        df_reason.groupby("label")
        .size()
        .reset_index(name="total_calls")
    )

    # add totals to labels
    label_totals["label_with_total"] = (
        label_totals["label"] + " (" + (label_totals["total_calls"] / 1000).round(1).astype(str) + "k)"
    )

    # calculate percent within label (based on full label denominator)
    reason_counts = reason_counts.merge(label_totals[["label", "total_calls"]], on="label", how="left")
    reason_counts["pct_of_label"] = reason_counts["count"] / reason_counts["total_calls"] * 100

    # label order
    label_order = [
        "Wi-Fi Status",
        "Unreliable Wi-Fi",
        "Slow Wi-Fi",
        "Poor Coverage",
        "Other",
        "Unclear"
    ]

    # determine top X reasons by overall count
    top_reasons = (
        reason_counts.groupby("first_csg_call_reason")["count"]
        .sum()
        .reset_index()
        .sort_values("count", ascending=False)
        .head(top_x)["first_csg_call_reason"]
    )

    # filter to only top reasons (no "Other" bucket)
    reason_counts = reason_counts[reason_counts["first_csg_call_reason"].isin(top_reasons)].copy()

    # merge totals into chart df
    reason_counts = reason_counts.merge(
        label_totals[["label", "label_with_total"]],
        on="label",
        how="left"
    )

    # build chart
    reason_chart = (
        alt.Chart(reason_counts)
        .mark_bar()
        .encode(
            x=alt.X(
                "label_with_total:N",
                title="Label (Total Calls)",
                sort=alt.SortArray(
                    label_totals[
                        label_totals["label"].isin(label_order)
                    ]
                    .assign(
                        label_order=lambda df: df["label"].map(
                            {label: i for i, label in enumerate(label_order)}
                        )
                    )
                    .sort_values(by="label_order")["label_with_total"]
                    .tolist()
                ),
                axis=alt.Axis(labelAngle=0, labelLimit=1000)
            ),
            y=alt.Y("pct_of_label:Q", title="% of Label Calls", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("first_csg_call_reason:N", title="CSG Reason"),
            tooltip=[
                alt.Tooltip("label:N", title="Label"),
                alt.Tooltip("first_csg_call_reason:N", title="CSG Reason"),
                alt.Tooltip("pct_of_label:Q", title="% of Label", format=".1f"),
                alt.Tooltip("count:Q", title="Count")
            ]
        )
        .properties(height=350)
    )

    st.altair_chart(reason_chart, use_container_width=True)

    # remaining rows after filtering
    st.caption(f"{label_totals.total_calls.sum():,} or {round(label_totals.total_calls.sum() / len(df_filtered) * 100, 1)}% calls with a CSG call reason after global filters applied")

    st.divider()


    ########################################
    ### section 4 - csg reason alignment ###
    ########################################

    st.subheader("CSG Call Reason Alignment by Label")

    st.write("\n\n")
    st.warning("Alignment is calculated only for calls with a mapped CSG call reason.")
    st.write("\n\n")

    # confidence filter
    # filter_col, _ = st.columns([3, 7])
    # with filter_col:
    with st.expander("Confidence filtering", expanded=False):
        csg_min_confidence = st.slider(
            "Minimum LLM-derived confidence score:",
            min_value=1,
            max_value=10,
            value=1,
            key="csg_alignment_confidence"
        )

    # mapping dictionary
    csg_to_llm_map = {
        "No Connection": "Wi-Fi Status",
        "Intermittent Connection": "Unreliable Wi-Fi",
        "Slow Connection": "Slow Wi-Fi",
    }

    df_working["mapped_llm_label_csg"] = df_working["first_csg_call_reason"].map(csg_to_llm_map)

    # compute alignment based on non-null CSG reasons and confidence filter
    alignment_base = df_working[
        (df_working["first_csg_call_reason"].notna()) &
        (df_working["confidence"] >= csg_min_confidence)
    ].copy()

    mapped_counts = (
        alignment_base.dropna(subset=["mapped_llm_label_csg"])
        .groupby(["label", "mapped_llm_label_csg"])
        .size()
        .reset_index(name="mapped_count")
    )

    label_totals_reason = (
        alignment_base.groupby("label")
        .size()
        .reset_index(name="label_reason_count")
    )

    if alignment_base.shape[0] < 50:
        st.warning("Low sample size — interpret alignment with caution.")

    alignment_df = mapped_counts.merge(label_totals_reason, on="label", how="left")

    alignment_df["match_flag"] = alignment_df["label"] == alignment_df["mapped_llm_label_csg"]
    alignment_df["match_count"] = alignment_df["mapped_count"] * alignment_df["match_flag"]

    alignment_df = (
        alignment_df.groupby("label")
        .agg(
            mapped_count=("mapped_count", "sum"),
            match_count=("match_count", "sum"),
            label_reason_count=("label_reason_count", "first")
        )
        .reset_index()
    )

    alignment_df["alignment_pct"] = (alignment_df["match_count"] / alignment_df["label_reason_count"]) * 100

    alignment_chart = (
        alt.Chart(alignment_df)
        .mark_bar(color="#5A67D8")
        .encode(
            y=alt.Y("label:N", sort="-x", title=None),
            x=alt.X("alignment_pct:Q", title="Alignment (%)", scale=alt.Scale(domain=[0, 100])),
            tooltip=[
                alt.Tooltip("label:N", title="Label"),
                alt.Tooltip("label_reason_count:Q", title="Calls with CSG Reason"),
                alt.Tooltip("match_count:Q", title="Mapped Calls"),
                alt.Tooltip("alignment_pct:Q", title="Alignment %", format=".1f")
            ]
        )
        .properties(height=45 * len(alignment_df))
    )

    st.altair_chart(alignment_chart, use_container_width=True)

    with st.expander("Label to CSG Call Reason mapping"):
        label_to_csg_map = pd.DataFrame(
            list(csg_to_llm_map.items()),
            columns=["CSG Call Reason", "Label"]
        )
        st.table(label_to_csg_map[["Label", "CSG Call Reason"]])

    st.divider()


    ##################################
    ### section 5 - llm confidence ###
    ##################################

    # ensure numeric types
    df_working["confidence"] = pd.to_numeric(df_working["confidence"], errors="coerce")

    # bin confidence values from 1-10
    df_working["confidence_bin"] = pd.cut(
        df_working["confidence"],
        bins=list(range(0, 11)),   # 0-10 edges
        labels=list(range(1, 11)), # 1-10 labels
        include_lowest=True,
        right=True
    )

    conf_dist = (
        df_working.groupby("confidence_bin")
        .size()
        .reset_index(name="count")
    )

    conf_chart = (
        alt.Chart(conf_dist)
        .mark_bar(color="#5A67D8")
        .encode(
            x=alt.X("confidence_bin:O", title="Confidence (1–10)"),
            y=alt.Y("count:Q", title="Calls"),
            tooltip=[
                alt.Tooltip("confidence_bin:O", title="Confidence"),
                alt.Tooltip("count:Q", title="Count")
            ]
        )
    )

    st.subheader("LLM-derived Confidence Score Distribution (1–10)")
    st.write("\n\n")
    st.warning("LLMs are naturally overconfident. Use with caution.")
    st.write("\n\n")
    st.altair_chart(conf_chart, use_container_width=True)

    # remaining rows after filtering
    st.caption(f"{sum(conf_dist['count']):,} or {round(sum(conf_dist['count']) / len(df_filtered) * 100, 1)}% calls with a confidence score after global filters applied")

    st.divider()