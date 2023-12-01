import threading
import time
from datetime import datetime
import common

class BackgroundTasks(threading.Thread):
    def run(self,*args,**kwargs):
        while True:
            print('background 실행')
            current_time = datetime.today().strftime("%d%H%M") 
            if current_time == '011200' :
                print('크롤링 수행')
                query = common.croll_economy()
                common.postgres_update(query)
                time.sleep(120)
