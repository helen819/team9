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
import folium.features
from streamlit_folium import st_folium, folium_static
import random
import altair as alt
from itertools import cycle
from PIL import Image
import math
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import project
import os

radio1 = "권리조사 및 법무사 과실담보"
radio2 = "예측결과 정확도 담보"
radio3 = "보험 가입 안함"

def get_buildings() :
    return common.postgres_select("""
                                    select
                                        *,
                                        case
                                            when register_date is null then '미등록'
                                            when conclusion_date is not null then '거래 완료'
                                            else '등록'
                                        end as transaction_status
                                    from
                                        transactions t
                                    right outer join building as b on
                                        t.building = b.loc
                                    where year1 is not null
                                      and year1 != 0
                                    order by
                                        t.conclusion_date, t.register_date, b.tran_day desc
                                    limit 200;                                
                                    """)

def get_buildings_with_address(address) :
    return common.postgres_select(f"""
                                  select
                                        *,
                                        case
                                            when register_date is null then '미등록'
                                            when conclusion_date is not null then '거래 완료'
                                            else '등록'
                                        end as transaction_status
                                    from
                                        transactions t
                                    right outer join building as b on
                                        t.building = b.loc
                                    where b.loc like '%{address}%'
                                      and year1 is not null
                                      and year1 != 0
                                    order by
                                        t.conclusion_date, t.register_date, b.tran_day desc ;
                                  """)

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

