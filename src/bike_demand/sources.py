"""Real HTTP ingestion; one network attempt per Airflow task attempt."""
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import hashlib
import io
import json
import time
import zipfile
import requests
from bike_demand.contracts import ContractError
from bike_demand.io_utils import atomic_bytes, data_dir, now, write_json

UCI_URL = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"
WEATHER_URL = ("https://archive-api.open-meteo.com/v1/archive?latitude=38.9072&longitude=-77.0369"
    "&start_date=2011-01-01&end_date=2012-12-31"
    "&daily=temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max"
    "&timezone=America%2FNew_York&models=era5&temperature_unit=celsius"
    "&wind_speed_unit=kmh&precipitation_unit=mm&timeformat=iso8601")

class SourceUnavailable(RuntimeError):
    pass

def retry_after_seconds(value):
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        try:
            seconds = (parsedate_to_datetime(value)-datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            seconds = 0
    return max(0, min(300, seconds))

def download(url, limit=10_000_000):
    try:
        with requests.get(url, timeout=(10, 75), stream=True,
                          headers={"User-Agent": "IDS706-DCBike-Part1/1.0"}) as response:
            if response.status_code == 429:
                time.sleep(retry_after_seconds(response.headers.get("Retry-After")))
                raise SourceUnavailable("Rate limited; no nested HTTP retries")
            if response.status_code >= 500:
                raise SourceUnavailable(f"Source HTTP {response.status_code}")
            if response.status_code != 200:
                raise ContractError(f"Permanent source HTTP {response.status_code}")
            chunks, size = [], 0
            for chunk in response.iter_content(65536):
                size += len(chunk)
                if size > limit:
                    raise ContractError("Source exceeds size limit")
                chunks.append(chunk)
            payload = b"".join(chunks)
            if not payload:
                raise ContractError("Empty source body")
            return payload, dict(url=url, final_url=response.url, http_status=response.status_code,
                retrieved_at_utc=now(), bytes=size, sha256=hashlib.sha256(payload).hexdigest(),
                content_type=response.headers.get("Content-Type"))
    except requests.RequestException:
        raise SourceUnavailable("Source connection/timeout failure") from None

def ingest_uci(run_id):
    payload, meta = download(UCI_URL)
    folder = data_dir(run_id) / "raw"
    atomic_bytes(folder/"uci.zip", payload)
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            candidates = [n for n in archive.namelist() if n.split("/")[-1] == "day.csv"]
            if len(candidates) != 1 or archive.getinfo(candidates[0]).file_size > 2_000_000:
                raise ContractError("Unexpected day.csv archive member")
            day = archive.read(candidates[0])
    except (zipfile.BadZipFile, RuntimeError):
        raise ContractError("Invalid UCI archive") from None
    atomic_bytes(folder/"day.csv", day)
    meta.update(path=str(folder/"day.csv"), raw_path=str(folder/"uci.zip"),
                day_csv_sha256=hashlib.sha256(day).hexdigest())
    write_json(folder/"uci-source.json", meta)
    return meta

def ingest_weather(run_id):
    payload, meta = download(WEATHER_URL)
    try:
        body = json.loads(payload)
    except (ValueError, UnicodeDecodeError):
        raise ContractError("Weather endpoint did not return JSON") from None
    if not isinstance(body, dict) or body.get("error"):
        raise ContractError("Weather endpoint returned an error object")
    path = data_dir(run_id)/"raw"/"weather.json"
    atomic_bytes(path, payload)
    meta.update(path=str(path), requested_model="era5", requested_timezone="America/New_York")
    write_json(path.with_name("weather-source.json"), meta)
    return meta
