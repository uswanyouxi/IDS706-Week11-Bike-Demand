"""Phase A only: fetch public sources and record measured schemas/coverage.

No Airflow task, database writes, EDA, or ML training occurs here.
Run from the project root with Python 3.11. Standard library only.
"""
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'docs' / 'verification' / 'sources.json'
UCI_URL = 'https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip'
FIELDS = ['temperature_2m_mean', 'temperature_2m_max', 'temperature_2m_min',
          'precipitation_sum', 'wind_speed_10m_max']
PARAMS = dict(latitude='38.9072', longitude='-77.0369', start_date='2011-01-01',
              end_date='2012-12-31', daily=','.join(FIELDS), timezone='America/New_York',
              models='era5', temperature_unit='celsius', wind_speed_unit='kmh',
              precipitation_unit='mm', timeformat='iso8601')
WEATHER_URL = 'https://archive-api.open-meteo.com/v1/archive?' + urllib.parse.urlencode(PARAMS)
EXPECTED_DATES = [(date(2011, 1, 1) + timedelta(days=i)).isoformat() for i in range(731)]


def fetch(url, filename):
    request = urllib.request.Request(url, headers={'User-Agent': 'IDS706-PhaseA-source-verifier/1.0'})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read()
        metadata = dict(url=url, final_url=response.url, http_status=response.status,
                        content_type=response.headers.get('Content-Type'),
                        sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload),
                        retrieved_at_utc=datetime.now(timezone.utc).isoformat())
    (RAW / filename).write_bytes(payload)
    return payload, metadata


def csv_type(values):
    # CSV has text cells; these are observed parseable logical types.
    try:
        for value in values:
            int(value)
        return 'integer'
    except ValueError:
        pass
    try:
        for value in values:
            float(value)
        return 'number'
    except ValueError:
        pass
    try:
        for value in values:
            date.fromisoformat(value)
        return 'ISO date string'
    except ValueError:
        return 'string'


def verify_uci():
    payload, meta = fetch(UCI_URL, 'uci-bike-sharing.zip')
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        member = next(name for name in archive.namelist() if name.split('/')[-1] == 'day.csv')
        day = archive.read(member)
        rows = list(csv.DictReader(io.StringIO(day.decode('utf-8-sig'))))
        meta['archive_members'] = archive.namelist()
    (RAW / 'day.csv').write_bytes(day)
    dates = [r['dteday'] for r in rows]
    meta.update(rows=len(rows), columns=list(rows[0]),
                logical_types={k: csv_type([r[k] for r in rows]) for k in rows[0]},
                empty_counts={k: sum(r[k] == '' for r in rows) for k in rows[0]},
                min_date=min(dates), max_date=max(dates), duplicate_dates=len(dates)-len(set(dates)),
                exact_daily_coverage=sorted(dates) == EXPECTED_DATES,
                target_identity=all(int(r['cnt']) == int(r['casual']) + int(r['registered']) for r in rows))
    if not meta['exact_daily_coverage'] or not meta['target_identity']:
        raise ValueError('UCI coverage or target identity failed')
    meta['status'] = 'verified'
    return meta, set(dates)


def verify_weather():
    payload, meta = fetch(WEATHER_URL, 'open-meteo-era5-2011-2012.json')
    body = json.loads(payload)
    if body.get('error'):
        raise ValueError(body)
    daily = body['daily']
    dates = daily['time']
    meta.update(top_level_types={k: type(v).__name__ for k, v in body.items()},
                response_metadata={k: v for k, v in body.items() if k not in ('daily', 'daily_units')},
                daily_units=body['daily_units'],
                lengths={k: len(v) for k, v in daily.items()},
                value_types={k: sorted({type(x).__name__ for x in v}) for k, v in daily.items()},
                null_counts={k: sum(x is None for x in v) for k, v in daily.items()},
                min_date=min(dates), max_date=max(dates), duplicate_dates=len(dates)-len(set(dates)),
                exact_daily_coverage=dates == EXPECTED_DATES,
                samples={d: {k: daily[k][dates.index(d)] for k in daily} for d in
                         ['2011-01-01', '2011-03-13', '2011-11-06', '2012-02-29', '2012-12-31']})
    if body['timezone'] != PARAMS['timezone'] or not meta['exact_daily_coverage']:
        raise ValueError('Weather timezone or coverage failed')
    for field in FIELDS:
        if len(daily[field]) != 731 or any(type(x) not in (int, float) for x in daily[field]):
            raise ValueError(f'Invalid numeric array: {field}')
    expected_units = dict(zip(FIELDS, ['°C', '°C', '°C', 'mm', 'km/h']))
    if any(body['daily_units'][k] != unit for k, unit in expected_units.items()):
        raise ValueError('Unexpected weather units')
    meta['status'] = 'verified'
    return meta, set(dates)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'phase': 'A'}
    date_sets = {}
    for name, url, fn in [('uci', UCI_URL, verify_uci), ('open_meteo', WEATHER_URL, verify_weather)]:
        try:
            result[name], date_sets[name] = fn()
        except Exception as exc:
            result[name] = dict(status='unverified', url=url, error=f'{type(exc).__name__}: {exc}')
    if len(date_sets) == 2:
        a, b = date_sets['uci'], date_sets['open_meteo']
        result['date_join_probe'] = dict(matched_dates=len(a & b), uci_only=len(a-b), weather_only=len(b-a),
                                         note='Source date comparison only; no pipeline merge or DB load performed.')
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if all(result[k]['status'] == 'verified' for k in ('uci', 'open_meteo')) else 1


if __name__ == '__main__':
    raise SystemExit(main())