def update_transaction(insurance_amount) :   
    if st.session_state['보험유형'] == radio1 :
        common.postgres_update(f"""insert
                                    into
                                    insurance
                                    (insurance_id,
                                    insurance_userid,
                                    building,
                                    payment_date,
                                    payment_amount,
                                    payment_complete,
                                    year1,
                                    year2,
                                    year3,
                                    year4,
                                    year5,
                                    year6,
                                    year7,
                                    year8,
                                    year9,
                                    year10,
                                    insurance_type)
                                    values(nextval('seq_insurance_id'),
                                    '{st.session_state["userid"]}',
                                    '{st.session_state["계약 빌딩"]["building"]}',
                                    '{datetime.today().strftime("%Y-%m-%d")}',
                                    {insurance_amount},
                                    'Y',
                                    {st.session_state["계약 빌딩"]["year1"]},
                                    {st.session_state["계약 빌딩"]["year2"]},
                                    {st.session_state["계약 빌딩"]["year3"]},
                                    {st.session_state["계약 빌딩"]["year4"]},
                                    {st.session_state["계약 빌딩"]["year5"]},
                                    {st.session_state["계약 빌딩"]["year6"]},
                                    {st.session_state["계약 빌딩"]["year7"]},
                                    {st.session_state["계약 빌딩"]["year8"]},
                                    {st.session_state["계약 빌딩"]["year9"]},
                                    {st.session_state["계약 빌딩"]["year10"]},
                                    '1');""")
    elif st.session_state['보험유형'] == radio2 :
        common.postgres_update(f"""insert
                    into
                    insurance
                    (insurance_id,
                    insurance_userid,
                    building,
                    payment_date,
                    payment_amount,
                    payment_complete,
                    year1,
                    year2,
                    year3,
                    year4,
                    year5,
                    year6,
                    year7,
                    year8,
                    year9,
                    year10,
                    insurance_type)
                    values(nextval('seq_insurance_id'),
                    '{st.session_state["userid"]}',
                    '{st.session_state["계약 빌딩"]["building"]}',
                    '{datetime.today().strftime("%Y-%m-%d")}',
                    {int(insurance_amount/12)},
                    'Y',
                    {st.session_state["계약 빌딩"]["year1"]},
                    {st.session_state["계약 빌딩"]["year2"]},
                    {st.session_state["계약 빌딩"]["year3"]},
                    {st.session_state["계약 빌딩"]["year4"]},
                    {st.session_state["계약 빌딩"]["year5"]},
                    {st.session_state["계약 빌딩"]["year6"]},
                    {st.session_state["계약 빌딩"]["year7"]},
                    {st.session_state["계약 빌딩"]["year8"]},
                    {st.session_state["계약 빌딩"]["year9"]},
                    {st.session_state["계약 빌딩"]["year10"]},
                    '2');""")
        for i in range(1,12) :
            common.postgres_update(f"""insert
                                into
                                insurance
                                (insurance_id,
                                insurance_userid,
                                building,
                                payment_date,
                                payment_amount,
                                payment_complete,
                                year1,
                                year2,
                                year3,
                                year4,
                                year5,
                                year6,
                                year7,
                                year8,
                                year9,
                                year10,
                                insurance_type)
                                values(nextval('seq_insurance_id'),
                                '{st.session_state["userid"]}',
                                '{st.session_state["계약 빌딩"]["building"]}',
                                '{(datetime.today()+relativedelta(months=i)).strftime("%Y-%m-%d")}',
                                {int(insurance_amount/12)},
                                'N',
                                {st.session_state["계약 빌딩"]["year1"]},
                                {st.session_state["계약 빌딩"]["year2"]},
                                {st.session_state["계약 빌딩"]["year3"]},
                                {st.session_state["계약 빌딩"]["year4"]},
                                {st.session_state["계약 빌딩"]["year5"]},
                                {st.session_state["계약 빌딩"]["year6"]},
                                {st.session_state["계약 빌딩"]["year7"]},
                                {st.session_state["계약 빌딩"]["year8"]},
                                {st.session_state["계약 빌딩"]["year9"]},
                                {st.session_state["계약 빌딩"]["year10"]},
                                '2');""")
    else :
        common.postgres_update(f"""insert
                            into
                            insurance
                            (insurance_id,
                            insurance_userid,
                            building,
                            payment_date,
                            payment_amount,
                            payment_complete,
                            year1,
                            year2,
                            year3,
                            year4,
                            year5,
                            year6,
                            year7,
                            year8,
                            year9,
                            year10,
                            insurance_type)
                            values(nextval('seq_insurance_id'),
                            '{st.session_state["userid"]}',
                            '{st.session_state["계약 빌딩"]["building"]}',
                            '{datetime.today().strftime("%Y-%m-%d")}',
                             0,
                            'N',
                            {st.session_state["계약 빌딩"]["year1"]},
                            {st.session_state["계약 빌딩"]["year2"]},
                            {st.session_state["계약 빌딩"]["year3"]},
                            {st.session_state["계약 빌딩"]["year4"]},
                            {st.session_state["계약 빌딩"]["year5"]},
                            {st.session_state["계약 빌딩"]["year6"]},
                            {st.session_state["계약 빌딩"]["year7"]},
                            {st.session_state["계약 빌딩"]["year8"]},
                            {st.session_state["계약 빌딩"]["year9"]},
                            {st.session_state["계약 빌딩"]["year10"]},
                            '3');""")
    common.postgres_update(f"""
                           update
                                transactions
                            set
                                buyer = '{st.session_state["userid"]}',
                                conclusion = true,
                                conclusion_date = '{datetime.today().strftime("%Y-%m-%d")}',
                                insurance_amount = {insurance_amount},
                                selling_price = {st.session_state["계약 빌딩"]["expected_selling_price"]}
                            where
                                building = '{st.session_state["계약 빌딩"]["building"]}';""")

def select_my_info_buyer(userid) :
    return common.postgres_select(f"""
                                    select
                                        *,
                                        case
                                            when conclusion is null then '매물 등록'
                                            when conclusion is not null then '거래 완료' end as status
                                        from
                                            transactions t 
                                        where buyer = '{userid}'
                                        order by
                                        t.conclusion_date desc;""")

def select_my_info_seller(userid) :
    return common.postgres_select(f"""
                                    select
                                        *,
                                        case
                                            when conclusion is null then '매물 등록'
                                            when conclusion is not null then '거래 완료' end as status
                                        from
                                            transactions t 
                                        where seller = '{userid}';""")

def select_insurance(building, insurance_userid) :
    return common.postgres_select(f"""
                                    select
                                        *
                                    from
                                        insurance
                                    where
                                        insurance_userid = '{insurance_userid}'
                                        and building = '{building}'
                                    order by
                                        payment_date;
                                    """)
