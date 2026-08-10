Write-Host "Starting Discord Gaming Tracker development environment..."

# --------------------------------------------------
# Virtual environment
# --------------------------------------------------

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

Write-Host "Activating virtual environment..."

& ".\.venv\Scripts\Activate.ps1"


# --------------------------------------------------
# Dependencies
# --------------------------------------------------

Write-Host "Installing dependencies..."

python -m pip install -r requirements.txt


# --------------------------------------------------
# PostgreSQL
# --------------------------------------------------

Write-Host "Starting PostgreSQL..."

docker compose up -d postgres

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start PostgreSQL."
    exit 1
}


# --------------------------------------------------
# Wait for PostgreSQL
# --------------------------------------------------

Write-Host "Waiting for PostgreSQL..."

$maxAttempts = 30
$attempt = 0

do {
    $attempt++

    docker exec discord-bot-postgres `
        pg_isready `
        -U discordbot `
        -d discordbot `
        *> $null

    if ($LASTEXITCODE -eq 0) {
        break
    }

    Start-Sleep -Seconds 1

} while ($attempt -lt $maxAttempts)


if ($attempt -ge $maxAttempts) {
    Write-Host "PostgreSQL did not become ready."
    exit 1
}

Write-Host "PostgreSQL is ready."


# --------------------------------------------------
# Migrations
# --------------------------------------------------

Write-Host "Running database migrations..."

python -m alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host "Migration failed."
    exit 1
}


# --------------------------------------------------
# Discord Bot
# --------------------------------------------------

Write-Host "Starting Discord bot..."

python bot.py