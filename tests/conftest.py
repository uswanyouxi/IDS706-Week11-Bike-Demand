"""Synthetic contract fixtures are labeled; real-source tests are separate."""
import io
import json
from datetime import date
import pandas as pd
import pytest
from bike_demand.contracts import EXPECTED_DATES, UCI_COLUMNS, WEATHER_COLUMNS, clean_bike, clean_weather, merge_dates

@pytest.fixture
def bike_csv():
    rows=[]
    for i,label in enumerate(EXPECTED_DATES):
        day=date.fromisoformat(label); weekday=(day.weekday()+1)%7
        rows.append([i+1,label,1,day.year-2011,day.month,0,weekday,int(weekday not in [0,6]),
                     1,0.5,0.5,0.5,0.1,100,200,300])
    return pd.DataFrame(rows,columns=UCI_COLUMNS).to_csv(index=False).encode()

@pytest.fixture
def weather_body():
    return {"latitude":39.0,"longitude":-77.0,"timezone":"America/New_York","utc_offset_seconds":-18000,
        "daily_units":dict(zip(["time"]+WEATHER_COLUMNS,["iso8601","°C","°C","°C","mm","km/h"])),
        "daily":{"time":list(EXPECTED_DATES),**{k:[v]*len(EXPECTED_DATES) for k,v in
            zip(WEATHER_COLUMNS,[15.0,20.0,10.0,1.0,12.0])}}}

@pytest.fixture
def merged_frame(bike_csv,weather_body):
    bike,_=clean_bike(bike_csv); weather,_=clean_weather(weather_body)
    return merge_dates(bike,weather)[0]
