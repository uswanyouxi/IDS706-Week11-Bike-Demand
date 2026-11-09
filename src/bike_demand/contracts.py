"""Strict contracts for the fixed, retrospective DC 2011–2012 study."""
from datetime import date, timedelta
import hashlib
import io
import json
import numpy as np
import pandas as pd

START, END = date(2011, 1, 1), date(2012, 12, 31)
EXPECTED_DATES = [(START + timedelta(days=i)).isoformat() for i in range((END-START).days+1)]
UCI_COLUMNS = "instant dteday season yr mnth holiday weekday workingday weathersit temp atemp hum windspeed casual registered cnt".split()
WEATHER_COLUMNS = ["temperature_2m_mean", "temperature_2m_max", "temperature_2m_min",
                   "precipitation_sum", "wind_speed_10m_max"]
BIKE_COLUMNS = ["date", "cnt", "yr", "mnth", "weekday", "season", "holiday", "workingday"]
FINAL_COLUMNS = BIKE_COLUMNS + WEATHER_COLUMNS

class ContractError(ValueError):
    """Permanent invalid input; not a transient network failure."""

def require(condition, message):
    if not condition:
        raise ContractError(message)

def dates_contract(frame, *, complete=True):
    require("date" in frame.columns, "Missing date column")
    values = frame["date"].tolist()
    require(all(isinstance(v, str) and len(v) == 10 for v in values), "Dates must be YYYY-MM-DD labels")
    try:
        parsed = [date.fromisoformat(v) for v in values]
    except ValueError:
        raise ContractError("Invalid ISO date") from None
    require(all(v.isoformat() == s for v, s in zip(parsed, values)), "Noncanonical date labels")
    require(not frame["date"].duplicated().any(), "Duplicate dates")
    if complete:
        actual = set(values)
        missing, extra = sorted(set(EXPECTED_DATES)-actual), sorted(actual-set(EXPECTED_DATES))
        require(not missing and not extra and len(values) == len(EXPECTED_DATES),
                f"Coverage mismatch: missing={len(missing)}, extra={len(extra)}, rows={len(values)}")
    return dict(rows=len(values), unique_dates=len(set(values)),
                min_date=min(values) if values else None, max_date=max(values) if values else None,
                expected_days=len(EXPECTED_DATES))

def numeric(frame, column, lower, upper, *, integer=False):
    try:
        values = pd.to_numeric(frame[column], errors="raise")
        array = values.to_numpy(dtype=float)
    except (TypeError, ValueError, KeyError):
        raise ContractError(f"Invalid numeric column: {column}") from None
    require(np.isfinite(array).all(), f"Nonfinite/missing values: {column}")
    require(((array >= lower) & (array <= upper)).all(), f"Out-of-range values: {column}")
    if integer:
        require((array == np.floor(array)).all(), f"Noninteger values: {column}")
    frame[column] = values.astype("int64" if integer else "float64")

def clean_bike(payload):
    try:
        frame = pd.read_csv(io.BytesIO(payload), dtype=str, keep_default_na=False)
    except Exception:
        raise ContractError("Could not parse UCI CSV") from None
    require(list(frame.columns) == UCI_COLUMNS, "Unexpected UCI day.csv schema/order")
    require(not frame.eq("").any().any(), "Empty UCI cells")
    frame = frame.rename(columns={"dteday": "date"})
    coverage = dates_contract(frame)
    for col, bounds in {"instant": (1, len(EXPECTED_DATES)), "season": (1, 4), "yr": (0, 1),
                        "mnth": (1, 12), "holiday": (0, 1), "weekday": (0, 6),
                        "workingday": (0, 1), "weathersit": (1, 4),
                        "casual": (0, 100000), "registered": (0, 100000), "cnt": (0, 100000)}.items():
        numeric(frame, col, *bounds, integer=True)
    for col in ["temp", "atemp", "hum", "windspeed"]:
        numeric(frame, col, 0, 1)
    require(not frame["instant"].duplicated().any(), "Duplicate UCI record IDs")
    require((frame["cnt"] == frame["casual"] + frame["registered"]).all(), "Count identity failed")
    parsed = pd.to_datetime(frame["date"], format="%Y-%m-%d")
    require((frame["mnth"] == parsed.dt.month).all(), "Month/date inconsistency")
    require((frame["yr"] == parsed.dt.year-2011).all(), "Year/date inconsistency")
    require((frame["weekday"] == (parsed.dt.day_of_week+1) % 7).all(), "Weekday/date inconsistency")
    expected_work = (~frame["weekday"].isin([0, 6]) & (frame["holiday"] == 0)).astype(int)
    require((frame["workingday"] == expected_work).all(), "Working-day/calendar inconsistency")
    frame[["holiday", "workingday"]] = frame[["holiday", "workingday"]].astype(bool)
    return frame[BIKE_COLUMNS].sort_values("date").reset_index(drop=True), coverage

