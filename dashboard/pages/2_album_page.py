import streamlit as st

st.logo("supporting/logo.png", size = "large")
if st.sidebar.button("Business Tab"):
    st.session_state["play_event_planning_intro"] = True
    st.switch_page("pages/4_event_planning.py")
