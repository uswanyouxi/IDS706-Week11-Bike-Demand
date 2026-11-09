"""Real DagBag parsing: skip explicitly if Airflow is unavailable."""
from pathlib import Path
import pytest

pytestmark=pytest.mark.airflow

def test_real_airflow_dag_contract():
    pytest.importorskip("airflow")
    from airflow.dag_processing.dagbag import DagBag
    folder=Path(__file__).resolve().parents[2]/"dags"
    bag=DagBag(dag_folder=str(folder),safe_mode=False)
    assert bag.import_errors=={}
    dag=bag.dags.get("dc_bike_weather_daily")
    assert dag is not None and dag.catchup is False
    assert dag.max_active_runs==1 and dag.max_active_tasks==2
    assert str(dag.timezone)=="America/New_York"
    assert dag.schedule=="0 6 * * *"
    expected={"start","download_uci","fetch_era5_weather","clean_bike","clean_weather",
              "validate_and_merge_dates","load_application_postgres","read_database_and_make_eda","end"}
    assert set(dag.task_ids)==expected
    assert dag.get_task("download_uci").downstream_task_ids=={"clean_bike"}
    assert dag.get_task("fetch_era5_weather").downstream_task_ids=={"clean_weather"}
    assert dag.get_task("validate_and_merge_dates").upstream_task_ids=={"clean_bike","clean_weather"}
    assert dag.get_task("download_uci").retries==2
    assert dag.get_task("clean_bike").retries==0
    assert dag.get_task("read_database_and_make_eda").upstream_task_ids=={"load_application_postgres"}
