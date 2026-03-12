import streamlit as st

st.logo("supporting/logo.png", size = "large")

with st.sidebar:
    selectbox_option = st.sidebar.selectbox(
    "Looking for something specific?",
    ("Look up an Artist", "Look up an Album", "Look up a Track"),
    index = None,
    placeholder="Look up..."
    )

    st.space("xxlarge")

    if st.sidebar.button(
        label = "Business Tab",
        type = "primary"
    ):
        st.switch_page("pages/4_event_planning.py")


if selectbox_option == "Look up an Artist":
    st.switch_page("pages/1_artist_page.py")
elif selectbox_option == "Look up an Album":
    st.switch_page("pages/2_album_page.py")
elif selectbox_option == "Look up a Track":
    st.switch_page("pages/3_track_page.py")