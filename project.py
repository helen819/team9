import streamlit as st
import sqlite3
import hashlib

conn = sqlite3.connect('data.db', check_same_thread=False)
c = conn.cursor()

def create_usertable():
    c.execute('DROP TABLE IF EXISTS userstable')  # 기존 테이블 삭제
    c.execute('CREATE TABLE userstable(username TEXT, userid TEXT, password TEXT)')  # 새로운 테이블 생성

def create_buildingtable():
    c.execute('CREATE TABLE IF NOT EXISTS buildingtable(userid TEXT, address TEXT, price REAL)')

def add_userdata(username, userid, password):
    c.execute('INSERT INTO userstable(username, userid, password) VALUES (?, ?, ?)', (username, userid, password))
    conn.commit()

def add_buildingdata(userid, address, price):
    c.execute('INSERT INTO buildingtable(userid, address, price) VALUES (?, ?, ?)', (userid, address, price))
    conn.commit()

def login_user(userid, password):
    c.execute('SELECT * FROM userstable WHERE userid =? AND password = ?', (userid, password))
    data = c.fetchall()
    return data

def check_user(userid):
    c.execute('SELECT * FROM userstable WHERE username =? OR userid = ?', (userid))
    data = c.fetchall()
    return len(data) > 0

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
            create_usertable()
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
                create_usertable()
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
