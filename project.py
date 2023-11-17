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

def add_userdata(username, userid, password):
    common.postgres_update(f"INSERT INTO users(name, id, password) VALUES ('{username}', '{userid}', '{password}')")

def add_buildingdata(username, address, price):
    common.postgres_update(f"INSERT INTO transactions(seller, building, price) VALUES ('{username}', '{address}', price)")
    return True


def price_prediction(address):
    # 데이터베이스 쿼리 결과를 가져옴
    result = common.postgres_select(f"SELECT price, year1, year2, year3, year5, year10 FROM building WHERE loc='{address}'")
    if result:
        # 데이터 추출
        data = result[0]  # 여기서는 첫 번째 행을 사용합니다
        building_year=common.postgres_select(f"SELECT year FROM building WHERE loc='{address}'")
        years = [f'최근거래연도{building_year}','1 year', '2 years', '3 years', '5 years', '10 years']
        values = [data[0], data[1], data[2], data[3], data[4], data[5]]

        # 꺾은선 그래프 생성
        plt.figure()
        plt.plot(years, values, marker='o')
        plt.title(f"Price Prediction for {address}")
        plt.xlabel("Years")
        plt.ylabel("Price")
        
        # Streamlit에 그래프 표시
        st.pyplot(plt)
    else:
        st.write("No data available for this address")


def login_user(userid, password):
    response = common.postgres_select(f"SELECT * FROM users WHERE id ='{userid}' AND password = '{password}'")
    return len(response)>0

def check_user(userid):
    response = common.postgres_select(f"SELECT * FROM users WHERE id = '{userid}'")
    return len(response)>0

def main():
    st.title("건물공유중개 및 가격예측서비스")

    if 'userid' not in st.session_state:
        st.session_state['userid'] = None

    if '매물' not in st.session_state:
        st.session_state['매물'] = None

    menu = ["대시보드", "로그인", "회원가입", "매물 등록", "가격예측서비스", "매물 조회"]
    icon = ['house', 'person-check', 'person-add', 'building-add', 'card-checklist' , 'building']

    if st.session_state['userid'] is not None :
        del menu[1]
        del menu[1]
        del icon[1]
        del icon[1]
    
    with st.sidebar:
        choice = option_menu("메뉴", menu,
                            icons=icon,
                            menu_icon="list", 
                            default_index=0,
                            styles={
            "container": {"padding": "4!important", "background-color": "#fafafa"},
            "icon": {"color": "black", "font-size": "20px"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px", "--hover-color": "#fafafa"},
            "nav-link-selected": {"background-color": "#d8d9f0", "color": "black"},
        }
    )

    # choice = st.sidebar.selectbox("Menu", menu)

    if choice == "대시보드":

        if st.session_state['userid']:
            st.subheader(f"Welcome {st.session_state['userid']}")
        else:
            st.subheader("Home")

    elif choice == "로그인":
        st.subheader("Login Section")

        userid = st.sidebar.text_input("User ID")
        password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.button("Login"):
            hashed_pswd = hashlib.sha256(password.encode('utf-8')).hexdigest()
            result = login_user(userid, hashed_pswd)
            if result:
                st.session_state['userid'] = userid
                st.success("로그인에 성공했습니다!")
                st.rerun()
            else:
                st.warning("잘못된 사용자 ID 또는 비밀번호입니다.")

    elif choice == "회원가입":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_userid = st.text_input("User ID")
        new_password = st.text_input("Password",type='password')

        if st.button("Signup"):
            if check_user(new_userid):
                st.warning("이미 존재하는 사용자 ID입니다.")
            else:
                add_userdata(new_user, new_userid, hashlib.sha256(new_password.encode('utf-8')).hexdigest())
                st.success("회원가입에 성공했습니다!")
                st.info("Go to Login Menu to login")
            
    elif choice == "매물 등록":
        st.subheader("Add Your Building Information")
        if st.session_state['userid']:
            address = st.text_input("건물주소(읍면동)")
            price = st.number_input("매매희망가격(원)", step=1000000.0, format="%f")
            if st.button("Submit"):
                if add_buildingdata(st.session_state['userid'], address, price):
                    st.success("건물정보가 성공적으로 입력되었습니다.")
                else:
                    st.error("주소를 찾을 수 없습니다.")
        else:
            st.warning("먼저 로그인을 하세요.")

    elif choice == "가격예측서비스":
        st.subheader("예측하고자 하는 건물의 주소를 입력하세요")
        if st.session_state['userid']:
            address = st.text_input("건물주소(읍면동)")
            if st.button("Submit"):
                if price_prediction(st.session_state['userid'], address):
                    st.success("건물정보가 성공적으로 입력되었습니다.")
                else:
                    st.error("주소를 찾을 수 없습니다.")
        else:
            st.warning("먼저 로그인을 하세요.")

    elif choice == "매물 조회" :
        ft.building_select()

if __name__ == '__main__':
    main()
