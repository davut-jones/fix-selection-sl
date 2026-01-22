###############
### imports ###
###############

# standard python imports
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import altair as alt

# customer streamlit views
from views.overview import render as render_overview
from views.label_accuracy import render as render_label_accuracy
from views.fix_analysis import render as render_fix_analysis
from views.raw_data import render as render_raw_data

###########################
### load and cache data ###
###########################

# load functions
@st.cache_data
def load_label_data():
    return pd.read_csv("data/aug_nov_50k_calls.csv")

###################
### page config ###
###################

# dashboard name
dash_name = "Service Checker Call Label Modelling"

# layout and tab title
st.set_page_config(layout="wide", page_title=dash_name)

######################
### authentication ###
######################

# password function
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.password_wrong = False
        st.session_state.password_input = ""

    if not st.session_state.authenticated:
        st.session_state.password_input = st.text_input("Enter dashboard password:", type="password")

        if st.button("Login"):
            if st.session_state.password_input == st.secrets["app_password"]:
                st.session_state.authenticated = True
                st.session_state.password_wrong = False
            else:
                st.session_state.password_wrong = True

        if st.session_state.password_wrong:
            st.error("Wrong password. Please try again.")

        st.stop()

# set auth on and off for dev vs prod
AUTH_ENABLED = False

# run auth if auth variable is true
if AUTH_ENABLED:
    check_password()
else:
    st.session_state.authenticated = True

# only view if authenticated
if st.session_state.authenticated:

    #################################
    ### navigation and main view ####
    #################################

    # sidebar to navigate views
    with st.sidebar:
        selected_view = option_menu(
            menu_title="Dashboard Views",
            options=["Overview","Call Labelling Accuracy", "Fix Analysis", "Raw Label Data"],
            icons=["info-circle","speedometer2", "table", "database"],
            menu_icon="layers",
            default_index=0,
        )

    # dynamic title change for each view
    st.title(selected_view)
    st.divider()

    # view selection
    if selected_view == "Overview":
        render_overview()

    elif selected_view == "Call Labelling Accuracy":
        render_label_accuracy()

    elif selected_view == "Fix Analysis":
        render_fix_analysis()

    elif selected_view == "Raw Label Data":
        render_raw_data()




# # page title
# st.title(dash_name)
# st.write("")
# st.write("")

# # load csv
# df = pd.read_csv("data/aug_nov_50k_calls.csv")

# # # button to show table data
# # if st.button("Show data"):

# ### label and selected outcome split ###
# st.subheader("Label and Selected Outcome Splits")

# # filters
# selected_labels = st.multiselect("Select call issues types", options=sorted(df["label"].unique().tolist()), default=sorted(df["label"].unique().tolist()))

# # filter df
# filtered_df = df[df["label"].isin(selected_labels)]
# st.write(f"Showing {len(filtered_df)} rows remaining after filtering")

# # aggregate for label and selected_outcome view
# grouped = filtered_df.groupby(["label", "selected_outcome_cleaned"]).size().reset_index(name="volume")
# grouped["pct_total_volume"] = grouped["volume"] / grouped["volume"].sum()
# grouped["pct_total_volume"] = (grouped["pct_total_volume"] * 100).round(2)
# grouped["pct_total_volume"] = grouped["pct_total_volume"].map(lambda x: f"{x:.1f}%")
# grouped = grouped.sort_values(by="volume", ascending=False)

# st.dataframe(grouped, height=400)