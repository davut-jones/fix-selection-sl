import streamlit as st
import pandas as pd
import altair as alt

st.title("Dashboard Test")

# Load CSV
df = pd.read_csv("data/aug_nov_50k_calls.csv")

if st.button("Show data"):
    st.markdown(
        """
        <div style="overflow-x: auto;">
            {table}
        </div>
        """.format(table=df.head(3).to_html(index=False)),
        unsafe_allow_html=True
    )

