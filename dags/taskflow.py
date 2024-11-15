from datetime import datetime, timedelta
import logging
from typing import List
from airflow.decorators import dag, task

from sequence_sum_of_squares import returnListOfSums


@dag(schedule="@daily", start_date=datetime(2021, 12, 1), catchup=False)
def taskflow():
    logger = logging.getLogger("airflow.task")
    logger.setLevel(logging.DEBUG)

    @task()
    def mark_start()-> None:
        print("Starting")
        logger.info("Mark start")

    @task(retries=3, retry_delay=timedelta(minutes=5))
    def local_executor() -> List[int]:
        logger.info("Executing local_executor task")
        # # Simulating a long-running task
        # res = returnListOfSums(2)
        # logger.info(f"Local executor task completed with result: {res}")
        # return res
    
    mark_start >> local_executor()

taskflow()
        