FROM python:3.12-slim

# ---- ENV ----
ENV HOME=/home/fast \
    APP_HOME=/home/fast/app \
    PYTHONPATH="/home/fast" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---- Create user ----
RUN addgroup --system fast && \
    adduser --system --ingroup fast fast

# ---- Create app directory ----
RUN mkdir -p $APP_HOME

WORKDIR $HOME

# ---- Copy project ----
COPY app app
COPY scripts scripts
COPY main.py requirements.txt alembic.ini .env ./

# ---- Install dependencies ----
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    chown -R fast:fast $HOME

# ---- Switch user ----
USER fast

EXPOSE 8000
