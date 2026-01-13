@echo off
REM Build Forge for Windows
REM Creates a portable folder that can be zipped and distributed

setlocal enabledelayedexpansion

set APP_NAME=Forge
set VERSION=1.0.0
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set DIST_DIR=%PROJECT_DIR%\dist\%APP_NAME%-Windows

echo.
echo  🔥 Building Forge for Windows v%VERSION%
echo.

REM Clean previous build
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
mkdir "%DIST_DIR%"
mkdir "%DIST_DIR%\forge"

REM Copy application files
echo Copying application files...
copy "%PROJECT_DIR%\forge_nicegui.py" "%DIST_DIR%\forge\"
copy "%PROJECT_DIR%\forge_backend.py" "%DIST_DIR%\forge\"
copy "%PROJECT_DIR%\forge_progress.py" "%DIST_DIR%\forge\" 2>nul
copy "%PROJECT_DIR%\requirements.txt" "%DIST_DIR%\forge\"
copy "%PROJECT_DIR%\forge_config.example.json" "%DIST_DIR%\forge\"
xcopy /E /I "%PROJECT_DIR%\workflows" "%DIST_DIR%\forge\workflows" 2>nul
xcopy /E /I "%PROJECT_DIR%\voices" "%DIST_DIR%\forge\voices" 2>nul
xcopy /E /I "%PROJECT_DIR%\docs" "%DIST_DIR%\forge\docs" 2>nul

REM Create launcher batch file
echo Creating launcher...
(
echo @echo off
echo setlocal
echo.
echo set FORGE_DIR=%%~dp0forge
echo set VENV_DIR=%%~dp0venv
echo set CONFIG_DIR=%%USERPROFILE%%\.config\forge
echo.
echo REM Check for Python
echo where python ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     echo Python is required but not installed.
echo     echo Please download Python from https://python.org
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Create config directory
echo if not exist "%%CONFIG_DIR%%" mkdir "%%CONFIG_DIR%%"
echo.
echo REM Create virtual environment if needed
echo if not exist "%%VENV_DIR%%\Scripts\activate.bat" ^(
echo     echo Setting up Forge for first use...
echo     python -m venv "%%VENV_DIR%%"
echo     call "%%VENV_DIR%%\Scripts\activate.bat"
echo     pip install --upgrade pip
echo     pip install -r "%%FORGE_DIR%%\requirements.txt"
echo ^)
echo.
echo call "%%VENV_DIR%%\Scripts\activate.bat"
echo.
echo REM Copy config if needed
echo if not exist "%%CONFIG_DIR%%\forge_config.json" ^(
echo     copy "%%FORGE_DIR%%\forge_config.example.json" "%%CONFIG_DIR%%\forge_config.json"
echo ^)
echo.
echo REM Check if ComfyUI is running
echo curl -s --connect-timeout 2 http://127.0.0.1:8188 ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     echo.
echo     echo ⚠️  ComfyUI is not running!
echo     echo.
echo     echo Please start ComfyUI first:
echo     echo   1. Open ComfyUI folder
echo     echo   2. Run: python main.py
echo     echo   3. Then run Forge again
echo     echo.
echo     echo Press any key to open ComfyUI download page...
echo     pause ^>nul
echo     start https://github.com/comfyanonymous/ComfyUI
echo     exit /b 1
echo ^)
echo.
echo echo Starting Forge...
echo start http://localhost:7861
echo cd "%%FORGE_DIR%%"
echo python forge_nicegui.py
) > "%DIST_DIR%\Start Forge.bat"

REM Create README
(
echo # Forge for Windows
echo.
echo ## Quick Start
echo.
echo 1. Make sure ComfyUI is installed and running
echo 2. Double-click "Start Forge.bat"
echo 3. Forge opens in your browser at http://localhost:7861
echo.
echo ## Requirements
echo.
echo - Windows 10/11
echo - Python 3.10+ ^(https://python.org^)
echo - ComfyUI ^(https://github.com/comfyanonymous/ComfyUI^)
echo - At least one AI model in ComfyUI/models/checkpoints/
echo.
echo ## First Run
echo.
echo On first run, Forge will:
echo - Create a virtual environment
echo - Install required Python packages
echo - This may take a few minutes
echo.
echo ## Configuration
echo.
echo Config file location: %%USERPROFILE%%\.config\forge\forge_config.json
) > "%DIST_DIR%\README.txt"

echo.
echo ✅ Build complete!
echo.
echo    Location: %DIST_DIR%
echo.
echo To distribute:
echo    1. Zip the %APP_NAME%-Windows folder
echo    2. Share the zip file
echo.
pause
