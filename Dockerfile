FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY corpus ./corpus
RUN pip install --no-cache-dir . \
    && mkdir -p /data

ENV PYTHONUNBUFFERED=1 \
    Q2PY_CORPUS=/app/corpus/cases.json \
    Q2PY_DB=/data/q2py.sqlite
EXPOSE 43118
VOLUME /data
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:43118/api/v1/health')"
CMD ["uvicorn", "q2py.api:app", "--host", "0.0.0.0", "--port", "43118"]
