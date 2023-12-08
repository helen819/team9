import streamlit as st
import pandas as pd
import psycopg2
from neo4j import GraphDatabase
from pandas.io import gbq
import pydata_google_auth
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime

# 연결 정보
# bigquery
project_id = "team9-404702"
# postgres
connection_info = "host=147.47.200.145 dbname=teamdb9 user=team9 password=aplus port=34543"
keepalives=1,
keepalives_idle=30,
keepalives_interval=10,
keepalives_count=5
# neo4j
dbname = "teamdb9"
uri_param = "bolt://147.47.200.145:37687"
user_param = "team9"
pwd_param = "aplus"

def run_bigquery(query):
    SCOPES = [
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/bigquery'
    ]

    credentials = pydata_google_auth.get_user_credentials(SCOPES, auth_local_webserver=False)
    response = pd.read_gbq(query, project_id=project_id, credentials=credentials, dialect='standard')
    return response

# postgres select 수행
def postgres_select(query):
    try:
        # print(query)
        conn = psycopg2.connect(connection_info)
        df = pd.read_sql(query,conn)
    except psycopg2.Error as e:
        print("DB error: ", e)
        conn.close()
    finally:
        conn.close()
    return df

# postgres insert, update, delete 수행 (commit 필요한 작업)
def postgres_update(query):
    try:
        conn = psycopg2.connect(connection_info)
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
    except psycopg2.Error as e:
        print("DB error: ", e)
        conn.rollback()
        conn.close()
    finally:
        conn.close()

class Neo4jConnection:
    def __init__(self, uri, user, pwd):
        self.__uri = uri
        self.__user = user
        self.__pwd = pwd
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__pwd))
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):
        if self.__driver is not None:
            self.__driver.close()

    def query(self, query, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = list(session.run(query))
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()
        return response

# neo4j cypher 수행   
def run_neo4j(cypher) :
    conn = Neo4jConnection(uri=uri_param, user=user_param, pwd=pwd_param)
    response = conn.query(cypher, db=dbname)
    conn.close()
    return response

def croll_economy():
    date = datetime.today().strftime("%Y%m") 
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    url = 'https://www.korcham.net/nCham/Service/EconBrief/appl/ProspectList.asp'
    # driver = webdriver.Chrome("chromedriver.exe", options=options)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(1)
    # cold_rate = driver.find_elements_by_xpath('/html/body/div/div[2]/section/div/table/tbody/tr[2]/td[5]')[0].text
    call_rate = driver.find_elements('xpath','/html/body/div/div[2]/section/div/table/tbody/tr[2]/td[5]')[0].text

    url = 'https://ecos.bok.or.kr/#/'
    # driver = webdriver.Chrome("chromedriver.exe", options=options)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(1)
    # m2 = driver.find_elements_by_xpath('/html/body/div[1]/div[5]/div/div[2]/div[2]/div/div[1]/ul/li[5]/div/div/span[2]/span[1]')[0].text
    # m2 = driver.find_elements('/html/body/div[1]/div[5]/div/div[2]/div[2]/div/div[1]/ul/li[5]/div/div/span[2]/span[1]')[0].text
    m2 = driver.find_elements('xpath','/html/body/div[1]/div[5]/div/div[2]/div[2]/div/div[1]/ul/li[5]/div/div/span[2]/span[1]')[0].text
    
    query = f"""
    INSERT INTO public.economy
    ("date", call_rate, "m2")
    VALUES('{date}', '{call_rate}', '{m2}');
    """
    return query