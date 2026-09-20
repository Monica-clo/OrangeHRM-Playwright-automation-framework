@echo off
REM Usage: run_tests.bat [workflow^|positive^|negative^|smoke^|regression^|perf] [extra options]
REM   run_tests.bat                     -> all 5 E2E workflows
REM   run_tests.bat negative            -> the negative workflow only
REM   run_tests.bat positive --headed   -> the 4 positive workflows with a visible browser
REM   run_tests.bat perf                -> k6 performance test (login + employee creation API)
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
set SUITE=%1
if "%SUITE%"=="perf" goto perf
if "%SUITE%"=="workflow" goto marker
if "%SUITE%"=="positive" goto marker
if "%SUITE%"=="negative" goto marker
if "%SUITE%"=="smoke" goto marker
if "%SUITE%"=="regression" goto marker
python -m pytest -m workflow %*
goto end
:marker
shift
python -m pytest -m %SUITE% %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end
:perf
shift
if not exist reports\performance mkdir reports\performance
k6 run %1 %2 %3 %4 %5 %6 %7 %8 %9 performance\k6\api-performance.js
:end
