import streamlit as st
import pandas as pd
import altair as alt

st.title("Dashboard Test")

# Load CSV
df = pd.read_csv("data.csv")

st.markdown(
    """
    <div style="overflow-x: auto;">
        {table}
    </div>
    """.format(table=df.head(3).to_html(index=False)),
    unsafe_allow_html=True
)

# st.table(df.head(10))

# # Filter by category (change "Category" to your column name)
# category = st.selectbox("Category", ["All"] + list(df["Category"].unique()))

# if category != "All":
#     df = df[df["Category"] == category]

# st.write(df)

# # Simple chart
# chart = alt.Chart(df).mark_bar().encode(
#     x="Category:N",
#     y="Value:Q"
# )

# st.altair_chart(chart, use_container_width=True)
