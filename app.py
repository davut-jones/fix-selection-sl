import streamlit as st
import pandas as pd
import altair as alt

### page config ###

# layout and tab title
st.set_page_config(layout="wide", page_title="SC Fix Selection Dashboard")

### authentication ###

# # password
# def check_password():
#     if "authenticated" not in st.session_state:
#         st.session_state.authenticated = False
#         st.session_state.password_wrong = False
#         st.session_state.password_input = ""

#     if not st.session_state.authenticated:
#         st.session_state.password_input = st.text_input("Enter dashboard password:", type="password")

#         if st.button("Login"):
#             if st.session_state.password_input == st.secrets["app_password"]:
#                 st.session_state.authenticated = True
#                 st.session_state.password_wrong = False
#             else:
#                 st.session_state.password_wrong = True

#         if st.session_state.password_wrong:
#             st.error("Wrong password. Please try again.")

#         st.stop()
# check_password()

### main view ####

# # only view if authenticated
# if st.session_state.authenticated:

# page title
st.title("SC Fix Selection Dashboard")
st.write("")
st.write("")

# load csv
df = pd.read_csv("data/aug_nov_50k_calls.csv")

# # button to show table data
# if st.button("Show data"):

### label and selected outcome split ###
st.subheader("Label and Selected Outcome Splits")

# filters
selected_labels = st.multiselect("Select call issues types", options=sorted(df["label"].unique().tolist()), default=sorted(df["label"].unique().tolist()))

# filter df
filtered_df = df[df["label"].isin(selected_labels)]
st.write(f"Showing {len(filtered_df)} rows remaining after filtering")

# aggregate for label and selected_outcome view
grouped = filtered_df.groupby(["label", "selected_outcome_cleaned"]).size().reset_index(name="volume")
grouped["pct_total_volume"] = grouped["volume"] / grouped["volume"].sum()
grouped["pct_total_volume"] = (grouped["pct_total_volume"] * 100).round(2)
grouped["pct_total_volume"] = grouped["pct_total_volume"].map(lambda x: f"{x:.1f}%")
grouped = grouped.sort_values(by="volume", ascending=False)

st.dataframe(grouped, height=400)