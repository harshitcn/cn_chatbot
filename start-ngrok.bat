@echo off
REM Batch script to start FastAPI app with ngrok
echo Starting CN Chatbot with ngrok...

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=py
    ) else (
        echo Error: Python not found. Please install Python 3.11 or higher.
        pause
        exit /b 1
    )
)

echo Using Python: %PYTHON_CMD%

REM Check for virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Creating one...
    %PYTHON_CMD% -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    %PYTHON_CMD% -m pip install --upgrade pip
    %PYTHON_CMD% -m pip install -r requirements.txt
)

REM Check for ngrok
where ngrok >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ngrok not found. Please install ngrok:
    echo 1. Download from: https://ngrok.com/download
    echo 2. Or install via winget: winget install ngrok
    echo 3. Or install via chocolatey: choco install ngrok
    echo.
    echo Starting FastAPI without ngrok...
    echo FastAPI will be available at: http://localhost:8000
    echo API docs at: http://localhost:8000/docs
    echo.
    set APP_ENV=stage
    %PYTHON_CMD% -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    pause
    exit /b 0
)

REM Set environment variables
set APP_ENV=stage
set PYTHONUNBUFFERED=1
set PORT=8000

echo.
echo Starting FastAPI server on port %PORT%...
echo Starting ngrok tunnel...
echo.

REM Start FastAPI in a new window
start "FastAPI Server" cmd /k "%PYTHON_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port %PORT%"

REM Wait for FastAPI to start
timeout /t 3 /nobreak >nul

echo FastAPI is starting...
echo ngrok tunnel will be available shortly...
echo.
echo Local URL: http://localhost:%PORT%
echo API Docs: http://localhost:%PORT%/docs
echo.

REM Start ngrok
ngrok http %PORT%

pause

