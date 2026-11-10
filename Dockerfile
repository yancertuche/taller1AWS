FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/tmp \
    XDG_CACHE_HOME=/tmp/.cache

WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app

# Capa de dependencias reutilizable; nunca copiamos credenciales ni el repositorio entero.
COPY requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock

COPY --chown=app:app app.py read_value_yf.py gunicorn.conf.py ./
COPY --chown=app:app templates/ ./templates/

USER 10001:10001
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
