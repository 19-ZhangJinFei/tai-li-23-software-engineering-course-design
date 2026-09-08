FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml requirements.txt ./
RUN mkdir app && touch app/__init__.py && pip install --no-cache-dir . && rm -rf app
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
COPY main.py ./main.py
RUN pip install --no-cache-dir --no-deps .
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
