import common
import streamlit as st
import sqlite3
import hashlib
from geopy.geocoders import ArcGIS
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import folium
from streamlit_folium import st_folium, folium_static

def get_buildings() :
    return common.postgres_select(f"SELECT * FROM transactions t, building b WHERE t.building = b.loc and t.buyer IS NULL ORDER BY t.register_date desc limit 100")

def get_buildings_with_address(address) :
    return common.postgres_select(f"SELECT * FROM transactions t, building b WHERE t.building = b.loc and t.building like '%{address}%'")

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
        df = get_buildings_with_address(address)
        if len(df) == 0:
            st.warning("해당 주소의 매물이 존재하지 않습니다.")
    else:
        df = get_buildings()

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

        # 지도
        # 1.5km 미만인 지하철역 표시
        query = f"match (s:Station)-[rel]-(b:Building) where b.loc =~ '{selected_rows[0]['building']}'and rel.distance < 1.5 return s, rel, b order by rel.distance;"
        response = common.run_neo4j(query)

        map = folium.Map(location=[selected_rows[0]['lat'], selected_rows[0]['lng']], zoom_start=14, control_scale=True)
        
        feature_group = folium.FeatureGroup("Locations")
        for i, each in enumerate(response):
            stname = each['s']['stname']
            if stname.strip()[-1] != '역' :
                stname = stname + '역'
            html = f"""
                {stname}
                """
            feature_group.add_child(folium.Marker(location=[each['s']['lat'],each['s']['lng']], tooltip=html))
            feature_group.add_child(folium.Marker(location=[each['b']['lat'],each['b']['lng']], icon= folium.Icon(color = 'red')))
        map.add_child(feature_group)

        folium.Circle([selected_rows[0]['lat'], selected_rows[0]['lng']],
                color='tomato',
                radius=1500
              ).add_to(map)
        
        folium_static(map)

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