def clean_weather(body):
    require(isinstance(body, dict) and not body.get("error"), "Invalid weather response")
    require(body.get("timezone") == "America/New_York", "Unexpected weather timezone")
    require(type(body.get("utc_offset_seconds")) is int, "Missing integer weather UTC offset")
    require(isinstance(body.get("latitude"), (int, float)) and isinstance(body.get("longitude"), (int, float)),
            "Missing weather coordinates")
    require(abs(body["latitude"]-38.9072) <= 0.5 and abs(body["longitude"]+77.0369) <= 0.5,
            "Unexpected weather grid point")
    daily, units = body.get("daily"), body.get("daily_units")
    require(isinstance(daily, dict) and isinstance(units, dict), "Missing daily weather arrays/units")
    expected_units = dict(zip(["time"]+WEATHER_COLUMNS, ["iso8601", "°C", "°C", "°C", "mm", "km/h"]))
    require(all(units.get(k) == v for k, v in expected_units.items()), "Unexpected weather units")
    require(all(isinstance(daily.get(k), list) for k in expected_units), "Missing weather array")
    size = len(daily["time"])
    require(all(len(daily[k]) == size for k in expected_units), "Weather array length mismatch")
    for col in WEATHER_COLUMNS:
        require(all(type(v) in (int, float) for v in daily[col]), f"Nonnumeric/null weather: {col}")
    frame = pd.DataFrame({k: daily[k] for k in expected_units}).rename(columns={"time": "date"})
    coverage = dates_contract(frame)
    for col in WEATHER_COLUMNS[:3]:
        numeric(frame, col, -60, 60)
    numeric(frame, "precipitation_sum", 0, 1000)
    numeric(frame, "wind_speed_10m_max", 0, 400)
    require(((frame["temperature_2m_min"] <= frame["temperature_2m_mean"]) &
             (frame["temperature_2m_mean"] <= frame["temperature_2m_max"])).all(),
            "Weather min/mean/max inconsistency")
    return frame.sort_values("date").reset_index(drop=True), {
        **coverage, "timezone": body["timezone"], "utc_offset_seconds": body["utc_offset_seconds"],
        "grid_latitude": body["latitude"], "grid_longitude": body["longitude"],
        "date_boundary_note": "API returned date labels; fixed-offset daily windows, not DST-exact civil days."}

def merge_dates(bike, weather):
    dates_contract(bike, complete=False)
    dates_contract(weather, complete=False)
    require(list(bike.columns) == BIKE_COLUMNS and list(weather.columns) == ["date"]+WEATHER_COLUMNS,
            "Unexpected cleaned branch columns")
    try:
        merged = bike.merge(weather, how="outer", on="date", validate="one_to_one", indicator=True)
    except pd.errors.MergeError:
        raise ContractError("Join is not one-to-one") from None
    counts = merged["_merge"].value_counts()
    diagnostics = dict(bike_only=int(counts.get("left_only", 0)), weather_only=int(counts.get("right_only", 0)),
                       matched=int(counts.get("both", 0)), bike_rows=len(bike), weather_rows=len(weather),
                       merged_rows=len(merged))
    require(diagnostics["bike_only"] == 0 and diagnostics["weather_only"] == 0,
            f"Unmatched join rows: {json.dumps(diagnostics, sort_keys=True)}")
    require(len(merged) == len(bike) == len(weather), "Join row explosion")
    result = merged[FINAL_COLUMNS].sort_values("date").reset_index(drop=True)
    validate_final(result)
    return result, diagnostics

def validate_final(frame):
    require(list(frame.columns) == FINAL_COLUMNS, "Unexpected final schema")
    dates_contract(frame)
    require(not frame.isna().any().any(), "Nulls in final dataset")
    for col in FINAL_COLUMNS[1:]:
        require(np.isfinite(frame[col].to_numpy(dtype=float)).all(), f"Nonfinite final values: {col}")

def dataset_hash(frame):
    validate_final(frame)
    records = frame.sort_values("date").to_dict(orient="records")
    return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
