$ErrorActionPreference = "Stop"

Set-Location "C:\MinorProject\backend"
python manage.py makemigrations --check --dry-run
python manage.py check
python manage.py test core

$env:Path = "C:\Program Files\nodejs;$env:Path"
Set-Location "C:\MinorProject\frontend"
npm run build
