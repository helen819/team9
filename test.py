import common
import streamlit as st

with st.form("my_form1"):
    sid = st.text_input('Student ID:', autocomplete="on", placeholder="학번입력", max_chars=10)
    submitted = st.form_submit_button("조회")
    if submitted:
        query = f"SELECT * FROM student WHERE sid = '{sid}'"
        st.write(common.postgres_select(query))