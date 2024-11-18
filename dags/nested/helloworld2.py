from datetime import datetime
import time
from airflow.decorators import dag, task

@dag(schedule="@daily", start_date=datetime(2021, 12, 1), catchup=False)
def helloWorld2():
    @task
    def helloWorld2():
        time.sleep(2)
        print("Hello World 2")

    helloWorld2()

helloWorld2()