import common

import streamlit as st
import pandas as pd
import numpy as np

query = f"SELECT * FROM station where stname = '서울대입구역'"
response = common.postgres_select(query)

# print(response)

df = pd.DataFrame({
    "col1": response['latitude'],
    "col2": response['longitude'],
    "col3": 700,
    "col4": '#0044ff',
})

st.map(df,
    latitude='col1',
    longitude='col2',
    size='col3',
    color='col4')


query = f"SELECT * FROM station limit 100"
response = common.postgres_select(query)

df2 = pd.DataFrame({
    "col1": response['latitude'],
    "col2": response['longitude'],
    "col3": np.random.randn(100) * 100,
    "col4": np.random.rand(100, 4).tolist(),
})

st.map(df2,
    latitude='col1',
    longitude='col2',
    size='col3',
    color='col4')