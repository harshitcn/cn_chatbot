# PowerShell script to start FastAPI app with ngrok
# This script starts the FastAPI application and ngrok tunnel

Write-Host "Starting CN Chatbot with ngrok..." -ForegroundColor Green

# Check if Python is available
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} else {
    Write-Host "Error: Python not found. Please install Python 3.11 or higher." -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $pythonCmd" -ForegroundColor Yellow

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
} elseif (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & ".venv\Scripts\Activate.ps1"
} else {
    Write-Host "No virtual environment found. Creating one..." -ForegroundColor Yellow
    & $pythonCmd -m venv venv
    & "venv\Scripts\Activate.ps1"
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    & $pythonCmd -m pip install --upgrade pip
    & $pythonCmd -m pip install -r requirements.txt
}

# Check if ngrok is installed
$ngrokPath = $null
if (Get-Command ngrok -ErrorAction SilentlyContinue) {
    $ngrokPath = "ngrok"
} elseif (Test-Path "$env:LOCALAPPDATA\Microsoft\WindowsApps\ngrok.exe") {
    $ngrokPath = "$env:LOCALAPPDATA\Microsoft\WindowsApps\ngrok.exe"
} elseif (Test-Path "C:\Program Files\ngrok\ngrok.exe") {
    $ngrokPath = "C:\Program Files\ngrok\ngrok.exe"
} else {
    Write-Host "ngrok not found. Please install ngrok:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://ngrok.com/download" -ForegroundColor Cyan
    Write-Host "2. Or install via winget: winget install ngrok" -ForegroundColor Cyan
    Write-Host "3. Or install via chocolatey: choco install ngrok" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Starting FastAPI without ngrok..." -ForegroundColor Yellow
    Write-Host "FastAPI will be available at: http://localhost:8000" -ForegroundColor Green
    Write-Host "API docs at: http://localhost:8000/docs" -ForegroundColor Green
    $env:APP_ENV = "stage"
    & $pythonCmd -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    exit 0
}

# Set environment variables
$env:APP_ENV = "stage"
$env:PYTHONUNBUFFERED = "1"

# Port for FastAPI
$port = 8000

Write-Host "Starting FastAPI server on port $port..." -ForegroundColor Yellow
Write-Host "Starting ngrok tunnel..." -ForegroundColor Yellow
Write-Host ""

# Start FastAPI in background
$fastapiJob = Start-Job -ScriptBlock {
    param($pythonCmd, $port)
    Set-Location $using:PWD
    $env:APP_ENV = "stage"
    $env:PYTHONUNBUFFERED = "1"
    & $pythonCmd -m uvicorn app.main:app --host 0.0.0.0 --port $port
} -ArgumentList $pythonCmd, $port

# Wait a moment for FastAPI to start
Start-Sleep -Seconds 3

# Start ngrok
Write-Host "FastAPI is starting..." -ForegroundColor Green
Write-Host "ngrok tunnel will be available shortly..." -ForegroundColor Green
Write-Host ""
Write-Host "Local URL: http://localhost:$port" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:$port/docs" -ForegroundColor Cyan
Write-Host ""

# Start ngrok
& $ngrokPath http $port

# Cleanup on exit
Write-Host "Stopping services..." -ForegroundColor Yellow
Stop-Job $fastapiJob
Remove-Job $fastapiJob

