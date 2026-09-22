from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
from pendulum import datetime

PROJECT = "/usr/local/airflow"
DBT = f"{PROJECT}/dbt"

with DAG(
    dag_id="ledger_pipeline",
    start_date=datetime(2026, 3, 1),
    schedule="@daily",
    catchup=False,
    tags=["ledger"],
):

    extract = BashOperator(
        task_id="extract_validate_transform",
        bash_command=f"cd {PROJECT} && python main.py",
    )

    seed = BashOperator(
        task_id="dbt_seed",
        bash_command=f"cd {DBT} && dbt seed --profiles-dir .",
    )

    run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT} && dbt run --profiles-dir .",
    )

    test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT} && dbt test --profiles-dir .",
    )

    extract >> seed >> run >> test