def select_total_amount(building, insurance_userid) :
    return common.postgres_select(f"""
                                    select
                                        sum(payment_amount) as total
                                    from
                                        insurance
                                    where
                                        insurance_userid = '{insurance_userid}'
                                        and building = '{building}'
                                        and payment_complete = 'Y';
                                    """)

def caculate_payback(minus,building, insurance_userid) :
    return common.postgres_select(f"""
                                    select
                                        case when {minus} > sum(payment_amount)*1.2 then sum(payment_amount)*1.2
                                        else {minus} end as payback
                                    from
                                        insurance
                                    where
                                        insurance_userid = '{insurance_userid}'
                                        and building = '{building}'
                                        and payment_complete = 'Y';
                                    """)

def change_address3():
    st.session_state['읍/면/동'] = get_address3_select_option(st.session_state.key2)
    st.session_state['읍/면/동'].loc[0] = "읍/면/동"

def change_by_insurance_type():
    st.session_state['보험유형'] = st.session_state.key3

def convert_price(price, include_0 = False) :
    temp = ""
    price = price
    if not math.isnan(price):
        if  price >= 10000 :
            temp = temp + str(int(price / 10000)) + '억 '
            price = price % 10000
        if price != 0 :
            temp = temp + str(int(price)) +'만원'
        if include_0 is True and price == 0:
            temp = temp + str(int(price)) +'만원'
    return temp 

def check_max_value() :
    if st.session_state.key4 > int(st.session_state["계약 빌딩"]['expected_selling_price']*0.1) :
        st.session_state["가입 가능"] = 'N'
    elif st.session_state.key4 <= 0 :
        st.session_state["가입 가능"] = 'N'
    else :
        st.session_state["가입 가능"] = 'Y'

# def dashboard():
#     submitted = ""

#     # st.markdown("##### 찾으려는 매물의 주소를 입력하세요.")
    
#     col1, col2, col3, col4 = st.columns([2,2,2,1])
    
#     select2_option = get_address2_select_option()
#     select2_option.loc[0] = "군/구"
#     with col1:
#         key1 = st.selectbox(placeholder="서울특별시", label="address1", label_visibility="collapsed", options=["서울특별시"])
#     with col2:
#         key2 = st.selectbox(placeholder="군/구", label="address2", label_visibility='collapsed', options=select2_option, on_change=change_address3, key="key2")
#     with col3:
#         key3 = st.selectbox(placeholder="읍/면/동", label="address3", label_visibility='collapsed', options=st.session_state['읍/면/동'])
#     with col4:
#         submitted = st.button("검색")
#     seoul_lat = 37.56661
#     seoul_lng = 126.978386

#     if submitted :
#         df = ""
#         zoom_start = 11
#         if key2 == '군/구': 
#             df = get_buildings_with_seperate_address1(key1)
#         elif key3 == '읍/면/동' :
#             df = get_buildings_with_seperate_address2(key1, key2)
#             zoom_start = 13
#         else :
#             df = get_buildings_with_seperate_address3(key1, key2, key3)
#             zoom_start = 13
        
#         if df.shape[0] > 0:
#             seoul_lat = df.iloc[0]['center_lat']
#             seoul_lng = df.iloc[0]['center_lng']

#         map = folium.Map(location=[seoul_lat, seoul_lng], zoom_start=zoom_start, tiles = 'cartodbpositron')

#         for i, each in df.iterrows():
#             html = f"""
#                     {each['loc']}
#                     """
#             folium.Circle([each['lat'], each['lng']],
#                     color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]),
#                     # fill_color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]),
#                     fill= True,
#                     radius=100,
#                     fill_opacity= 0.8,
#                     tooltip=html
#                     ).add_to(map)
#         folium_static(map)

#     else :
#         map = folium.Map(location=[seoul_lat, seoul_lng], zoom_start=11, tiles = 'cartodbpositron')
#         df = st.session_state['대시보드_지도'] 
#         if df is None :
#             df = get_transaction_strength_by_address3()
#             st.session_state['대시보드_지도'] = df
#             color_list = []
#             for i in range(df.shape[0]) :
#                 color_list.append("#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]))
#             st.session_state['대시보드_지도_색깔'] = color_list
#         for i, each in df.iterrows():
#             html = f"""
#                     {each['address3']}, 매물 {each['strength']}건 
#                     """
#             folium.Circle([each['center_lat'], each['center_lng']],
#                     color = st.session_state['대시보드_지도_색깔'][i],
#                     # fill_color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]),
#                     fill= True,
#                     radius=1000*each['strength'],
#                     fill_opacity= 0.8,
#                     tooltip=html
#                     ).add_to(map)
            
