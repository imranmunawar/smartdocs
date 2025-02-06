#!/bin/bash
echo "Database host: $DATABASE_HOST"

# Wait until MySQL is ready
while ! mysqladmin ping -h"$DATABASE_HOST" --silent; do
    echo "Waiting for MySQL to start..."
    sleep 1
done

echo "MySQL Database started"
exec "$@"