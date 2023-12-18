FROM python:3.11-slim-bookworm

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=0 \
    POETRY_VERSION=1.7.1

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock /app/
WORKDIR /app

RUN poetry install --no-root --without dev

COPY . .
CMD ["poetry", "run", "python3", "main.py"]
