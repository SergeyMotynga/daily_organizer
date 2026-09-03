#!/usr/bin/env bash
set -euo pipefail

database_name="daily_organizer_test"
container_name="daily_organizer_postgres"

exists="$(
  docker exec "$container_name" psql \
    -U daily_organizer \
    -d postgres \
    -tAc "SELECT 1 FROM pg_database WHERE datname = '$database_name'"
)"

if [[ "$exists" == "1" ]]; then
  echo "Database '$database_name' already exists."
  exit 0
fi

docker exec "$container_name" createdb -U daily_organizer "$database_name"
echo "Database '$database_name' created."
