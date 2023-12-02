import common
import streamlit as st
import sqlite3
import hashlib
from geopy.geocoders import ArcGIS
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
import pandas as pd
import matplotlib.pyplot as plt
import front as ft
from streamlit_option_menu import option_menu
import background
from PIL import Image
from datetime import datetime

#####
import matplotlib.ticker as ticker
import numpy as np
from scipy.interpolate import interp1d
# 한글깨짐 필요 라이브러리 불러오기
import matplotlib as mpl

mpl.rcParams['font.family'] = 'NanumGothic'
mpl.rcParams['font.size'] = 8

def formatter(x, pos):
    return '%1.0f' % (x * 1e-3)

def add_userdata(username, userid, password):
    common.postgres_update(f"INSERT INTO users(name, id, password) VALUES ('{username}', '{userid}', '{password}')")

def add_buildingdata(username, address, price, register_date):
    common.postgres_update(f"INSERT INTO transactions(seller, building, expected_selling_price, register_date) VALUES ('{username}', '{address}', {price},'{register_date}')")

def get_address3(address) :
    return common.postgres_select(f"""
                                    select
                                        distinct split_part(loc,' ',3) as address3
                                    from
                                        building
                                    where
                                        loc = '{address}';
                                    """)

def change_address3():
    st.session_state['읍/면/동'] = ft.get_address3_select_option(st.session_state.key2)
    st.session_state['읍/면/동'].loc[0] = "읍/면/동"

def price_prediction(address):
    try:
        # 원래 건물 정보 및 가격 데이터 쿼리
        price_query = f"""
                        select
                            price,
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
                            loc like '%{address}%'
                            and year1 is not null 
                            and year1 !=0;
                        """
        price_info = common.postgres_select(price_query)

        price_before_query=f"SELECT price, tran_day From building where loc like '%{address}%' order by tran_day asc;"
        price_before_info = common.postgres_select(price_before_query)
        
        address3 = str(get_address3(address).iloc[0]['address3'])
        
        # 동에 해당하는 모든 건물의 데이터 쿼리
        address3_query = f"""
                        select
                            price,
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
                            split_part(loc, ' ', 3) = '{address3}'
                            and year1 is not null 
                            and year1 !=0;
                        """
        address3_avg_info = common.postgres_select(address3_query)

        # 원래 건물 가격 예측 그래프
        price_data = price_info.iloc[0]

        # 동 데이터의 평균 계산
        avg_address3 = address3_avg_info.mean()

        # 이전 거래 데이터 처리
        years = ['1년후', '2년후', '3년후', '4년후', '5년후', '6년후', '7년후', '8년후', '9년후', '10년후']
        values = [price_data['year1'], price_data['year2'], price_data['year3'], price_data['year4'], price_data['year5'], price_data['year6'], price_data['year7'], price_data['year8'], price_data['year9'], price_data['year10']]
        avg_values = [avg_address3['year1'], avg_address3['year2'], avg_address3['year3'], avg_address3['year4'], avg_address3['year5'], avg_address3['year6'], avg_address3['year7'], avg_address3['year8'], avg_address3['year9'], avg_address3['year10']]

        # 이전 거래일자와 가격 추가
        num_previous_data = len(price_before_info)
        for index, row in price_before_info.iloc[::-1].iterrows():
                years.insert(0, str(row['tran_day'])[0:4])  # 거래일자 추가
                values.insert(0, row['price'])  # 거래가격 추가

        avg_values = [None] * (len(years) - len(avg_values)) + avg_values  # avg_values의 길이를 years 배열의 길이에 맞게 조정
        
        x = np.arange(len(years))

        # 보간 함수 생성 (f_values)
        valid_indices_values = [i for i, v in enumerate(values) if v is not None]
        f_values = interp1d([x[i] for i in valid_indices_values], [values[i] for i in valid_indices_values], kind='cubic')

        # 보간 함수 생성 (f_avg_values)
        valid_indices_avg = [i for i, v in enumerate(avg_values) if v is not None]
        f_avg_values = interp1d([x[i] for i in valid_indices_avg], [avg_values[i] for i in valid_indices_avg], kind='cubic')
        
        # 고해상도 X축 값 생성
        x_min_values = min([x[i] for i in valid_indices_values])
        x_max_values = max([x[i] for i in valid_indices_values])
        x_min_avg = min([x[i] for i in valid_indices_avg])
        x_max_avg = max([x[i] for i in valid_indices_avg])

        x_min = max(x_min_values, x_min_avg)  # 두 보간 함수 범위의 최소값 중 큰 값 선택
        x_max = min(x_max_values, x_max_avg)  # 두 보간 함수 범위의 최대값 중 작은 값 선택

        xnew = np.linspace(x_min, x_max, num=100, endpoint=True)
        
        xstart=x[num_previous_data-1]
        xnew2 = np.linspace(xstart, x_max, num=100, endpoint=True)

        # 선 그래프 생성
        plt.figure()
        plt.plot(x[:num_previous_data], values[:num_previous_data], linestyle='-', marker='o', color='#6469b0')
        plt.plot(xnew2, f_values(xnew2), linestyle='--', label=f"{address} 거래가격", color='#6469b0')
        plt.plot(xnew, f_avg_values(xnew), linestyle='--', linewidth=2, label=f"{address3} 평균 예측", color='#bd97b3')
        plt.scatter(x, values, color='#6469b0')  # 원래 데이터 포인트에만 마커 표시
        plt.scatter(x, avg_values, color='#bd97b3')  # 원래 데이터 포인트에만 마커 표시
        plt.xticks(ticks=x, labels=years)  # X축 눈금 설정
        plt.title(f"{address} 및 {address3} 평균 가격 비교")
        plt.xlabel("거래연도 및 예측시점")
        plt.ylabel("예상가격(천만)")
        plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(formatter))
        plt.legend()

        # Streamlit에 그래프 표시
        st.pyplot(plt)

        return True
    except Exception as e:
        st.write("데이터 처리 중 오류 발생:", e)
        return False

