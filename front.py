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
import random
import altair as alt
from itertools import cycle
from PIL import Image

seoul_address = {}

def get_buildings() :
    return common.postgres_select(f"SELECT * FROM transactions t, building b WHERE t.building = b.loc and t.buyer IS NULL ORDER BY t.register_date desc limit 100")

def get_buildings_with_address(address) :
    return common.postgres_select(f"SELECT * FROM transactions t, building b WHERE t.building = b.loc and t.building like '%{address}%'")

def get_address2_select_option() :
    return common.postgres_select("""select
                                            distinct address2
                                        from
                                            address a
                                        where
                                            address2 != ''
                                        order by address2;""")

def get_address3_select_option(address2) :
    return common.postgres_select(f"""select
                                            distinct address3
                                        from
                                            address a
                                        where
                                            address2 = '{address2}'
                                        order by address3;""")

def get_transaction_strength_by_address3() :
    return common.postgres_select("""select sub.*, a.center_lat ,a.center_lng 
                                    from (
                                    select
                                        split_part(b.loc,' ', 1) as address1,
                                        split_part(b.loc,' ', 2) as address2,
                                        split_part(b.loc,' ', 3) as address3,
                                        count(*) as strength
                                    from
                                        building b,
                                        transactions t
                                    where
                                        b.loc = t.building
                                    and t.conclusion_date is null
                                    group by
                                        split_part(b.loc,' ', 1),
                                        split_part(b.loc,' ', 2),
                                        split_part(b.loc,' ', 3)
                                        ) as sub, address a
                                    where sub.address1 = a.address1  and sub.address2 = a.address2 and sub.address3 = a.address3 ;  """)

def get_buildings_with_seperate_address1(address1) :
    return common.postgres_select(f"""select
                                        *
                                    from
                                        building b,
                                        transactions t,
                                        address a
                                    where
                                        b.loc = t.building
                                    and a.address1  = split_part(b.loc,' ', 1)
                                    and a.address2  = split_part(b.loc,' ', 2)
                                    and a.address3  = split_part(b.loc,' ', 3)
                                    and t.conclusion_date is null
                                    and split_part(b.loc,' ', 1) = '{address1}';  """)  

def get_buildings_with_seperate_address2(address1, address2) :
    return common.postgres_select(f"""select
                                        *
                                    from
                                        building b,
                                        transactions t,
                                        address a
                                    where
                                        b.loc = t.building
                                    and a.address1  = split_part(b.loc,' ', 1)
                                    and a.address2  = split_part(b.loc,' ', 2)
                                    and a.address3  = split_part(b.loc,' ', 3)
                                    and t.conclusion_date is null
                                    and split_part(b.loc,' ', 1) = '{address1}'
                                    and split_part(b.loc,' ', 2) = '{address2}';  """)  

def get_buildings_with_seperate_address3(address1, address2, address3) :
    return common.postgres_select(f"""select
                                        *
                                    from
                                        building b,
                                        transactions t,
                                        address a
                                    where
                                        b.loc = t.building
                                    and a.address1  = split_part(b.loc,' ', 1)
                                    and a.address2  = split_part(b.loc,' ', 2)
                                    and a.address3  = split_part(b.loc,' ', 3)
                                    and t.conclusion_date is null
                                    and split_part(b.loc,' ', 1) = '{address1}'
                                    and split_part(b.loc,' ', 2) = '{address2}'
                                    and split_part(b.loc,' ', 3) = '{address3}';  """)   

def get_transaction_count_by_address2() :
    return common.postgres_select("""select
                                        split_part(b.loc, ' ', 1) as address1,
                                        split_part(b.loc, ' ', 2) as address2,
                                        count(*)
                                    from
                                        building b,
                                        transactions t
                                    where
                                        b.loc = t.building
                                         and t.conclusion_date is null
                                    group by
                                        split_part(b.loc, ' ', 1),
                                        split_part(b.loc, ' ', 2)
                                  order by
                                        count(*) desc
                                    limit 5;""")   
    
def change_address3():
    st.session_state['읍/면/동'] = get_address3_select_option(st.session_state.key2)
    st.session_state['읍/면/동'].loc[0] = "읍/면/동"

