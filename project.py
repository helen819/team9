import common
import streamlit as st
import sqlite3
import hashlib
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
import pandas as pd

def add_userdata(username, userid, password):
    common.postgres_update(f"INSERT INTO users(name, id, password) VALUES ('{username}', '{userid}', '{password}')")

def add_buildingdata(userid, address, price):
    common.postgres_update(f"INSERT INTO building(userid, address, price) VALUES ('{userid}', '{address}','{price}' )")

def login_user(userid, password):
    response = common.postgres_select(f"SELECT * FROM users WHERE id ='{userid}' AND password = '{password}'")
    return len(response)>0

def check_user(userid):
    response = common.postgres_select(f"SELECT * FROM users WHERE id = '{userid}'")
    return len(response)>0

def get_buildings() :
    return common.postgres_select(f"SELECT * FROM transactions t, building b WHERE t.building = b.loc and t.buyer IS NULL ORDER BY t.register_date desc limit 100")

def get_buildings_with_address(address) :
    return common.postgres_select(f"SELECT * FROM transactions t, building b WHERE t.building = b.loc and t.building like '%{address}%'")


def main():
    st.title("건물공유중개 및 가격예측서비스")

    menu = ["Home", "Login", "SignUp", "Add Building Info", "매물 조회"]
    choice = st.sidebar.selectbox("Menu", menu)

    if 'userid' not in st.session_state:
        st.session_state['userid'] = None

    if choice == "Home":

        if st.session_state['userid']:
            st.subheader(f"Welcome {st.session_state['userid']}")
        else:
            st.subheader("Home")

    elif choice == "Login":
        st.subheader("Login Section")

        userid = st.sidebar.text_input("User ID")
        password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.button("Login"):
            hashed_pswd = hashlib.sha256(password.encode('utf-8')).hexdigest()
            result = login_user(userid, hashed_pswd)
            if result:
                st.session_state['userid'] = userid
                st.success("로그인에 성공했습니다!")
                st.experimental_rerun()
            else:
                st.warning("잘못된 사용자 ID 또는 비밀번호입니다.")

    elif choice == "SignUp":
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
            
    elif choice == "Add Building Info":
        st.subheader("Add Your Building Information")
        if st.session_state['userid']:
            address = st.text_input("Building Address")
            price = st.number_input("Desired Price", step=1000.0, format="%f")
            if st.button("Submit"):
                add_buildingdata(st.session_state['userid'], address, price)
                st.success("Building Information Added Successfully")
        else:
            st.warning("Please Login First to Add Building Information")

    elif choice == "매물 조회" :

        instr = ""
        submitted = ""
        with st.form('chat_input_form'):
            st.markdown("##### 찾으려는 매물의 주소를 입력하세요.")
            col1, col2 = st.columns([7,1]) 

            with col1:
                address = st.text_input(
                    instr,
                    value=instr,
                    placeholder=instr,
                    label_visibility='collapsed'
                )

            with col2:
                submitted = st.form_submit_button('검색')
        
        df =""
        if submitted:
            df = get_buildings_with_address(address)
            if len(df) == 0 : 
                st.warning("해당 주소의 매물이 존재하지 않습니다.")
        else :
            df = get_buildings()
        
        gb = GridOptionsBuilder.from_dataframe(df[['building','expected_selling_price']])
        gb.configure_selection(selection_mode="single")
        gridOptions = gb.build()

        data = AgGrid(df,
            gridOptions=gridOptions,
            enable_enterprise_modules=True,
            allow_unsafe_jscode=True,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW)
        
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

if __name__ == '__main__':
    main()
