Write-Host "===================================================================" -ForegroundColor Green
Write-Host "  Groundfall - The Offline Field Naturalist & Sensory Walk Companion" -ForegroundColor Green
Write-Host "  Built for Hacktoberfest Week 1: Touch Grass (#hf26challenge)" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Green
Write-Host "Starting server at http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Start-Process "http://127.0.0.1:8000"
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
