@echo off
REM Usage: run_tests.bat [suite] [extra pytest options]
REM   run_tests.bat                     -> all suites (API + UI + hybrid)
REM   run_tests.bat api                 -> API tests only
REM   run_tests.bat ui --headed         -> UI tests with a visible browser
REM   run_tests.bat hybrid --headed     -> full lifecycle (UI + API)
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
set SUITE=%1
if "%SUITE%"=="api" goto marker
if "%SUITE%"=="ui" goto marker
if "%SUITE%"=="hybrid" goto marker
python -m pytest %*
goto end
:marker
shift
python -m pytest -m %SUITE% %1 %2 %3 %4 %5 %6 %7 %8 %9
:end
