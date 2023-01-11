#!/bin/bash

current_date_time="$(date +%Y-%m-%d_%H%M%S)";
log_path="logs/$current_date_time.log";

echo "docker compose restart with log: $log_path";

docker compose down && \
docker compose up --build -d & \
docker compose logs -f app >> "$log_path";
