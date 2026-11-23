FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

LABEL org.opencontainers.image.title="Starlink Physical Atlas" \
      org.opencontainers.image.description="Reproducible physical atlas of the Starlink constellation" \
      org.opencontainers.image.source="https://github.com/M0-AR/starlink-physical-atlas" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends make \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip install --no-cache-dir -e .

COPY . .

CMD ["bash", "-lc", "make reproduce && make test"]
