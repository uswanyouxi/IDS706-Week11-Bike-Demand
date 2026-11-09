"""Explicit synthetic unit fixtures, never production ML evidence."""
import numpy as np
import pandas as pd
import pytest
from bike_demand.contracts import EXPECTED_DATES,dataset_hash

@pytest.fixture
def synthetic_frame():
    dates=pd.to_datetime(EXPECTED_DATES)
    t=np.arange(len(dates));temp=12+10*np.sin(2*np.pi*t/365)
    weekday=(dates.dayofweek+1)%7
    frame=pd.DataFrame({"date":EXPECTED_DATES,
        "cnt":np.rint(2500+4*t+60*temp+120*(weekday==5)).astype(int),
        "yr":dates.year-2011,"mnth":dates.month,"weekday":weekday,"season":(dates.month%12)//3+1,
        "holiday":False,"workingday":~np.isin(weekday,[0,6]),
        "temperature_2m_mean":temp,"temperature_2m_max":temp+5,"temperature_2m_min":temp-5,
        "precipitation_sum":np.where(t%7==0,3.0,0.0),"wind_speed_10m_max":12+(t%9)})
    return frame

@pytest.fixture
def synthetic_loader(synthetic_frame):
    def load():
        return synthetic_frame.copy(),{"origin":"synthetic_unit_fixture","database":"synthetic_unit_fixture",
            "table":"synthetic_unit_fixture","transaction_read_only":"not-a-db-test",
            "rows":len(synthetic_frame),"dataset_hash":dataset_hash(synthetic_frame)}
    return load
