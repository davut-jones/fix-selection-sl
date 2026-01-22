import streamlit as st

def render_view(df_filtered):

    st.divider()

    st.write("")
    st.write(
        """
        This dashboard evaluates the performance and usage of the **Service Checker Call Label modelling** approach.
        
        Calls are processed using a **large language model (LLM)** to assign labels aligned to the **IHH MOTs**. 
        These labels are then used to train machine learning models to predict call issue categories at scale. 
        A proof of concept (POC) has already been built and the models show strong performance.
        
        The goal of this dashboard is to:
        - **Assess label accuracy** against ground truth sources  
        - **Understand which customer outcomes** should be offered for each label based on key operational KPIs
        """
    )

    st.divider()

    # --- native cards ---
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container():
            st.markdown(
                """
                <span style="font-size: 24px;">
                    <i class="bi bi-speedometer2"></i>
                </span>
                """,
                unsafe_allow_html=True
            )
            st.subheader("Call Labelling Accuracy")
            st.write(
                "Compare **LLM-derived labels** against **CSG call reasons** and **engineer notes** to assess accuracy."
            )
            with st.expander("More detail"):
                st.write(
                    """
                    Engineer notes are considered the most reliable source as they reflect the on-site diagnosis.
                    High agreement indicates strong label accuracy and model validity.
                    """
                )

    with col2:
        with st.container():
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
                "Slice the data to create risk tiers and determine the right customer outcome."
            )
            with st.expander("More detail"):
                st.write(
                    """
                    Build risk tiers based on KPI impacts:
                    - **Low**: default outcome  
                    - **Medium**: agent can override  
                    - **High**: escalate to Tier 2
                    """
                )

    with col3:
        with st.container():
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
                "Inspect raw labels, evidence, confidence, and outcomes for manual validation."
            )
            with st.expander("More detail"):
                st.write(
                    """
                    View the raw labelled dataset including LLM evidence and confidence scores to verify model outputs.
                    """
                )
