FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY corpus ./corpus
RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
EXPOSE 43118
CMD ["uvicorn", "q2py.api:app", "--host", "0.0.0.0", "--port", "43118"]