def dashboard():
    submitted = ""

    # st.markdown("##### 찾으려는 매물의 주소를 입력하세요.")
    
    col1, col2, col3, col4 = st.columns([2,2,2,1])
    
    select2_option = get_address2_select_option()
    select2_option.loc[0] = "군/구"
    with col1:
        key1 = st.selectbox(placeholder="서울특별시", label="address1", label_visibility="collapsed", options=["서울특별시"])
    with col2:
        key2 = st.selectbox(placeholder="군/구", label="address2", label_visibility='collapsed', options=select2_option, on_change=change_address3, key="key2")
    with col3:
        key3 = st.selectbox(placeholder="읍/면/동", label="address3", label_visibility='collapsed', options=st.session_state['읍/면/동'])
    with col4:
        submitted = st.button("검색")
    seoul_lat = 37.56661
    seoul_lng = 126.978386

    if submitted :
        df = ""
        zoom_start = 11
        if key2 == '군/구': 
            df = get_buildings_with_seperate_address1(key1)
        elif key3 == '읍/면/동' :
            df = get_buildings_with_seperate_address2(key1, key2)
            zoom_start = 13
        else :
            df = get_buildings_with_seperate_address3(key1, key2, key3)
            zoom_start = 13
        
        if df.shape[0] > 0:
            seoul_lat = df.iloc[0]['center_lat']
            seoul_lng = df.iloc[0]['center_lng']

        map = folium.Map(location=[seoul_lat, seoul_lng], zoom_start=zoom_start, tiles = 'cartodbpositron')

        for i, each in df.iterrows():
            html = f"""
                    {each['loc']}
                    """
            folium.Circle([each['lat'], each['lng']],
                    color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]),
                    # fill_color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]),
                    fill= True,
                    radius=100,
                    fill_opacity= 0.8,
                    tooltip=html
                    ).add_to(map)
        folium_static(map)

    else :
        map = folium.Map(location=[seoul_lat, seoul_lng], zoom_start=11, tiles = 'cartodbpositron')
        df = st.session_state['대시보드_지도'] 
        if df is None :
            df = get_transaction_strength_by_address3()
            st.session_state['대시보드_지도'] = df
            color_list = []
            for i in range(df.shape[0]) :
                color_list.append("#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]))
            st.session_state['대시보드_지도_색깔'] = color_list
        for i, each in df.iterrows():
            html = f"""
                    {each['address3']}, 매물 {each['strength']}건 
                    """
            folium.Circle([each['center_lat'], each['center_lng']],
                    color = st.session_state['대시보드_지도_색깔'][i],
                    # fill_color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]),
                    fill= True,
                    radius=1000*each['strength'],
                    fill_opacity= 0.8,
                    tooltip=html
                    ).add_to(map)
            
        folium_static(map)  

    col1, col2 = st.columns(2)
    with col1 :
        with st.container() :
            
            st.markdown("##### 시/군/구별 거래 건수 Top 5")
            df_left = get_transaction_count_by_address2()
            df_left = df_left.rename(columns={
                                            'address1' : '시/도', 
                                            'address2' : '시/군/구', 
                                            'count' : '거래 건수'})
            chart = alt.Chart(df_left).mark_bar().encode(
                x='시/군/구',
                y=alt.Y('거래 건수', scale=alt.Scale(domain=[0, df_left.loc[0,'거래 건수'] +1 ], clamp=True)),
                color= '시/군/구'
            ).configure_axisX(labelAngle=0).configure_legend(disable=True).configure_range("diverging")
            st.altair_chart(chart, theme='streamlit', use_container_width=True)

            
            st.dataframe(df_left, use_container_width=True, hide_index= True)

    with col2 :
         with st.container() :
            # TODO : 가격 상승률로 변경해야 함
            st.markdown("##### 시/군/구별 1년뒤 가격상승률 Top 5")
            df_right = get_transaction_count_by_address2()
            df_right = df_right.rename(columns={
                                            'address1' : '시/도', 
                                            'address2' : '시/군/구', 
                                            'count' : '상승률 평균'})
            chart = alt.Chart(df_right).mark_bar().encode(
                x='시/군/구',
                y=alt.Y('상승률 평균', scale=alt.Scale(domain=[0, df_right.loc[0,'상승률 평균'] +1 ], clamp=True)),
                color= '시/군/구',
            ).configure_axisX(labelAngle=0).configure_legend(disable=True).configure_range("diverging")
            st.altair_chart(chart, theme='streamlit', use_container_width=True)

            st.dataframe(df_right, use_container_width=True, hide_index= True)


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
        theme= 'material',
        height= 500
    )

    selected_rows = data["selected_rows"]

    if len(selected_rows) != 0:

        # 지도
        # 1.5km 미만인 지하철역 표시
        query = f"match (s:Station)-[rel]-(b:Building) where b.loc =~ '{selected_rows[0]['주소']}'and rel.distance < 1.5 return s, rel, b order by rel.distance;"
        response = common.run_neo4j(query)

        map = folium.Map(location=[selected_rows[0]['lat'], selected_rows[0]['lng']], zoom_start=14)
        
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

            filteredImages = ['1.png','2.png','3.png','4.png','5.png','6.png'] # your images here
            cols = cycle(st.columns(3)) # st.columns here since it is out of beta at the time I'm writing this
            for idx, filteredImage in enumerate(filteredImages):
                image = Image.open(filteredImage)
                new_image = image.resize((400, 600))
                next(cols).image(new_image, use_column_width=True)

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

