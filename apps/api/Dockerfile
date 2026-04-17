FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Keep the repo-like depth so config/settings.py can still resolve ../../.. /.env.
WORKDIR /workspace/apps/api

COPY . /workspace/apps/api

RUN python -m pip install --upgrade pip \
    && python -m pip install . "uvicorn[standard]>=0.30,<0.31"

EXPOSE 8000

CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
