import streamlit as st
import pandas as pd

def render_view():

    vol_formatted = f"{st.session_state['df_label_total_rows'] / 1000:.1f}k"
    start_month_year = pd.to_datetime(st.session_state["df_label_min_dt"]).strftime("%b %y")
    end_month_year = pd.to_datetime(st.session_state["df_label_max_dt"]).strftime("%b %y")

    st.write("\n\n")
    st.write(
        f"""
        This dashboard provides background context and guidance for Data Science work into
        **Service Checker Call Label Modelling**.

        **{vol_formatted} Service Checker Hub 4 calls** between **{start_month_year}** and **{end_month_year}** were processed
        separately prior to this dashboard using a **large language model (LLM)** to assign
        **call issue labels** aligned to the **Service Checker IHH MOTs**. These labels represent
        the underlying **Wi-Fi-related issues** that may drive customers to contact us.

        This dashboard is built on top of that labelled dataset and is used to support
        analysis, validation, and decision-making. All volumes and metrics shown reflect
        the **currently applied global filters**.
        
        The dashboard focuses on two core objectives:
        - **Assessing the quality and consistency of the LLM-derived call issue labels**, using
          available operational signals such as **engineer notes** and **CSG call reasons**, and  
        - **Comparing how different customer outcomes perform** for a given issue label, using
          operational KPIs including **repeat calls**, **BB churn**, and **cost**

        Outcome analysis in this dashboard is **descriptive rather than causal**. It shows how
        outcomes have historically performed for similar calls, but does not imply that an
        outcome directly causes a change in customer behaviour.

        Once sufficient confidence is established in **(1) the call issue labels** and
        **(2) the relative performance of outcomes**, these insights can be used to support
        **predictive machine learning (ML) models**. A proof of concept has already been
        completed to assess the feasibility of predicting issue occurrence ahead of contact.
        """
    )

    st.divider()

    ######################
    ### 2x2 grid cards ###
    ######################

    st.subheader("Sections")
    st.write("\n\n")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div style="background:#aec7e8; padding:15px; border-radius:5px; text-align:center;">
                <h3 style="margin:0 0 .6rem; color:#FAF9F6; line-height:1;">Overview</h3>
                <p style="margin:0; color:#FAF9F6;">High-level summaries of call issues, customer outcomes, and key metrics</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("\n\n")
        with st.expander("More detail"):
            st.write(
                """
                This section provides a starting point for exploring the data, highlighting
                common call issue types, outcome distributions, and headline trends before
                deeper analysis.
                """
            )
        st.write("\n\n")

    with col2:
        st.markdown(
            f"""
            <div style="background:#c5b0d5; padding:15px; border-radius:5px; text-align:center;">
                <h3 style="margin:0 0 .6rem; color:#FAF9F6; line-height:1;">Label Evaluation</h3>
                <p style="margin:0; color:#FAF9F6;">Evaluate how well LLM-generated call issue labels reflect real customer issues</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("\n\n")
        with st.expander("More detail"):
            st.write(
                """
                Label evaluation compares LLM-derived labels with other operational signals,
                including **engineer-reported symptoms** and **CSG call reasons** where available.

                These signals are not available for all calls, but provide a strong reference
                point for assessing consistency and reliability of the labelling approach.
                """
            )
        st.write("\n\n")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(
            f"""
            <div style="background:#ffbb78; padding:15px; border-radius:5px; text-align:center;">
                <h3 style="margin:0 0 .6rem; color:#FAF9F6; line-height:1;">Outcome Analysis</h3>
                <p style="margin:0; color:#FAF9F6;">Explore how different customer outcomes perform for each call issue label</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("\n\n")
        with st.expander("More detail"):
            st.write(
                """
                This section supports comparison of outcomes using operational KPIs such as
                repeat calls, BB churn, and cost.

                Outcomes are assessed based on observed historical performance and grouped
                into **low**, **medium**, and **high** risk tiers to support decision-making.
                """
            )
        st.write("\n\n")

    with col4:
        st.markdown(
            f"""
            <div style="background:#ff9896; padding:15px; border-radius:5px; text-align:center;">
                <h3 style="margin:0 0 .6rem; color:#FAF9F6; line-height:1;">Raw Label Data</h3>
                <p style="margin:0; color:#FAF9F6;">Inspect the underlying labelled dataset used throughout the dashboard</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("\n\n")
        with st.expander("More detail"):
            st.write(
                """
                This section exposes the raw data behind the analysis, enabling manual
                inspection and validation of:
                - Call issue labels  
                - Supporting evidence  
                - Selected outcomes  
                - Customer behaviours such as repeat calls and BB churn
                """
            )
        st.write("\n\n")
