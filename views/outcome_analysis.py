import streamlit as st
import pandas as pd

def render_view(df_filtered):

    # Persist view mode across reruns
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "Single table"

    # view titles
    st.subheader("Outcome breakdown by call issue label")
    st.write("For each call issue label evaluate selected outcome performance via repeat calls and churn")

    # view toggle
    view_mode = st.radio(
        "Choose view type:",
        options=["Single table", "Table per call issue label"],
        index=0,
        key="view_mode"
    )

    # aggregate for label and selected_outcome view
    df_grouped = df_filtered.groupby(["label", "selected_outcome_cleaned"]).size().reset_index(name="volume")

    # % of filtered total
    df_grouped["pct_total_volume"] = df_grouped["volume"] / df_grouped["volume"].sum()
    df_grouped["pct_total_volume"] = (df_grouped["pct_total_volume"] * 100).round(1)

    # % of all unfiltered calls
    total_all = st.session_state.get("df_label_total_rows", len(df_filtered))
    df_grouped["pct_total_all"] = (df_grouped["volume"] / total_all * 100).round(1)

    # format percentage with % marks
    df_grouped["pct_total_volume"] = df_grouped["pct_total_volume"].map(lambda x: f"{x:.1f}%")
    df_grouped["pct_total_all"] = df_grouped["pct_total_all"].map(lambda x: f"{x:.1f}%")

    # reset index
    df_grouped = df_grouped.sort_values(by="volume", ascending=False).reset_index(drop=True)

    # rename columns
    df_grouped = df_grouped.rename(columns={
        "label": "Call issue label",
        "selected_outcome_cleaned": "Selected outcome",
        "volume": "Volume",
        "pct_total_volume": "% of filtered",
        "pct_total_all": "% of all calls"
    })

    # single table view
    if view_mode == "Single table":
        st.dataframe(df_grouped, use_container_width=True)

    # expandable per label view
    else:
        labels = df_grouped["Call issue label"].unique()
        for label in labels:
            with st.expander(label):
                df_label_group = df_grouped[df_grouped["Call issue label"] == label]
                st.dataframe(df_label_group, use_container_width=True)

    # remaining rows after filtering
    st.caption(f"{len(df_filtered):,} rows remaining after filtering")

    st.divider()