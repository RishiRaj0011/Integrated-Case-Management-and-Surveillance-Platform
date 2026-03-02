@echo off
REM Celery Worker Startup Script
REM Max 4 concurrent workers for memory management

echo Starting Celery worker with 4 concurrent tasks...
echo Memory threshold: 80%%
echo.

celery -A celery_app worker --loglevel=info --concurrency=4 --max-tasks-per-child=10 --max-memory-per-child=2000000

pause
