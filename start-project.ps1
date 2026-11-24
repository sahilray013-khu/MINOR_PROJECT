$ErrorActionPreference = "Stop"

$node = "C:\Program Files\nodejs"
$env:Path = "$node;$env:Path"

Write-Host "Starting Django backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'C:\MinorProject\backend'; python manage.py runserver 127.0.0.1:8000"

Write-Host "Starting React frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'C:\MinorProject\frontend'; `$env:Path='$node;' + `$env:Path; npm run dev -- --host 127.0.0.1"

Start-Sleep -Seconds 3
Start-Process "http://127.0.0.1:5173/login"
