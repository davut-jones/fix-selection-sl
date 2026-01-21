import streamlit as st
import pandas as pd
import altair as alt

# page config
st.set_page_config(layout="wide", page_title="SC Fix Selection Dash")

# password
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

check_password()

if st.session_state.authenticated:
    # page title
    st.title("SC Fix Selection Dash")

    # load csv
    df = pd.read_csv("data/aug_nov_50k_calls.csv")

    # button to show table data
    if st.button("Show data"):
        st.markdown(
            """
            <div style="overflow-x: auto;">
                {table}
            </div>
            """.format(table=df.head(3).to_html(index=False)),
            unsafe_allow_html=True
        )
