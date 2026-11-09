from unittest.mock import MagicMock, patch
import json
import pytest
from bike_demand import sources, pipeline
from bike_demand.contracts import ContractError, FINAL_COLUMNS, dataset_hash
from bike_demand.io_utils import artifact_dir, write_json

def test_json_roundtrip_preserves_contract_column_order(tmp_path,merged_frame):
    path=tmp_path/"rows.json"; write_json(path,merged_frame.to_dict(orient="records"))
    reread=pipeline.read_frame_file(path,FINAL_COLUMNS)
    assert dataset_hash(reread)==dataset_hash(merged_frame)

def test_run_id_is_not_a_path_escape(tmp_path,monkeypatch):
    monkeypatch.setenv("PROJECT_ARTIFACT_DIR",str(tmp_path))
    assert artifact_dir("../../escape").parent==tmp_path/"pipeline"

def test_failure_audit_sanitizes_unknown_exceptions(tmp_path,monkeypatch):
    monkeypatch.setenv("PROJECT_ARTIFACT_DIR",str(tmp_path))
    def failure(): raise RuntimeError("password=do-not-log")
    with pytest.raises(RuntimeError):
        pipeline.execute_stage("test","load",1,failure)
    body=next(tmp_path.rglob("*.json")).read_text()
    assert "failed" in body and "do-not-log" not in body

def test_stage_can_forward_run_id(tmp_path,monkeypatch):
    monkeypatch.setenv("PROJECT_ARTIFACT_DIR",str(tmp_path))
    assert pipeline.execute_stage("audit","task",1,lambda run_id: {"id":run_id},run_id="forward")=={"id":"forward"}

@pytest.mark.parametrize("code,error",[(400,ContractError),(500,sources.SourceUnavailable)])
def test_http_permanent_vs_transient(code,error):
    response=MagicMock(); response.status_code=code
    response.__enter__.return_value=response
    with patch.object(sources.requests,"get",return_value=response) as get:
        with pytest.raises(error): sources.download(sources.UCI_URL)
        assert get.call_count==1

def test_rate_limit_wait_bounded():
    response=MagicMock(); response.status_code=429; response.headers={"Retry-After":"99999"}
    response.__enter__.return_value=response
    with patch.object(sources.requests,"get",return_value=response) as get,patch.object(sources.time,"sleep") as sleep:
        with pytest.raises(sources.SourceUnavailable): sources.download(sources.WEATHER_URL)
        sleep.assert_called_once_with(300)
        assert get.call_count==1
