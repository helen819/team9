import pandas as pd
import psycopg2
import joblib
import common
import lightgbm as lgbm
import xgboost as xgb
from sklearn.ensemble import GradientBoostingRegressor, StackingRegressor
from sklearn.linear_model import LinearRegression

# postgres
connection_info = "host=147.47.200.145 dbname=teamdb9 user=team9 password=aplus port=34543"

def get_model(lgbm_params1, lgbm_params2, xgb_params):
    

    lgbm_model1 = lgbm.LGBMRegressor(lgbm_params1, verbose=100)
    lgbm_model2 = lgbm.LGBMRegressor(lgbm_params2, verbose=100)
    xgb_model = xgb.XGBRegressor(xgb_params, verbose=100)


    lgbm_model1 =  joblib.load('./model_weight/lgbm_model1.pkl')
    lgbm_model2 =  joblib.load('./model_weight/lgbm_model2.pkl')
    # gbr_model =  joblib.load('./model_weight/gbr_model.pkl')
    xgb_model =  joblib.load('./model_weight/xgb_model.pkl')

    stack_models = [
        ('lgbm1', lgbm_model1),
        ('lgbm2', lgbm_model2),
        ('xgb', xgb_model)
    ]

    linear = LinearRegression(fit_intercept = False)
    stack_models = StackingRegressor(stack_models, final_estimator = linear, n_jobs = -1)
    stack_models = joblib.load('./model_weight/stack.pkl')
    return stack_models

def min_weight_bir(x):
    min = 0.5
    max = 5.25
    return (x-min)/(max-min)

def min_weight_m2(x):
    min = 1286.4
    max = 3830.9
    return (x-min)/(max-min)

def get_data(loc, date, col, lgbm_params1, lgbm_params2, xgb_params):    
    building_query = '''
    SELECT * FROM building3
    WHERE loc = '{}'
    ORDER BY year DESC
    LIMIT 1;
    '''.format(loc)

    economy_query = '''
    SELECT distinct * FROM economy
    WHERE date = {}
    '''.format(date)

    building_df = common.postgres_select(building_query)
    economy_df = common.postgres_select(economy_query)

    bir = economy_df['call_rate'] 
    m2 = economy_df['m2']

    building_df["M2"] = min_weight_m2(m2)
    building_df["bir"] = min_weight_bir(bir)
    
    building_df = building_df[col]
    
    stack_model = get_model(lgbm_params1, lgbm_params2, xgb_params)
    
    anw = stack_model.predict(building_df.iloc[0:1].fillna(0)) 
    anw = anw[0]-bir*1000+m2*2000
    return anw

def update_query(num, place, col, lgbm_params1, lgbm_params2, xgb_params):
    now_year = 202312
    print(place)
    for i in range(1,11):
        year = now_year + 100*i
        globals()['year{}'.format(i)] = get_data(place, year, col, lgbm_params1, lgbm_params2, xgb_params)[0]

    update_query = '''
    UPDATE building
    SET
        year1 = {},
        year2 = {},
        year3 = {},
        year4 = {},
        year5 = {},
        year6 = {},
        year7 = {},
        year8 = {},
        year9 = {},
        year10 = {}
    WHERE
        loc = '{}';
    '''.format(year1, year2, year3, year4, year5, year6, year7, year8, year9, year10, place)

    common.postgres_update(update_query)
    num += 1
    return num
    


    
    
    
