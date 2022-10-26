###############################################
# Import Necessary Libraries
import airflow
from datetime import timedelta
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator 
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.utils.dates import days_ago
###############################################
# Parameters
###############################################
# Spark App Name; shown on Spark UI
spark_app_name = "Postgresdb"
###############################################
# Path to Jars
jar_home="/usr/local/spark/resources"
###############################################
# Runtime Arguments
app_jars=f'{jar_home}/jars/postgresql-42.4.0.jar'
driver_class_path=f'{jar_home}/jars/postgresql-42.4.0.jar'
###############################################
###############################################
# DAG Definition
###############################################
# Arguments
args = {
    'owner': 'airflow',    
    'retry_delay': timedelta(minutes=5),
}
###############################################
# DAG Definition
with DAG(
    dag_id='Postgres-Spark',
    default_args=args,
    schedule_interval=None,
    start_date=days_ago(1),
    tags=['load/read/data', 'postgres'],
) as dag:
        start_task = DummyOperator(
	task_id='start_task'
)
###############################################
# Sequence of Tasks
###############################################
spark_job_load_postgres = SparkSubmitOperator(task_id='Load_Data',
                                              conn_id='post_connect',
                                              application='/usr/local/spark/app/postgres/load-postgres.py',
                                              total_executor_cores=2, jars=app_jars, driver_class_path=driver_class_path,
                                              packages="org.postgresql:postgresql:42.4.0",
                                              executor_cores=2,
                                              executor_memory='2g',
                                              driver_memory='2g',
                                              name=spark_app_name,
                                              execution_timeout=timedelta(minutes=10),
                                              dag=dag
                                              ) 
############################################### 
end = DummyOperator(task_id="end", dag=dag)
###############################################
start_task >> spark_job_load_postgres >> end
###############################################