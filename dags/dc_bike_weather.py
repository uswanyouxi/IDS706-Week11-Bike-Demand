"""Original daily two-source retrospective pipeline. No I/O during DAG parsing."""
from datetime import timedelta
import pendulum
from airflow.sdk import dag, task, get_current_context
from airflow.exceptions import AirflowException
from airflow.sdk.exceptions import AirflowFailException
from airflow.providers.standard.operators.empty import EmptyOperator

def stage(task_id, function, **kwargs):
    from bike_demand.pipeline import execute_stage
    from bike_demand.contracts import ContractError
    context = get_current_context()
    try:
        return execute_stage(context["run_id"],task_id,context["ti"].try_number,function,**kwargs)
    except ContractError as exc:
        raise AirflowFailException(f"{task_id}: {exc}") from None
    except Exception as exc:
        raise AirflowException(f"{task_id}: {type(exc).__name__}; see sanitized run audit") from None

@dag(dag_id="dc_bike_weather_daily", schedule="0 6 * * *",
     start_date=pendulum.datetime(2026,11,1,tz="America/New_York"),catchup=False,
     max_active_runs=1,max_active_tasks=2,dagrun_timeout=timedelta(minutes=30),
     default_args={"retries":2,"retry_delay":timedelta(seconds=60),
                   "retry_exponential_backoff":True,"max_retry_delay":timedelta(minutes=5),
                   "execution_timeout":timedelta(minutes=10)},
     tags=["ids706","dc-bike","part1"],description="Original parallel UCI + ERA5; application-DB-fed EDA")
def dc_bike_weather_daily():
    @task(task_id="download_uci",multiple_outputs=False)
    def download_uci():
        from bike_demand.sources import ingest_uci
        return stage("download_uci",ingest_uci,run_id=get_current_context()["run_id"])

    @task(task_id="fetch_era5_weather",multiple_outputs=False)
    def fetch_weather():
        from bike_demand.sources import ingest_weather
        return stage("fetch_era5_weather",ingest_weather,run_id=get_current_context()["run_id"])

    @task(task_id="clean_bike",retries=0,multiple_outputs=False)
    def clean_bike(raw):
        from bike_demand.pipeline import clean_bike as operation
        return stage("clean_bike",operation,source=raw,run_id=get_current_context()["run_id"])

    @task(task_id="clean_weather",retries=0,multiple_outputs=False)
    def clean_weather(raw):
        from bike_demand.pipeline import clean_weather as operation
        return stage("clean_weather",operation,source=raw,run_id=get_current_context()["run_id"])

    @task(task_id="validate_and_merge_dates",retries=0,multiple_outputs=False)
    def merge(bike,weather):
        from bike_demand.pipeline import merge as operation
        return stage("validate_and_merge_dates",operation,bike=bike,weather=weather,run_id=get_current_context()["run_id"])

    @task(task_id="load_application_postgres",multiple_outputs=False)
    def load(merged):
        from bike_demand.pipeline import load as operation
        return stage("load_application_postgres",operation,merged=merged,run_id=get_current_context()["run_id"])

    @task(task_id="read_database_and_make_eda",multiple_outputs=False)
    def analyze(receipt):
        from bike_demand.eda import analyze as operation
        return stage("read_database_and_make_eda",operation,receipt=receipt)

    start,end = EmptyOperator(task_id="start"),EmptyOperator(task_id="end")
    uci,weather = download_uci(),fetch_weather()
    start >> [uci,weather]
    merged = merge(clean_bike(uci),clean_weather(weather))
    analyze(load(merged)) >> end

dag = dc_bike_weather_daily()
