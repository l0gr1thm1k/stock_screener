FROM python:3

WORKDIR /app

# Prevent Spacy from using all available cores
ENV OPENBLAS_NUM_THREADS=1

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/

EXPOSE 8000

CMD gunicorn -c gunicorn_config.py application
