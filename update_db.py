import common    
import update_building2
import threading
import time 

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


def update_db_by_query(address2) : 
    num = 0
    building_query = f'''
    SELECT distinct loc FROM building
    where (year1 is null or year1 = 0)
    and split_part(loc, ' ',2) = '{address2}'
    '''

    loc = common.postgres_select(building_query)

    for i in range(num,len(loc)):
        place = loc['loc'][i]
        num = update_building2.update_query(num, place, col, lgbm_params1, lgbm_params2, xgb_params)

if __name__ == '__main__':
    address2_df = common.postgres_select("select distinct address2 from address")
    for i, each in address2_df.iterrows():
        t = threading.Thread(target=update_db_by_query,args=(each['address2'],))
        t.start()
    time.sleep(3)
    for thread in threading.enumerate(): 
        print('***', thread.name)