#         folium_static(map)  

#     col1, col2 = st.columns(2)
#     with col1 :
#         with st.container() :
            
#             st.markdown("##### 시/군/구별 거래 건수 Top 5")
#             df_left = get_transaction_count_by_address2()
#             df_left = df_left.rename(columns={
#                                             'address1' : '시/도', 
#                                             'address2' : '시/군/구', 
#                                             'count' : '거래 건수'})
#             chart = alt.Chart(df_left).mark_bar().encode(
#                 x='시/군/구',
#                 y=alt.Y('거래 건수', scale=alt.Scale(domain=[0, df_left.loc[0,'거래 건수'] +1 ], clamp=True)),
#                 color= '시/군/구'
#             ).configure_axisX(labelAngle=0).configure_legend(disable=True).configure_range("diverging")
#             st.altair_chart(chart, theme='streamlit', use_container_width=True)

            
#             st.dataframe(df_left, use_container_width=True, hide_index= True)

#     with col2 :
#          with st.container() :
#             # TODO : 가격 상승률로 변경해야 함
#             st.markdown("##### 시/군/구별 1년뒤 가격상승률 Top 5")
#             df_right = get_transaction_count_by_address2()
#             df_right = df_right.rename(columns={
#                                             'address1' : '시/도', 
#                                             'address2' : '시/군/구', 
#                                             'count' : '상승률 평균'})
#             chart = alt.Chart(df_right).mark_bar().encode(
#                 x='시/군/구',
#                 y=alt.Y('상승률 평균', scale=alt.Scale(domain=[0, df_right.loc[0,'상승률 평균'] +1 ], clamp=True)),
#                 color= '시/군/구',
#             ).configure_axisX(labelAngle=0).configure_legend(disable=True).configure_range("diverging")
#             st.altair_chart(chart, theme='streamlit', use_container_width=True)

#             st.dataframe(df_right, use_container_width=True, hide_index= True)


