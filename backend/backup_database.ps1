$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDirectory = "C:\MinorProject\backups"
New-Item -ItemType Directory -Force -Path $backupDirectory | Out-Null

if (-not $env:POSTGRES_DB) {
    Write-Warning "POSTGRES_DB is not configured. SQLite backup can be used instead."
    Copy-Item "C:\MinorProject\backend\db.sqlite3" "$backupDirectory\db-$timestamp.sqlite3"
    return
}

$file = "$backupDirectory\postgres-$timestamp.dump"
pg_dump -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d $env:POSTGRES_DB -Fc -f $file
Write-Host "Database backup created: $file"
