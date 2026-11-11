# compilar.ps1
Write-Host "1. Cerrando instancias previas..." -ForegroundColor Cyan
Stop-Process -Name "GestionCMF" -Force -ErrorAction SilentlyContinue

Write-Host "2. Actualizando estaticos..." -ForegroundColor Cyan
python manage.py collectstatic --noinput --clear

Write-Host "3. Limpiando build previo y cache de Python..." -ForegroundColor Cyan
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "4. Compilando usando GestionCMF.spec..." -ForegroundColor Cyan
pyinstaller GestionCMF.spec

Write-Host "¡Listo! Compilación finalizada." -ForegroundColor Green