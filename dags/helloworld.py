import datetime
from airflow.decorators import dag, task


@dag(schedule="@daily", start_date=datetime(2021, 12, 1), catchup=False)
def taskflow():

    @task
    def helloWorld():
        print("Hello World")

    helloWorld()

taskflow()

          