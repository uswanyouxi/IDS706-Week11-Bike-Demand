# Classroom reference and data attribution

Original classroom material: [Kedar-V/automl-research-lab](https://github.com/Kedar-V/automl-research-lab/tree/a294145ea9aa4225908ce701c06160c33213335d), commit a294145ea9aa4225908ce701c06160c33213335d. The instructor's completed Airflow DAG, LangGraph and runtime helpers are imported unmodified from a checksum-verified ignored cache. They are not presented as student-authored adaptive agents.

The [original dataset attribution](https://github.com/Kedar-V/automl-research-lab/blob/a294145ea9aa4225908ce701c06160c33213335d/datasets/airflow/ATTRIBUTION.md) identifies customers.csv and transactions.csv as synthetic educational extracts from the Financial Transaction Intelligence Dataset 2026, Kaggle slug roshaaann30/financial-transaction-intelligence-dataset-2026, licensed CC BY-NC-SA 4.0. The new merged/subset/publication CSVs retain that provenance.

This directory's driver, isolation checks, evidence observer and read-only viewer are separate reproduction infrastructure. The Bike Demand DAG and adaptive algorithms remain original student implementations.

Airflow's [official Python 3.11 constraint file](https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.11.txt) is vendored with its verified hash in source-pins.json. The native environment uses the instructor's Airflow 2.10.4/Python 3.11 base with explicitly pinned classifier dependencies.
