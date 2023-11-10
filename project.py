import common
import streamlit as st
import sqlite3
import hashlib

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

def main():
    st.title("건물공유중개 및 가격예측서비스")

    menu = ["Home", "Login", "SignUp", "Add Building Info"]
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

if __name__ == '__main__':
    main()
