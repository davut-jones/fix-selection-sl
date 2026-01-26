###############
### imports ###
###############

# standard python imports
import streamlit as st
from streamlit_option_menu import option_menu  # type: ignore
import pandas as pd

# customer streamlit views
from views.background import render_view as render_background
from views.overview import render_view as render_overview
from views.label_evaluation import render_view as render_label_evaluation
from views.outcome_analysis import render_view as render_outcome_analysis
from views.raw_data import render_view as render_raw_data

###################
### page config ###
###################

# dashboard name
dash_name = "Service Checker Call Label Modelling"

# layout and tab title
st.set_page_config(layout="wide", page_title=dash_name)

# markdown for bootstrap icons
st.markdown(
    """
    <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    """,
    unsafe_allow_html=True
)

###########################
### load and cache data ###
###########################

# load functions
@st.cache_data
def load_label_data():
    df = pd.read_csv(
        "data/aug_nox_50k_calls_all_data.csv",
        dtype={
            "other_label": "string"
        }
    )
    df["call_date"] = pd.to_datetime(df["call_date"]).dt.date
    return df

# load data
df_label = load_label_data()

# store variable with total rows
st.session_state["df_label_total_rows"] = len(df_label)
st.session_state["df_label_min_dt"] = df_label["call_date"].min()
st.session_state["df_label_max_dt"] = df_label["call_date"].max()

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

    # define global filter options
    label_options = sorted(df_label["label"].dropna().unique().tolist())
    outcome_options = sorted(df_label["selected_outcome_cleaned"].dropna().unique().tolist())

    # initialise session state for filters
    if "selected_labels" not in st.session_state:
        st.session_state.selected_labels = label_options

    if "selected_outcomes" not in st.session_state:
        st.session_state.selected_outcomes = outcome_options

    # force list type (prevents single-select UI bug)
    st.session_state.selected_labels = list(st.session_state.selected_labels)
    st.session_state.selected_outcomes = list(st.session_state.selected_outcomes)

    # reset state if options changed (deploy / data updates)
    if set(st.session_state.selected_labels) - set(label_options):
        st.session_state.selected_labels = label_options

    if set(st.session_state.selected_outcomes) - set(outcome_options):
        st.session_state.selected_outcomes = outcome_options

    # date range filter setup
    min_date = st.session_state["df_label_min_dt"]
    max_date = st.session_state["df_label_max_dt"]

    if "start_date" not in st.session_state:
        st.session_state.start_date = min_date

    if "end_date" not in st.session_state:
        st.session_state.end_date = max_date

    # sidebar to navigate views
    with st.sidebar:
        selected_view = option_menu(
            menu_title="Sections",
            options=["Background", "Overview", "Label Evaluation", "Outcome Analysis", "Raw Label Data"],
            icons=["info-circle", "card-checklist", "speedometer2", "table", "database"],
            menu_icon="layers",
            default_index=0,
            key="selected_view"
        )

        if selected_view != "Background":

            # global filters (only for non-overview views)
            st.write("")
            st.write("## Global Filters")

            if st.button("Reset all filters"):
                st.session_state.selected_labels = label_options
                st.session_state.selected_outcomes = outcome_options
                st.session_state.start_date = min_date
                st.session_state.end_date = max_date

            # Date filters
            st.date_input(
                "Start of period:",
                min_value=min_date,
                max_value=max_date,
                key="start_date"
            )

            st.date_input(
                "End of period:",
                min_value=min_date,
                max_value=max_date,
                key="end_date"
            )

            # call issue label filter
            st.multiselect(
                f"Select call issue labels ({len(st.session_state.selected_labels)} selected):",
                options=label_options,
                key="selected_labels"
            )

            # selected outcome filter
            st.multiselect(
                f"Select outcomes ({len(st.session_state.selected_outcomes)} selected):",
                options=outcome_options,
                key="selected_outcomes"
            )

    # apply filters
    if selected_view == "Background":
        df_filtered = df_label.copy()
    else:
        df_filtered = df_label[
            (df_label["label"].isin(st.session_state.selected_labels)) &
            (df_label["selected_outcome_cleaned"].isin(st.session_state.selected_outcomes)) &
            (df_label["call_date"].between(
                st.session_state.start_date,
                st.session_state.end_date
            ))
        ]

    # dynamic title change for each view
    st.title(
        "Service Checker Call Label Modelling"
        if selected_view == "Background"
        else selected_view
    )

    # view selection
    if selected_view == "Background":
        render_background(df_label)

    elif selected_view == "Overview":
        render_overview(df_filtered)

    elif selected_view == "Label Evaluation":
        render_label_evaluation(df_filtered)

    elif selected_view == "Outcome Analysis":
        render_outcome_analysis(df_filtered)

    elif selected_view == "Raw Label Data":
        render_raw_data(df_filtered)
