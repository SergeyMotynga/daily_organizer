$ErrorActionPreference = "Stop"

$databaseName = "daily_organizer_test"
$containerName = "daily_organizer_postgres"

$existsOutput = @(
    docker exec $containerName psql `
    -U daily_organizer `
    -d postgres `
    -tAc "SELECT 1 FROM pg_database WHERE datname = '$databaseName'"
)

if ($LASTEXITCODE -ne 0) {
    throw "Failed to check whether database '$databaseName' exists."
}

$exists = ($existsOutput -join "").Trim()
if ($exists -eq "1") {
    Write-Host "Database '$databaseName' already exists."
    exit 0
}

docker exec $containerName createdb -U daily_organizer $databaseName
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create database '$databaseName'."
}

Write-Host "Database '$databaseName' created."
