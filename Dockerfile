FROM python:3.10
ENV PYTHONUNBUFFERED 1
WORKDIR /app


RUN apt-get update && \
    apt-get install -y libreoffice

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -U pip setuptools wheel && pip install --no-cache-dir launchflow[gcp] django

RUN pip install -r requirements.txt
COPY . /app
# Add a custom script to wait for the database
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Expose the port for the Django development server
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]