def building_select():
    if st.session_state['userid'] == None:
        st.warning("먼저 로그인을 하세요.")
        return 

    instr = ""
    submitted = ""
    df = st.session_state['건물']
    with st.form("address_input_form"):
        st.markdown("##### 찾으려는 건물의 주소를 입력하세요.")
        col1, col2 = st.columns([7, 1])

        with col1:
            address = st.text_input(
                label= "주소 입력", value=instr, placeholder=instr, label_visibility="collapsed"
            )

        with col2:
            submitted = st.form_submit_button("검색")

        if submitted:
            df = get_buildings_with_address(address)
            st.session_state['건물'] = df
            if len(df) == 0:
                st.warning("해당 주소의 건물이 존재하지 않습니다.")
        else :
            if df is None :
                df = get_buildings()
                st.session_state['건물'] = df

    max_len = 50
    count = 0
    df_display = pd.DataFrame(columns=df.columns)
    
    for i, row in df.iterrows():
        if count == max_len :
            break
        if not np.isin(row['loc'], df_display['loc']) :
            df_display.loc[len(df_display)] = row
        count +=1

    df_display = df_display.rename(columns={
        'loc' : '주소', 
        'how' :'용도 지역', 
        'main_how' : '건축물주용도', 
        'road_condition' : '도로 조건', 
        'year' : '준공 연도',
        'land_ratio' : '건폐율',
        'floor_ratio' : '용적률',
        'up_floor' : '지상',
        'under_floor' : '지하',
        'building_area' : '건물 면적',
        'tran_day' : '실거래 일자',
        'register_date' : '매물 등록 일자',
        'transaction_status' : '매물'})
    
    df_display['매매 희망가'] = "-"
    df_display['실거래가'] = "0만원"

    for i, row in df_display.iterrows():
        price = row['expected_selling_price']
        if price is not None and not math.isnan(price) :
            if row['매물'] != '거래 완료' :
                row['매매 희망가'] = convert_price(price)
        price = row['price']
        if price is not None and not math.isnan(price) :
            row['실거래가'] = convert_price(price)  
        row['실거래 일자'] = str(row['실거래 일자'])[0:4]+"-"+str(row['실거래 일자'])[4:6] +"-"+str(row['실거래 일자'])[6:]
        df_display.iloc[i] = row

    gb = GridOptionsBuilder.from_dataframe(df_display[["주소", "매물", "실거래가", "매매 희망가"]])
    gb.configure_selection(selection_mode="single")
    gridOptions = gb.build()

    data = AgGrid(
        df_display,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.MODEL_CHANGED,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        theme= 'material',
        height= 500
    )

    selected_rows = data["selected_rows"]

    if len(selected_rows) != 0:

        # 지도
        # 1.5km 미만
        query1 = f"match (s:Station)-[rel]-(b:Building) where b.loc =~ '{selected_rows[0]['주소']}'and rel.distance < 1.5 return s, rel, b order by rel.distance;"
        response1 = common.run_neo4j(query1)
    
        query2 = f"match (s:Starbucks)-[rel]-(b:Building) where b.loc =~ '{selected_rows[0]['주소']}'and rel.distance < 1.5 return s, rel, b order by rel.distance;"
        response2 = common.run_neo4j(query2)

        query3 = f"match (h:Hotel)-[rel]-(b:Building) where b.loc =~ '{selected_rows[0]['주소']}'and rel.distance < 1.5 return h, rel, b order by rel.distance;"
        response3 = common.run_neo4j(query3)

        map = folium.Map(location=[selected_rows[0]['lat'], selected_rows[0]['lng']], zoom_start=14, tiles = 'cartodbpositron')

        subway_icon_path = os.getcwd() + r"\subway.png"
        starbucks_icon_path = os.getcwd() + r"\starbucks.png"
        hotel_icon_path = os.getcwd() + r"\hotel.png"

        for i, each in enumerate(response1):
            stname = each['s']['stname']
            if stname.strip()[-1] != '역' :
                stname = stname + '역'
            distance = str(round(each['rel']['distance'],2)) + 'km'
            html = f"""
                {stname}, {distance} 
                """         
            folium.Marker(location=[each['s']['lat'],each['s']['lng']], icon= folium.features.CustomIcon(icon_image=subway_icon_path,icon_size=(40,40)), tooltip=html).add_to(map)
            folium.Marker(location=[each['b']['lat'],each['b']['lng']], icon= folium.Icon(color = 'darkpurple', icon='building', prefix='fa'), tooltip=selected_rows[0]['주소']).add_to(map)

        for i, each in enumerate(response2):
            sbname = each['s']['sbname']
            distance = str(round(each['rel']['distance'],2)) + 'km'
            html = f"""
                {sbname}, {distance} 
                """         
            folium.Marker(location=[each['s']['lat'],each['s']['lng']], icon= folium.features.CustomIcon(icon_image=starbucks_icon_path,icon_size=(30,30)), tooltip=html).add_to(map)
        
        for i, each in enumerate(response3):
            hname = each['h']['hname']
            distance = str(round(each['rel']['distance'],2)) + 'km'
            html = f"""
                {hname}, {distance} 
                """         
            folium.Marker(location=[each['h']['lat'],each['h']['lng']], icon= folium.features.CustomIcon(icon_image=hotel_icon_path,icon_size=(35,35)), tooltip=html).add_to(map)
        
        folium.Circle([selected_rows[0]['lat'], selected_rows[0]['lng']],
                color='#bd97b3',
                radius=1500
              ).add_to(map)
        
        folium_static(map)
        project.price_prediction(selected_rows[0]['주소'])
        tab1, tab2 = st.tabs(["매물 개요","매물 상세"])
        with tab1:
            col1, col2, col3 = st.columns([6,2,2])

            with col1:
                st.markdown("###### 주소")
                st.markdown(f"{selected_rows[0]['주소']}")
            with col2:
                if selected_rows[0]['매매 희망가'] != "-" :
                    st.markdown("###### 매매 희망가")
                    st.markdown(f"{selected_rows[0]['매매 희망가']}")
                else :
                    st.markdown("###### 실거래가")
                    st.markdown(f"{selected_rows[0]['실거래가']}")
            with col3:
                if selected_rows[0]['매매 희망가'] != "-" :
                    st.markdown("###### 매물 등록 일자")
                    st.markdown(f"{selected_rows[0]['매물 등록 일자'][0:10]}")
                else :
                    st.markdown("###### 실거래 일자")
                    st.markdown(f"{selected_rows[0]['실거래 일자']}") 
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
                button = ""
                if selected_rows[0]['매물'] == "등록" :
                    button = st.button("계약 체결")
                    if button:
                        st.session_state["계약 체결"] = "계약 체결"
                        st.session_state['계약 빌딩'] = selected_rows[0]
                        st.rerun()
                        pass

        with tab2 :
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("###### 용도 지역")
                st.markdown(f"{selected_rows[0]['용도 지역']}")
            with col2:
                st.markdown("###### 건축물주용도")
                st.markdown(f"{selected_rows[0]['건축물주용도']}")
            with col3:
                st.markdown("###### 도로 조건")
                st.markdown(f"{selected_rows[0]['도로 조건']}")
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
                st.markdown("###### 실거래 일자")
                st.markdown(f"{selected_rows[0]['실거래 일자']}") 

