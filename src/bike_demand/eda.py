"""Figures/findings from a fresh application-PostgreSQL SELECT only."""
from bike_demand.io_utils import artifact_dir, atomic_bytes, now, write_json
from bike_demand.storage import read_snapshot, record_analysis

def analyze(receipt):
    frame, provenance = read_snapshot(receipt["run_id"], receipt["dataset_hash"])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    folder = artifact_dir(receipt["run_id"])/"eda"
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    weekday = frame.groupby("weekday")["cnt"].mean().reindex(range(7))
    monthly = frame.groupby("mnth")["cnt"].mean().reindex(range(1,13))
    for name, series, labels, xlabel in [
        ("weekday_mean_rentals.png", weekday, ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"], "DC rental-day weekday"),
        ("monthly_mean_rentals.png", monthly, [str(i) for i in range(1,13)], "Calendar month")]:
        fig, ax = plt.subplots(figsize=(8,4.5))
        ax.bar(labels, series.values, color="#16697a")
        ax.set(xlabel=xlabel, ylabel="Mean daily rentals", title="Capital Bikeshare 2011–2012 (database data)")
        fig.tight_layout()
        path = folder/name
        fig.savefig(path, dpi=150)
        plt.close(fig)
        paths.append(str(path))
    fig, ax = plt.subplots(figsize=(8,4.5))
    points = ax.scatter(frame["temperature_2m_mean"], frame["cnt"], c=frame["precipitation_sum"],
                        cmap="viridis", s=16, alpha=0.8)
    fig.colorbar(points, ax=ax, label="Daily precipitation (mm)")
    ax.set(xlabel="ERA5 mean daily temperature (°C)", ylabel="Daily rentals",
           title="Retrospective demand and reanalysis weather (database data)")
    fig.tight_layout()
    path = folder/"weather_vs_demand.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    paths.append(str(path))
    mean_temp_corr = float(frame["cnt"].corr(frame["temperature_2m_mean"]))
    rain_corr = float(frame["cnt"].corr(frame["precipitation_sum"]))
    summary = {**provenance, "created_at_utc": now(), "charts": paths,
        "date_min": frame["date"].min(), "date_max": frame["date"].max(),
        "total_rentals": int(frame["cnt"].sum()), "mean_daily_rentals": float(frame["cnt"].mean()),
        "temperature_pearson_r": mean_temp_corr, "precipitation_pearson_r": rain_corr,
        "weekday_mean_rentals": {str(k):float(v) for k,v in weekday.items()},
        "monthly_mean_rentals": {str(k):float(v) for k,v in monthly.items()},
        "interpretation": "Retrospective associations only; no causal or future-forecast claim. API fixed-offset day boundaries apply."}
    write_json(folder/"summary.json", summary)
    text = (f"Read {len(frame)} persisted rows from {provenance['database']}.{provenance['table']}.\n"
            f"Dates: {summary['date_min']} to {summary['date_max']}; total rentals: {summary['total_rentals']:,}.\n"
            f"Mean daily rentals: {summary['mean_daily_rentals']:.2f}.\n"
            f"Demand/temperature Pearson r: {mean_temp_corr:.3f}; demand/precipitation r: {rain_corr:.3f}.\n"
            f"{summary['interpretation']}\n")
    atomic_bytes(folder/"summary.txt", text.encode())
    record_analysis(receipt["run_id"], summary)
    return dict(rows=len(frame),dataset_hash=receipt["dataset_hash"],charts=paths,summary=str(folder/"summary.json"))