def check_building(address1, address2, address3, address4):
    return common.postgres_select(f"""
                                select
                                    distinct loc
                                from
                                    building
                                where
                                    split_part(loc, ' ', 1) = '{address1}'
                                and split_part(loc, ' ', 2) = '{address2}'
                                and split_part(loc, ' ', 3) = '{address3}'
                                and split_part(loc, ' ', 4) like '%{address4}%';""")

def check_transaction_building(building) :
    return common.postgres_select(f"""
                                    select * from transactions where building = '{building}' and buyer is null;
                                    """)

def login_user(userid, password):
    response = common.postgres_select(f"SELECT * FROM users WHERE id ='{userid}' AND password = '{password}'")
    return len(response)>0

def check_user(userid):
    response = common.postgres_select(f"SELECT * FROM users WHERE id = '{userid}'")
    return len(response)>0

def set_session_state():
    if 'userid' not in st.session_state:
        st.session_state['userid'] = None

    if '건물' not in st.session_state:
        st.session_state['건물'] = None

    if '읍/면/동' not in st.session_state :
        st.session_state['읍/면/동'] = ['읍/면/동']

    # if '대시보드_지도' not in st.session_state :
    #     st.session_state['대시보드_지도'] = None
    #     st.session_state['대시보드_지도_색깔'] = None

    if '계약 체결' not in st.session_state :
        st.session_state['계약 체결'] = None
    if '계약 빌딩' not in st.session_state :
        st.session_state['계약 빌딩'] = None

    if '보험유형' not in st.session_state :
        st.session_state['보험유형'] = None

    if '가입 가능' not in st.session_state :
        st.session_state['가입 가능'] = 'Y'

