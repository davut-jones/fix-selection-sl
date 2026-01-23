import streamlit as st

def render_view(df_filtered):

    # page text
    st.header("Header")
    st.write("Explanation")
    # st.dataframe(df_filtered, height=400)