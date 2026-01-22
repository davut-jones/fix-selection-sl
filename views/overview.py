import streamlit as st

def render_view(df):
    st.header("Header")
    st.write("Explanation")
    st.dataframe(df, height=400)