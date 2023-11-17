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
    if st.session_state['userid'] == None:
        st.warning("먼저 로그인을 하세요.")
        return 

    instr = ""
    submitted = ""
    df = st.session_state['매물']
    with st.form("address_input_form"):
        st.markdown("##### 찾으려는 매물의 주소를 입력하세요.")
        col1, col2 = st.columns([7, 1])

        with col1:
            address = st.text_input(
                label= "주소 입력", value=instr, placeholder=instr, label_visibility="collapsed"
            )

        with col2:
            submitted = st.form_submit_button("검색")

        if submitted:
            df = get_buildings_with_address(address)
            st.session_state['매물'] = df
            if len(df) == 0:
                st.warning("해당 주소의 매물이 존재하지 않습니다.")
        else :
            if df is None :
                df = get_buildings()
                st.session_state['매물'] = df

    df_display = df.rename(columns={
        'building' : '주소', 
        'how' :'용도', 
        'main_how' : '세부 용도', 
        'road_condition' : '대지 요건', 
        'year' : '준공 연도',
        'price' : '매매가',
        'land_ratio' : '건폐율',
        'floor_ratio' : '용적률',
        'up_floor' : '지상',
        'under_floor' : '지하',
        'building_area' : '건물 면적',
        'tran_day' : '?? 일자',
        'register_date' : '매물 등록 일자'})
    
    df_display['매매 희망가'] = 0

    for i, row in df_display.iterrows():
        temp = ""
        price = row['expected_selling_price']
        if  price >= 10000 :
            temp = temp + str(int(price / 100000)) + '억 '
            price = price % 100000
        if price / 10 != 0 :
            temp = temp + str(int(price / 10)) +'만원'
        row['매매 희망가'] = temp
        df_display.iloc[i] = row

    gb = GridOptionsBuilder.from_dataframe(df_display[["주소", "매매 희망가"]])
    gb.configure_selection(selection_mode="single")
    gridOptions = gb.build()

    data = AgGrid(
        df_display,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.MODEL_CHANGED,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        theme= 'material'
    )

    selected_rows = data["selected_rows"]

    if len(selected_rows) != 0:

        # 지도
        # 1.5km 미만인 지하철역 표시
        query = f"match (s:Station)-[rel]-(b:Building) where b.loc =~ '{selected_rows[0]['주소']}'and rel.distance < 1.5 return s, rel, b order by rel.distance;"
        response = common.run_neo4j(query)

        map = folium.Map(location=[selected_rows[0]['lat'], selected_rows[0]['lng']], zoom_start=14, control_scale=True)
        
        feature_group = folium.FeatureGroup("Locations")
        for i, each in enumerate(response):
            stname = each['s']['stname']
            if stname.strip()[-1] != '역' :
                stname = stname + '역'
            distance = str(round(each['rel']['distance'],2)) + 'km'
            html = f"""
                {stname}, {distance} 
                """
            feature_group.add_child(folium.Marker(location=[each['s']['lat'],each['s']['lng']], tooltip=html))
            feature_group.add_child(folium.Marker(location=[each['b']['lat'],each['b']['lng']], icon= folium.Icon(color = 'red'), tooltip=selected_rows[0]['주소']))
        map.add_child(feature_group)

        folium.Circle([selected_rows[0]['lat'], selected_rows[0]['lng']],
                color='tomato',
                radius=1500
              ).add_to(map)
        
        folium_static(map)

        tab1, tab2 = st.tabs(["매물 개요","매물 상세"])
        with tab1:
            col1, col2, col3 = st.columns([6,2,2])

            with col1:
                st.markdown("###### 주소")
                st.markdown(f"{selected_rows[0]['주소']}")
            with col2:
                st.markdown("###### 매매 희망가")
                st.markdown(f"{selected_rows[0]['매매 희망가']}")
            with col3:
                st.markdown("###### 매물 등록 일자")
                st.markdown(f"{selected_rows[0]['매물 등록 일자'][0:10]}")
            st.subheader("")

            # TODO : 건물 가격 그래프를 여기에 넣어야 하나?

            col1, col2 = st.columns([5, 1])
            button = ""
            with col2 :
                button = st.button("계약 체결")

            if button:
                # TODO : 구현 필요
                pass

        with tab2 :
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("###### 용도")
                st.markdown(f"{selected_rows[0]['용도']}")
            with col2:
                st.markdown("###### 세부 용도")
                st.markdown(f"{selected_rows[0]['세부 용도']}")
            with col3:
                st.markdown("###### 대지 요건")
                st.markdown(f"{selected_rows[0]['대지 요건']}")
            with col4:
                st.markdown("###### 준공 연도")
                st.markdown(f"{selected_rows[0]['준공 연도']}년")

            st.subheader("")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("###### 건폐율")
                st.markdown(f"{selected_rows[0]['건폐율']}%")
            with col2:
                st.markdown("###### 용적률")
                st.markdown(f"{selected_rows[0]['용적률']}%")

            st.subheader("")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("###### 지상")
                st.markdown(f"{selected_rows[0]['지상']}층")
            with col2:
                st.markdown("###### 지하")
                st.markdown(f"{selected_rows[0]['지하']}층")
            with col3:
                st.markdown("###### 건물 면적")
                st.markdown(f"{int(selected_rows[0]['건물 면적'])}m2")
            with col4:
                # TODO : 뭔지 알아내야 함
                st.markdown("###### ?? 일자")
                st.markdown(f"{selected_rows[0]['?? 일자']}") 

