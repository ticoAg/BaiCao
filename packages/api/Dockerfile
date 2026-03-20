FROM python:3.12-slim

WORKDIR /app

# Configure Aliyun mirror and install uv
RUN pip install --no-cache-dir uv && \
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# Install all dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy pydantic pydantic-settings \
    alembic asyncpg psycopg2-binary neo4j langchain langchain-openai python-dotenv

# Copy application source
COPY app/ ./app/

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
