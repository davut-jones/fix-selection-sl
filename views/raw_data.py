import streamlit as st

def render_view(df_filtered):

    # page text
    st.write("\n\n")
    st.markdown(
        '<span style="font-size: 1.1rem; font-weight: 400;">Raw data is displayed below for manual validation and debugging.</span>',
        unsafe_allow_html=True
    )
    st.divider()
