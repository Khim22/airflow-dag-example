from datetime import datetime, timedelta
import logging
import time
from typing import List
import random

from airflow.decorators import dag, task

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
        res.sort()
        logger.info(f"Local executor task completed with result: {res}")
        return res
    
    @task(retries=3, retry_delay=timedelta(minutes=5))
    def sequence_sum_of_squares(numbers: List[int]) -> List[int]:
        logger.info(f"Executing sequence_sum_of_squares task {numbers}")
        if len(numbers) < 2:
            raise ValueError("Input list should contain at least 2 numbers")
        startNum, endNum = numbers
        ans = []
        for i in range(startNum, endNum):
            ans.append(squaresum(i))
        logger.info(f"Sequence sum of squares task completed with result: {ans}")
        return ans

    def squaresum(n: int)-> int:
        logger.info("squaresum", n)
        print('bye', n)
        # Iterate i from 1
        # and n finding
        # square of i and
        # add to sum.
        sm = 0
        for i in range(1, n+1):
            sm = sm + (i * i)

        return sm
    
    @task.virtualenv(
        task_id="virtualenv_python", requirements=["colorama==0.4.0"], system_site_packages=False
    )
    def callable_virtualenv(squares: List[int]):
        """
        Example function that will be performed in a virtual environment.

        Importing at the module level ensures that it will not attempt to import the
        library before it is installed.
        """
        from time import sleep
        import logging
        from colorama import Back, Fore, Style

        logger = logging.getLogger("airflow.task")
        logger.setLevel(logging.DEBUG)
        logger.info(f"passing from previous step {squares}")
        print(Fore.RED + "some red text")
        print(Back.GREEN + "and with a green background")
        print(Style.DIM + "and in dim text")
        print(Style.RESET_ALL)
        for _ in range(4):
            print(Style.DIM + "Please wait...", flush=True)
            sleep(1)
        print("Finished")

    @task.kubernetes(image="python:3.11-bookworm", namespace="airflow", in_cluster=True, get_logs=True)
    def print_numpy(numbers):
        import logging

        logger = logging.getLogger("airflow.task")
        logger.setLevel(logging.DEBUG)
        logger.info(f"passing from previous step {numbers}")

        print(numbers)

    @task(retries=3, retry_delay=timedelta(minutes=1), executor_config={"KubernetesExecutor": {"image": "publysher/alpine-numpy:1.14.0-python3.6-alpine3.7"}})
    def pythonoperator_kubeExecutor(numbers: List[int]) -> List[int]:
        import logging
        import numpy as np

        logger = logging.getLogger("airflow.task")
        logger.setLevel(logging.DEBUG)
        logger.info(f"passing from previous step {numbers}")
        arr = np.array(numbers)
        print(arr)
    
    @task(retries=3, retry_delay=timedelta(minutes=0.1))
    def wait_tasks() -> None:
        # raise ValueError("wait_tasks")
        time.sleep(10)
        
    @task
    def mark_end()-> None:
        print("Ending")
        logger.info("Mark Ending")


    local_executor_res = local_executor()
    mark_start()>> local_executor_res
    seq_res = sequence_sum_of_squares(local_executor_res)
    callable_res = callable_virtualenv(seq_res)
    print_res = print_numpy(seq_res)
    exec_res = pythonoperator_kubeExecutor(seq_res)

    wait_res = wait_tasks()
    seq_res >> wait_res

    [callable_res ,print_res , exec_res, wait_res] >> mark_end()


taskflow()