def my_info() :
    st.markdown("#### 내 거래내역")
    st.markdown("#")
    st.markdown("##### 판매자")
    df = select_my_info_seller(st.session_state['userid'])
    df = df.rename(columns={
    'building' : '주소', 
    'status' :'상태', 
    'register_date' : '매물 등록일자',
    'conclusion_date' : '거래 완료일자',
    'expected_selling_price' : '매매 희망가',
    'selling_price' : '체결 금액'})

    for i, each in df.iterrows():
        each['매물 등록일자'] = str(each['매물 등록일자'])
        each['거래 완료일자'] = str(each['거래 완료일자'])
        if each['거래 완료일자'] == 'None' :
            each['거래 완료일자'] = '-'
        df.loc[i] = each

    gb = GridOptionsBuilder.from_dataframe(df[['주소','상태','매물 등록일자','거래 완료일자']])
    gb.configure_selection(selection_mode="single")
    gridOptions = gb.build()

    data = AgGrid(
        df,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.MODEL_CHANGED,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        theme= 'material',
        height= 300,
        key="agrid1"
    )        

    st.markdown("##### 구매자")
    df2 = select_my_info_buyer(st.session_state['userid'])
    df2 = df2.rename(columns={
    'building' : '주소', 
    'status' :'상태', 
    'register_date' : '매물 등록일자',
    'conclusion_date' : '거래 완료일자',
    'expected_selling_price' : '매매 희망가',
    'selling_price' : '체결 금액'})

    for i, each in df2.iterrows():
        each['매물 등록일자'] = str(each['매물 등록일자'])
        each['거래 완료일자'] = str(each['거래 완료일자'])
        if each['거래 완료일자'] == 'None' :
            each['거래 완료일자'] = '-'
        df2.loc[i] = each

    gb2 = GridOptionsBuilder.from_dataframe(df2[['주소','상태','매물 등록일자','거래 완료일자']])
    gb2.configure_selection(selection_mode="single")
    gridOptions = gb2.build()

    data2 = AgGrid(
        df2,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.MODEL_CHANGED,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        theme= 'material',
        height= 300,
        key="agrid2"
    )

    selected_rows = data2["selected_rows"]

    if len(selected_rows) != 0 :

        if selected_rows[0]['상태'] == '거래 완료':
            
            df3 = select_insurance(selected_rows[0]['주소'], st.session_state['userid'])
            df3 = df3.rename(columns={
            'building' : '주소', 
            'payment_date' :'납입 (예정)일자', 
            'payment_amount' : '납입 (예정)금액',
            'payment_complete' : '납입 완료여부'})

            for i, each in df3.iterrows():
                each['납입 (예정)금액'] = convert_price(int(each['납입 (예정)금액']))
                df3.loc[i] = each

            st.markdown("#### 보험료 납입내역")
            type = df3.iloc[0]['insurance_type']

            if type == '1' :
                st.markdown("##### 보험 유형 : "+radio1)
                df3 = df3.rename(columns={
                    '납입 (예정)일자' :'납입 일자', 
                    '납입 (예정)금액' : '납입 금액'})
                st.dataframe(df3[['납입 일자','납입 금액','납입 완료여부']],hide_index=True, use_container_width=True)
            elif type == '2' :
                st.markdown("##### 보험 유형 : "+radio2)

                conslution_date = datetime.strptime(str(selected_rows[0]['거래 완료일자']), '%Y-%m-%d')

                delta = datetime.today() - conslution_date
                total_df = select_total_amount(selected_rows[0]['주소'], st.session_state['userid'])
                total = 0
                if total_df.loc[[0],['total']].empty:
                    total = 0
                else :
                    total = int(total_df.iloc[0]['total'])

                st.markdown("#")
                st.markdown(f"###### 보험료 총 납입 금액 : {convert_price(total)}")

                if delta.days < 365 : # 1년 미만
                    st.markdown("###### 고객님이 받으실 수 있는 보험금은 총 0원입니다.")
                    st.markdown(f"###### 거래 완료일자는 {conslution_date.strftime('%Y년 %m월 %d일')}로 현재 일자 {datetime.today().strftime('%Y년 %m월 %d일')} 적용되는 예측 기준은 '1년 미만'입니다.")
                    st.markdown("###### 거래 완료일자 기준 최소 1년 후부터 최대 10년후까지의 예측치에 대한 정확도를 보장드립니다.") 
                    st.markdown(f"###### {(conslution_date+relativedelta(years=1)).strftime('%Y년 %m월 %d일')}부터는 보험금 청구가 가능하십니다.")
                    
                elif delta.days > 365 * 10 : # 10년 초과
                    st.markdown("###### 고객님이 받으실 수 있는 보험금은 총 0원입니다.")
                    st.markdown(f"###### 거래 완료일자는 {conslution_date.strftime('%Y년 %m월 %d일')}로 현재 일자 {datetime.today().strftime('%Y년 %m월 %d일')} 적용되는 예측 기준은 '10년 초과'입니다.")
                    st.markdown("###### 거래 완료일자 기준 최소 1년 후부터 최대 10년후까지의 예측치에 대한 정확도를 보장드립니다.") 
                    st.markdown(f"###### 고객님의 보험은 {(conslution_date+relativedelta(years=10)).strftime('%Y년 %m월 %d일')}에 효력이 종료되었습니다.")
                    

                else : # 보장 가능 기간
                    year_index = int(delta.days//365)
                    year_column = "year"+str(year_index)
                    
                    expect = convert_price(int(df3.iloc[0][f"{year_column}"]))
                    expect_lower = convert_price(int(int(df3.iloc[0][f"{year_column}"]) * 0.9))
                    expect_upper = convert_price(int(int(df3.iloc[0][f"{year_column}"]) * 1.1))
                    real = convert_price(int(int(selected_rows[0]['체결 금액']) * random.choice([1.05,2])))

                    payback = convert_price(int(total*1.2))
                    if real >= expect_lower and real<= expect_upper :
                        payback = convert_price(int(total*0.9))

                    st.markdown(f"###### 고객님이 받으실 수 있는 보험금은 총 {payback}입니다.")
                    st.markdown(f"###### 거래 완료일자는 {conslution_date.strftime('%Y년 %m월 %d일')}로 현재 일자 {datetime.today().strftime('%Y년 %m월 %d일')} 적용되는 예측 기준은 '{year_index}년 후'입니다.")
                    st.markdown(f"###### 해당 매물의 거래 완료일자 기준 {year_index}년 후 예측 가격은 {expect}으로,")
                    st.markdown(f"###### 예측이 정확하다고 판단하는 구간은 {expect_lower}부터 {expect_upper}까지의 가격입니다.")
                    
                    st.markdown("#")
                    if real >= expect_lower and real<= expect_upper :
                        st.markdown(f"###### 현재가 {real}은 해당 구간에 포함되므로") 
                        st.markdown(f"###### 보험료 총 납입금액의 90%인 {payback}을 환급드릴 수 있습니다.")
                    else :
                        st.markdown(f"###### 현재가 {real}은 해당 구간에 포함되지 않으므로")
                        st.markdown(f"###### 보험료 총 납입금액의 120%인 {payback}을 환급드릴 수 있습니다.")

                st.markdown("#")
                st.dataframe(df3[['납입 (예정)일자','납입 (예정)금액','납입 완료여부']],hide_index=True, use_container_width=True)
            elif type == '3' :
                st.markdown("##### 보험 유형 : "+radio3)
                st.markdown("###### 보험 납입내역이 존재하지 않습니다.")


def contract() :
    st.markdown("#### 보험 약관 및 계약 확인 사항")
    st.markdown("##### 보험명 : 호갱님 노노 보험")
    st.image('보험약관.png', use_column_width=True)
    st.image('보험 안내문.jpg',use_column_width=True)

    st.markdown("# ")
    st.markdown("##### 보험 가입까지 함께 진행하시겠습니까?")
    st.markdown("###### 가입을 원하는 보험을 선택하세요.")

    if st.session_state['보험유형'] is None :
        st.session_state['보험유형'] = radio1
    radio_select = st.radio(label = '가입을 원하는 보험을 선택하세요.', options = [radio1, radio2, radio3], label_visibility="collapsed",key="key3", on_change=change_by_insurance_type)

    amount = 0

    if st.session_state['보험유형'] == radio1:
        st.markdown("###### 최초 1회 납부하는 보험료를 안내드립니다.")
        amount = st.text_input("총 납입 금액(만원)", disabled=True, value=int(st.session_state["계약 빌딩"]['expected_selling_price']*0.0015),)        
    elif st.session_state['보험유형'] == radio2 :
        st.markdown("###### 계약 체결 후 12개월 분할로 보험료 납부 시, 최대 10년 후까지 보장드립니다.") 
        amount = st.number_input("총 납입 금액(만원)", step=10, format="%d", 
                                 value = int(st.session_state["계약 빌딩"]['expected_selling_price']*0.1),
                                 on_change= check_max_value,
                                 key="key4")    
    elif st.session_state['보험유형'] == radio3 :
        pass
    
    submitted = ""
    cancel = ""
    col11, col2, col3 = st.columns([4,1,1])

    with col2 :
        submitted = st.button("거래 체결")
    with col3 : 
        cancel = st.button("거래 취소")

    if submitted :
        if st.session_state["가입 가능"] == 'N' :
            st.warning(f"보험금 설정은 1만원부터 매매가의 10%인 {int(st.session_state['계약 빌딩']['expected_selling_price']*0.1)}만원까지 가능합니다. 다시 입력해주시기 바랍니다.")
        else :
            try :
                update_transaction(int(amount))
                update_building_price(int(amount), st.session_state['계약 빌딩']['주소'] )
            except :
                st.error("DB error")
            st.session_state['계약 체결'] = None
            st.session_state['계약 빌딩'] = None
            st.session_state['보험유형'] = None
            st.session_state['건물'] = get_buildings()
            st.rerun()

    if cancel :
        st.session_state['계약 체결'] = None
        st.session_state['계약 빌딩'] = None
        st.session_state['보험유형'] = None
        st.session_state['건물'] = get_buildings()
        st.rerun()

def update_building_price(price, address) :
    common.postgres_update(f"""insert
                                into
                                building 
                                (
                                select
                                    loc,
                                    how,
                                    main_how,
                                    road_condition,
                                    area1,
                                    area2,
                                    "year",
                                    {price},
                                    land_ratio,
                                    floor_ratio,
                                    up_floor,
                                    under_floor,
                                    building_area,
                                    {datetime.today().strftime("%Y-%m-%d")},
                                    road_name,
                                    pnu,
                                    lat,
                                    lng,
                                    year1,
                                    year2,
                                    year3,
                                    year4,
                                    year5,
                                    year6,
                                    year7,
                                    year8,
                                    year9,
                                    year10
                                from
                                    building
                                where
                                    loc = '{address}'
                                    and tran_day = (
                                    select
                                        max(tran_day)
                                    from
                                        building b
                                    where
                                        loc = {address});""")