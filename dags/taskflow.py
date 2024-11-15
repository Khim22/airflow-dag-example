from datetime import datetime, timedelta
import logging
from typing import List
import random

from airflow.decorators import dag, task
from airflow.operators.python_operator import PythonOperator

from sequence_sum_of_squares import returnListOfSums


@dag(schedule="@daily", start_date=datetime(2021, 12, 1), catchup=False)
def taskflow():
    logger = logging.getLogger("airflow.task")
    logger.setLevel(logging.DEBUG)

    @task
    def mark_start()-> None:
        print("Starting")
        logger.info("Mark start")

    @task(retries=3, retry_delay=timedelta(minutes=5))
    def local_executor() -> List[int]:
        logger.info("Executing local_executor task")
        random.seed(5)
        first  = random.randint(1,100)
        second = random.randint(1,100)
        res = [first, second]
        logger.info(f"Local executor task completed with result: {res}")
        return res
    
    @task(retries=3, retry_delay=timedelta(minutes=5))
    def sequence_sum_of_squares(numbers: List[int]) -> List[int]:
        logger.info("Executing sequence_sum_of_squares task")
        if len(numbers) < 2:
            raise ValueError("Input list should contain at least 2 numbers")
        sums = PythonOperator(python_callable=returnListOfSums, op_kwargs={"startNum":numbers[0], "endNum": numbers[1]})
        logger.info(f"Sequence sum of squares task completed with result: {sums}")
        return sums
    
    mark_start()
    sequence_sum_of_squares(local_executor())


taskflow()
        