#!/bin/bash
# Docker entrypoint script for Xcapit FHE-ML Platform
# Django 5.2 LTS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Xcapit FHE-ML Platform ===${NC}"
echo -e "${YELLOW}Django 5.2 LTS${NC}"
echo ""

# Wait for database to be ready
if [ -n "$DATABASE_URL" ]; then
    echo -e "${YELLOW}Waiting for database...${NC}"

    # Extract host and port from DATABASE_URL
    # Format: postgresql://user:pass@host:port/dbname
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

    if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
        MAX_RETRIES=30
        RETRY_COUNT=0

        while ! nc -z $DB_HOST $DB_PORT; do
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
                echo -e "${RED}Failed to connect to database after $MAX_RETRIES attempts${NC}"
                exit 1
            fi
            echo "Database not ready, waiting... ($RETRY_COUNT/$MAX_RETRIES)"
            sleep 2
        done

        echo -e "${GREEN}Database is ready!${NC}"
    fi
fi

# Run migrations if enabled
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo -e "${YELLOW}Running database migrations...${NC}"
    python manage.py migrate --noinput
    echo -e "${GREEN}Migrations complete!${NC}"
fi

# Collect static files if in production
if [ "${DJANGO_DEBUG:-False}" = "False" ]; then
    echo -e "${YELLOW}Collecting static files...${NC}"
    python manage.py collectstatic --noinput
    echo -e "${GREEN}Static files collected!${NC}"
fi

# Create superuser if credentials are provided (for initial setup)
# SECURITY: Using heredoc with single quotes to prevent shell injection
# Variables are read via os.environ inside Python, not interpolated by shell
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo -e "${YELLOW}Creating superuser if not exists...${NC}"
    python manage.py shell << 'PYTHON_EOF'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')

if email and password:
    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(email=email, password=password)
        print('Superuser created!')
    else:
        print('Superuser already exists.')
else:
    print('Email or password not provided.')
PYTHON_EOF
    if [ $? -ne 0 ]; then
        echo "Superuser creation skipped"
    fi
fi

echo ""
echo -e "${GREEN}Starting application...${NC}"

# Execute the main command
exec "$@"
