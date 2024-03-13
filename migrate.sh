#!/bin/sh
echo "Run database migrations if any."
poetry run alembic upgrade head 2>&1
echo "Migration complete."
