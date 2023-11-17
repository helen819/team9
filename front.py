import common
import streamlit as st
import sqlite3
import hashlib
from geopy.geocoders import ArcGIS
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
import pandas as pd
import matplotlib.pyplot as plt
import project as pj


def building_select():
    instr = ""
    submitted = ""
    with st.form("chat_input_form"):
        st.markdown("##### 찾으려는 매물의 주소를 입력하세요.")
        col1, col2 = st.columns([7, 1])

        with col1:
            address = st.text_input(
                instr, value=instr, placeholder=instr, label_visibility="collapsed"
            )

        with col2:
            submitted = st.form_submit_button("검색")

    df = ""
    if submitted:
        df = pj.get_buildings_with_address(address)
        if len(df) == 0:
            st.warning("해당 주소의 매물이 존재하지 않습니다.")
    else:
        df = pj.get_buildings()

    gb = GridOptionsBuilder.from_dataframe(df[["building", "expected_selling_price"]])
    gb.configure_selection(selection_mode="single")
    gridOptions = gb.build()

    data = AgGrid(
        df,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
    )

    selected_rows = data["selected_rows"]

    if len(selected_rows) != 0:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("##### year")
            st.markdown(f":orange[{selected_rows[0]['year']}]")
        with col2:
            st.markdown("##### price")
            st.markdown(f":orange[{selected_rows[0]['price']}]")
        with col3:
            st.markdown("##### land_ratio")
            st.markdown(f":orange[{selected_rows[0]['land_ratio']}]")
        with col4:
            st.markdown("##### floor_ratio")
            st.markdown(f":orange[{selected_rows[0]['floor_ratio']}]")
