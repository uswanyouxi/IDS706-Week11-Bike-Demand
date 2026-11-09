Runtime artifacts live in the Docker project-artifacts named volume, not these
host export folders. Part 1 writes /opt/project/artifacts/pipeline/<hashed-run-id>:
per-task attempt audits, source/clean/merge validation reports, a load receipt,
and three DB-fed EDA PNGs plus JSON/text findings.
Use the README's docker compose cp commands to export real runtime outputs into
docs/verification/phase-b. Host tests/file probes are not database/DAG evidence.
