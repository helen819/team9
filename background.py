import threading
import time
from datetime import date
import common
import schedule
from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx, get_script_run_ctx
# import update_building
import update_building2
import streamlit as st

lgbm_params1 = {
    'task': 'train',
    'objective': 'regression',
    'subsample': 0.8,
    'lambda_l1': 0.4,
    'learning_rate': 0.1,
    'feature_fraction' : 0.6,
    'max_depth': 16,
    'num_leaves':10000
}

lgbm_params2 = {
    'feature_fraction': 0.5,
    'learning_rate': 0.02,
    'n_estimators' : 150,
    'min_child_weight': 0.001,
    'max_depth': 15,
    'num_leaves': 4000
}

xgb_params = {
    'task': 'train',
    'objective': 'reg:squarederror',
    'subsample': 0.8,
    'lambda_l1': 0.4,
    'learning_rate': 0.1,
    'xgb__n_estimators': 100,
    'xgb__learning_rate': 0.01,
    'xgb__max_depth': 16,
    'max_leaf_nodes': 10000,
    'subsample': 0.8,
}

col = ['M2', 'bir', 'under_floor', 'lng', 'lat', 'floor_ratio', 'land_ratio', 'year']

def crawling() :
    print('crawling 호출')
    if date.today().day != 1 :
        return 
    query = common.croll_economy()
    print(query)
    common.postgres_update(query)
    print('crawling 완료')

def machine_learning():
    print('machine_learning 호출')
    
    if date.today().day != 1 :
        return
    
    num = 0
    building_query = '''
        SELECT distinct loc FROM building
        '''
        
    loc = common.postgres_select(building_query)

    for i in range(num,len(loc)):
        place = loc['loc'][i]
        num = update_building2.update_query(num, place, col, lgbm_params1, lgbm_params2, xgb_params)

    print('머신러닝 완료')

def schedule_crawling() :
    schedule.every().day.at("00:00").do(crawling)
    while True :
        # print('t1 실행중')
        schedule.run_pending()
        time.sleep(60)

def schedule_machine_learning() :
    schedule.every().day.at("00:30").do(machine_learning)
    while True :
        # print('t2 실행중')
        schedule.run_pending()
        time.sleep(10)

def run1() :
    t1 = threading.Thread(target=schedule_crawling)
    add_script_run_ctx(t1, ctx=get_script_run_ctx())
    t1.start()

def run2() :    
    t2 = threading.Thread(target=schedule_machine_learning)
    add_script_run_ctx(t2, ctx=get_script_run_ctx())
    t2.start()
    