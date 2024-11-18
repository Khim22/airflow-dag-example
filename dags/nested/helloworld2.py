from datetime import datetime
import time
from airflow.decorators import dag, task

@dag(schedule="@daily", start_date=datetime(2021, 12, 1), catchup=False)
def helloWorld():
    @task
    def helloWorld():
        time.sleep(2)
        print("Hello World 2")

    helloWorld()

helloWorld()