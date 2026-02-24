from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="test_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    
    task1 = BashOperator(
        task_id="say_hello",
        bash_command="echo Hello Sajan",
    )
    
    tas2 = BashOperator(
        task_id="say_bye",
        bash_command="echo Bye Sajan",
    )
    
    task1 >> task2