def main():
    set_session_state()

    menu = ["메인", "로그인", "회원가입", "매물 등록", "건물 조회"]
    icon = ['house', 'person-check', 'person-add', 'building-add', 'building']

    if st.session_state['userid'] is not None :
        del menu[1]
        del menu[1]
        del icon[1]
        del icon[1]
        menu.insert(1, '내 거래내역')
        icon.insert(1, 'person-lines-fill')

    with st.sidebar:
        choice = option_menu("메뉴", menu,
                            icons=icon,
                            menu_icon="list", 
                            default_index=0,
                            styles={
            "container": {"padding": "0", "background-color": "#fafafa"},
            "icon": {"color": "black", "font-size": "20px"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px", "--hover-color": "#fafafa"},
            "nav-link-selected": {"background-color": "#d8d9f0", "color": "black"},
        }
    )

    # choice = st.sidebar.selectbox("Menu", menu)

    # if choice == "대시보드":
    #     ft.dashboard()

    if st.session_state['계약 체결'] is not None :
        choice = st.session_state['계약 체결']

    if choice == "로그인":
        st.subheader("로그인")

        userid = st.text_input("ID")
        password = st.text_input('비밀번호', type='password')
        if st.button("로그인"):
            hashed_pswd = hashlib.sha256(password.encode('utf-8')).hexdigest()
            result = login_user(userid, hashed_pswd)
            if result:
                st.session_state['userid'] = userid
                st.success("로그인에 성공했습니다!")
                st.rerun()
            else:
                st.warning("잘못된 사용자 ID 또는 비밀번호입니다.")

    elif choice == "회원가입":
        st.subheader("회원가입")
        new_user = st.text_input("성함")
        new_userid = st.text_input("ID")
        new_password = st.text_input('비밀번호',type='password')

        if st.button("가입"):
            if check_user(new_userid):
                st.warning("이미 존재하는 사용자 ID입니다.")
            else:
                add_userdata(new_user, new_userid, hashlib.sha256(new_password.encode('utf-8')).hexdigest())
                st.success("회원가입에 성공했습니다! 로그인을 해주세요.")
            
    elif choice == "매물 등록":
        st.subheader("매물 등록")
        if st.session_state['userid']:
            col1, col2, col3, col4 = st.columns([2,2,2,3])

            select2_option = ft.get_address2_select_option()
            select2_option.loc[0] = "군/구"
            with col1:
                key1 = st.selectbox(placeholder="서울특별시", label="시/도", label_visibility="visible", options=["서울특별시"])
            with col2:
                key2 = st.selectbox(placeholder="군/구", label="군/구", label_visibility='visible', options=select2_option, on_change=change_address3, key="key2")
            with col3:
                key3 = st.selectbox(placeholder="읍/면/동", label="읍/면/동", label_visibility='visible', options=st.session_state['읍/면/동'])
            with col4:
                address = st.text_input("상세주소", label_visibility="visible") 
            price = st.text_input("매매희망가격(만원)")
            if st.button("입력"):
                building = check_building(key1, key2, key3, address)
                
                if len(building) == 1 :    
                    if price.isdecimal() :
                        building2 = check_transaction_building(building.iloc[0]['loc'])
                        if len(building2) == 0 :
                            add_buildingdata(st.session_state['userid'], building.iloc[0]['loc'], int(price), datetime.today().strftime("%Y-%m-%d"))
                            st.success("건물정보가 성공적으로 입력되었습니다.")
                            st.session_state['건물'] = None
                        else :
                            st.warning("이미 매물로 등록된 건물입니다.")
                    else :
                        st.error("유효한 숫자를 입력하세요.")

                elif len(building) > 1 :
                    st.warning("하나 이상의 건물이 존재합니다. 정확한 건물 정보를 입력해 주세요.")
                else :
                    st.warning("해당 건물이 존재하지 않습니다. 주소를 확인해주세요.")
        else:
            st.warning("먼저 로그인을 하세요.")

    elif choice == "메인":
        left_co, cent_co,last_co = st.columns(3)
        with cent_co:
            st.image('호갱님노노.jpg', use_column_width=True)
        st.subheader("예측하고자 하는 건물의 주소를 입력하세요")
        col1, col2, col3 = st.columns(3)

        select2_option = ft.get_address2_select_option()
        select2_option.loc[0] = "군/구"
        with col1:
            key1 = st.selectbox(placeholder="서울특별시", label="시/도", label_visibility="collapsed", options=["서울특별시"])
        with col2:
            key2 = st.selectbox(placeholder="군/구", label="군/구", label_visibility='collapsed', options=select2_option, on_change=change_address3, key="key2")
        with col3:
            key3 = st.selectbox(placeholder="읍/면/동", label="읍/면/동", label_visibility='collapsed', options=st.session_state['읍/면/동'])
        
        address = st.text_input("상세주소", label_visibility="collapsed") 
        
        col1, col2 = st.columns([8,2])
        with col2 :
            btn = st.button("가격예측", use_container_width=True)
        if btn:
            building = check_building(key1, key2, key3, address)

            if len(building) == 1 :    
                price_prediction(building.iloc[0]['loc'])
            elif len(building) > 1 :
                st.warning("하나 이상의 건물이 존재합니다. 정확한 건물 정보를 입력해 주세요.")
            else :
                st.warning("해당 건물이 존재하지 않습니다. 주소를 확인해주세요.")


    elif choice == "건물 조회" :
        ft.building_select()
    
    elif choice == "내 거래내역" :
        ft.my_info()
    elif choice == "계약 체결" :
        ft.contract()

if __name__ == '__main__':
    st.set_page_config(page_title="호갱님노노",initial_sidebar_state="auto")

    # with open('style.css') as f:
    #     st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    # t = background.BackgroundTasks()
    # t.start()
    main()
