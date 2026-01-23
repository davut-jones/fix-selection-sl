import streamlit as st

PRIMARY_COLOR = "#5A67D8"

def custom_header(text: str):
    st.markdown(
        f"<h1 style='color:{PRIMARY_COLOR}; font-weight:700; margin-bottom: 0.2em;'>{text}</h1>",
        unsafe_allow_html=True
    )

def custom_subheader(text: str):
    st.markdown(
        f"<h2 style='color:{PRIMARY_COLOR}; font-weight:700; margin-top: 0.5em;'>{text}</h2>",
        unsafe_allow_html=True
    )