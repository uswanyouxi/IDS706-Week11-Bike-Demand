# Source verification — November 8, 2026 (America/New_York)

`py -3.11 scripts/verify_sources.py` exited 0. Retrieval timestamps are recorded
in UTC (November 9 UTC is November 8 evening EST). The first sandbox network
attempt failed; the approved outside-sandbox downloads then returned HTTP 200.
The report contains actual response metadata, SHA-256 hashes and sample values.
Raw downloads stay under ignored `data/raw/`; no database load was performed.

## UCI actual archive and CSV

Exact download: https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip

Archive measured 279,992 bytes, SHA-256
`b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401`.
Its members are `Readme.txt`, `day.csv`, `hour.csv`. Only `day.csv` was inspected
for the daily schema; the website's hourly instance count is not the daily count.

The downloaded CSV has 731 rows, 16 columns, 731 unique contiguous dates,
2011-01-01 through 2012-12-31 inclusive (including leap day). There are no empty
cells. CSV cells are text on disk; the logical types below were measured by parsing
every value, not inferred solely from the website.

| Columns | Observed parseable type |
| --- | --- |
| dteday | ISO date string |
| instant, season, yr, mnth, holiday, weekday, workingday, weathersit | integer |
| temp, atemp, hum, windspeed | numeric (decimal) |
| casual, registered, cnt | integer |

`cnt == casual + registered` holds for all 731 rows; both components must be
excluded from predictors. `hr` is absent from day.csv. No timezone field exists;
these are rental-day calendar labels, not zoned timestamps. Project interpretation
is DC local date, with this source precision limitation stated explicitly.

Source/citation/license: [UCI Bike Sharing](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset)
by Hadi Fanaee-T (2013), DOI `10.24432/C5W894`, CC BY 4.0. Preserve attribution
and describe transformations. No authenticated API or documented daily-download
quota was identified for this public ZIP; do not invent one. Cache raw artifacts
and avoid needless repeated downloads.

## Open-Meteo actual response

Exact tested URL (single full-range request):

```text
https://archive-api.open-meteo.com/v1/archive?latitude=38.9072&longitude=-77.0369&start_date=2011-01-01&end_date=2012-12-31&daily=temperature_2m_mean%2Ctemperature_2m_max%2Ctemperature_2m_min%2Cprecipitation_sum%2Cwind_speed_10m_max&timezone=America%2FNew_York&models=era5&temperature_unit=celsius&wind_speed_unit=kmh&precipitation_unit=mm&timeformat=iso8601
```

HTTP 200, JSON response, 27,625 bytes at verification. Requested DC coordinates
38.9072/-77.0369; returned grid point 39.0/-77.0, elevation 25.0 m. Requested
ERA5 was accepted; the response does not independently return a model-name field,
so the saved URL records the requested model. Top-level latitude, longitude,
generationtime_ms and elevation were JSON numbers parsed as floats;
utc_offset_seconds was an integer; timezone/abbreviation strings; daily/daily_units
objects. Response `timezone` is `America/New_York`, abbreviation `GMT-5`, offset
`-18000`. Preserve these actual metadata rather than assuming hourly DST offsets.

| daily field | Actual element type | Unit | Length / null count |
| --- | --- | --- | --- |
| time | ISO date strings | iso8601 | 731 / 0 |
| temperature_2m_mean | JSON numbers (Python float) | °C | 731 / 0 |
| temperature_2m_max | JSON numbers (Python float) | °C | 731 / 0 |
| temperature_2m_min | JSON numbers (Python float) | °C | 731 / 0 |
| precipitation_sum | JSON numbers (Python float) | mm | 731 / 0 |
| wind_speed_10m_max | JSON numbers (Python float) | km/h | 731 / 0 |

Dates are unique, contiguous, ordered, and cover the exact 731 expected labels.
The source-date comparison finds 731 matches, 0 UCI-only and 0 weather-only dates.
This is potential join coverage, not evidence of a loaded final table.

The [historical API documentation](https://open-meteo.com/en/docs/historical-weather-api)
requires a timezone for daily fields and describes ISO date inputs, numeric arrays
and grid-cell selection. Its current text explicitly describes a fixed request-time
UTC offset and 24-hour daily aggregations; DST changes within the range are ignored.
The design therefore joins returned date labels with a documented civil-day boundary
limitation, rather than claiming DST-exact alignment. Exact 23/25-hour civil-day
aggregation would require separately verified hourly processing.

## Access limits and fallback instructions

The educational free endpoint needs no key. The [terms](https://open-meteo.com/en/terms)
allow noncommercial/educational use and require CC BY 4.0 attribution; state limits
below 600 calls/minute, 5,000/hour and 10,000/day. The current
[pricing page](https://open-meteo.com/en/pricing) also lists a 300,000/month free
budget. Requests exceeding two weeks or ten variables count as multiple weighted
calls. The full-range request's exact charged units were not returned/measured;
do not equate one HTTP request to one quota unit. This successful 731-day request
confirms that this range was accepted; no universal maximum-range claim is made.
Handle HTTP 429, bounded backoff and Retry-After; do not stress-test quotas.

If network is blocked on a later machine, keep its status **unverified**. Open the
exact ZIP and API URLs above in a browser or run the standard-library verifier
from PowerShell with approved network access. It writes an error and URL in
`sources.json` and exits nonzero if either source cannot be checked. Do not replace
failed responses with guessed columns, synthetic weather or successful status.
For offline checking only, preserve previously downloaded files with their hashes;
an old fixture is not evidence of a new successful remote fetch.