def my_info() :
    # TODO : DB에서 조회하는 것으로 변경
    st.markdown("#### 내 거래내역")
    df = pd.DataFrame({'주소' : ['서울특별시 강남구 역삼동 830-59번지', '서울특별시 강남구 청담동 38-1번지'], '상태' : ['거래 완료','매물 등록'],'매물 등록일자' : ['2022-11-23', '2023-11-20'], '거래 완료일자' : ['2023-01-01',' '], '매매 희망가' : ['5억 4321만원','60억'], '체결 금액' :['5억 4321만원',' '] })
    st.dataframe(df,hide_index=True, use_container_width=True)

    st.container()
    st.markdown("#### 보험료 납입내역")
    col1, col2, col3, col4 = st.columns(4)
    with col1 :
        st.markdown("###### 거래 체결 금액")
        st.markdown("5억 4321만원")
    with col2 :
        st.markdown("###### 예측 가격")
        st.markdown("6억 4321만원")
    with col3 :
        st.markdown("###### 현재 가격")
        st.markdown("5억 9321만원")
    with col4 :
        st.markdown("###### 보험료 총 납입 금액")
        st.markdown("1100만원")
    
    col1, col2= st.columns([4,6])
    with col2 :
        st.markdown("##### 받으실 수 있는 보험금은 총 ???만원입니다.")

    df2 = pd.DataFrame({ '주소' : ['서울특별시 강남구 역삼동 830-59번지','서울특별시 강남구 역삼동 830-59번지','서울특별시 강남구 역삼동 830-59번지','서울특별시 강남구 역삼동 830-59번지','서울특별시 강남구 역삼동 830-59번지','서울특별시 강남구 역삼동 830-59번지','서울특별시 강남구 역삼동 830-59번지','서울특별시 강남구 역삼동 830-59번지','서울특별시 강남구 역삼동 830-59번지','서울특별시 강남구 역삼동 830-59번지','서울특별시 강남구 역삼동 830-59번지'], 
                        '납입 일자' : ['2023-11-01','2023-10-01','2023-09-01','2023-08-01','2023-07-01','2023-06-01','2023-05-01','2023-04-01','2023-03-01','2023-02-01','2023-01-01'],
                        '납입 금액' : ['100만원','100만원','100만원','100만원','100만원','100만원','100만원','100만원','100만원','100만원','100만원']})
    st.dataframe(df2,hide_index=True, use_container_width=True)
    col1, col2 = st.columns([5, 1])
    button = ""
    with col2 :
        button = st.button("보험금 청구")
    if button:
        # TODO : 구현 필요
        pass
