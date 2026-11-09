import copy
import io
import json
from pathlib import Path
import pandas as pd
import pytest
from bike_demand.contracts import *

def test_full_coverage_and_no_leakage(bike_csv,weather_body):
    bike,coverage=clean_bike(bike_csv); weather,_=clean_weather(weather_body)
    merged,report=merge_dates(bike,weather)
    assert len(merged)==coverage["expected_days"]==731
    assert "2012-02-29" in merged["date"].values
    assert report["matched"]==731 and report["bike_only"]==report["weather_only"]==0
    assert not {"casual","registered","instant","temp","atemp","hum","windspeed","weathersit"} & set(merged.columns)

@pytest.mark.parametrize("column,value", [("cnt",-1),("holiday",2),("hum",1.1),("weekday",0),("cnt",300.5)])
def test_bad_bike_values_rejected(bike_csv,column,value):
    frame=pd.read_csv(io.BytesIO(bike_csv)).astype(object); frame.loc[0,column]=value
    with pytest.raises(ContractError):
        clean_bike(frame.to_csv(index=False).encode())

def test_target_identity_rejected(bike_csv):
    frame=pd.read_csv(io.BytesIO(bike_csv)); frame.loc[0,"registered"]=201
    with pytest.raises(ContractError,match="identity"):
        clean_bike(frame.to_csv(index=False).encode())

def test_duplicate_dates_rejected(bike_csv):
    frame=pd.read_csv(io.BytesIO(bike_csv)); frame.loc[1,"dteday"]=frame.loc[0,"dteday"]
    with pytest.raises(ContractError,match="Duplicate"):
        clean_bike(frame.to_csv(index=False).encode())

def test_missing_coverage_rejected(bike_csv):
    frame=pd.read_csv(io.BytesIO(bike_csv)).iloc[:-1]
    with pytest.raises(ContractError,match="Coverage"):
        clean_bike(frame.to_csv(index=False).encode())

@pytest.mark.parametrize("mutation",["null","string","length","unit","timezone","ordering","negative_rain"])
def test_weather_contract_failures(weather_body,mutation):
    body=copy.deepcopy(weather_body)
    if mutation=="null": body["daily"]["temperature_2m_mean"][0]=None
    elif mutation=="string": body["daily"]["temperature_2m_mean"][0]="15.0"
    elif mutation=="length": body["daily"]["temperature_2m_mean"].pop()
    elif mutation=="unit": body["daily_units"]["wind_speed_10m_max"]="m/s"
    elif mutation=="timezone": body["timezone"]="GMT"
    elif mutation=="ordering": body["daily"]["temperature_2m_min"][0]=30
    elif mutation=="negative_rain": body["daily"]["precipitation_sum"][0]=-1
    with pytest.raises(ContractError):
        clean_weather(body)

def test_merge_reports_unmatched_not_inner_drop(bike_csv,weather_body):
    bike,_=clean_bike(bike_csv); weather,_=clean_weather(weather_body)
    with pytest.raises(ContractError,match='"bike_only": 1'):
        merge_dates(bike,weather.iloc[1:])

def test_merge_duplicate_prevents_row_explosion(bike_csv,weather_body):
    bike,_=clean_bike(bike_csv); weather,_=clean_weather(weather_body)
    with pytest.raises(ContractError,match="Duplicate"):
        merge_dates(bike,pd.concat([weather,weather.iloc[:1]]))

def test_hash_stable_under_row_order(merged_frame):
    assert dataset_hash(merged_frame)==dataset_hash(merged_frame.iloc[::-1])

def test_cached_real_sources():
    raw=Path(__file__).resolve().parents[2]/"data"/"raw"
    if not (raw/"day.csv").exists() or not (raw/"open-meteo-era5-2011-2012.json").exists():
        pytest.skip("Optional prior real-source downloads not present")
    bike,b=clean_bike((raw/"day.csv").read_bytes())
    weather,w=clean_weather(json.loads((raw/"open-meteo-era5-2011-2012.json").read_text(encoding="utf-8")))
    merged,report=merge_dates(bike,weather)
    assert len(merged)==b["rows"]==w["rows"]==report["matched"]==731
