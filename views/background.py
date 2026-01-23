import streamlit as st

def render_view(df_filtered):

    st.write("\n\n\n\n")
    st.write(
        """
        This dashboard provides background context and guidance for the **Service Checker Call Label Modelling** work.

        Customer calls are processed using a **large language model (LLM)** to assign **call issue labels** aligned to the
        **IHH MOTs**. These labels represent the underlying reason for a customer contacting us due to Broadband issues.

        The labelled data supports two key objectives:
        - **Evaluating the quality and reliability of LLM-derived labels**, and  
        - **Understanding which customer outcomes should be offered** when a given issue is identified, based on
          operational KPIs such as churn, repeat calls, and net change in £.

        This dashboard brings those elements together to support decision-making, validation, and future automation.
        """
    )

    st.divider()

    # --- 2x2 grid cards ---
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <span style="font-size: 24px;">
                <i class="bi bi-card-checklist"></i>
            </span>
            """,
            unsafe_allow_html=True
        )
        st.subheader("Overview")
        st.write(
            "High-level summaries of call issues, outcomes, and key metrics to understand the landscape."
        )
        with st.expander("More detail"):
            st.write(
                """
                This section provides a starting point for exploring the data, highlighting
                common call issue types, outcome distributions, and headline trends before
                deeper analysis.
                """
            )

    with col2:
        st.markdown(
            """
            <span style="font-size: 24px;">
                <i class="bi bi-speedometer2"></i>
            </span>
            """,
            unsafe_allow_html=True
        )
        st.subheader("Label Evaluation")
        st.write(
            "Assess how well LLM-generated call labels reflect real customer issues."
        )
        with st.expander("More detail"):
            st.write(
                """
                Label evaluation focuses on comparing LLM-derived labels with available
                ground truth sources, such as **engineer notes** and **CSG call reasons**.

                Engineer notes are treated as the strongest signal, as they reflect the
                on-site diagnosis of the issue. High agreement builds confidence in the
                labelling approach.
                """
            )

    st.write("")  # spacing

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(
            """
            <span style="font-size: 24px;">
                <i class="bi bi-table"></i>
            </span>
            """,
            unsafe_allow_html=True
        )
        st.subheader("Outcome Analysis")
        st.write(
            "Explore which outcomes should be offered for each call issue label."
        )
        with st.expander("More detail"):
            st.write(
                """
                This section supports slicing and dicing the data to understand the
                operational impact of different outcomes.

                Users can assess risk across KPIs and group customers into tiers:
                - **Low risk** – default outcome  
                - **Medium risk** – agent discretion  
                - **High risk** – escalation to Tier 2
                """
            )

    with col4:
        st.markdown(
            """
            <span style="font-size: 24px;">
                <i class="bi bi-database"></i>
            </span>
            """,
            unsafe_allow_html=True
        )
        st.subheader("Raw Label Data")
        st.write(
            "Access the underlying labelled dataset for detailed inspection and validation."
        )
        with st.expander("More detail"):
            st.write(
                """
                This section exposes the raw data used throughout the dashboard, including:
                - Call issue labels  
                - LLM-generated evidence  
                - Confidence scores  
                - Selected customer outcomes  

                It enables manual spot-checking and deeper investigation where required.
                """
            )
