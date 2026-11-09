FROM python:3.11.14-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/opt/project/src \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
    LANGCHAIN_TRACING_V2=false
WORKDIR /opt/project
COPY requirements/ml.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --requirement /tmp/requirements.txt "pytest==8.4.2" && pip check \
    && useradd --create-home --uid 10001 student
COPY --chown=student:student src/ src/
COPY --chown=student:student agents/ agents/
COPY --chown=student:student dashboard/ dashboard/
COPY --chown=student:student tests/ml/ tests/ml/
COPY --chown=student:student pytest.ini pytest.ini
USER student
CMD ["python", "-m", "streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--browser.gatherUsageStats=false"]
