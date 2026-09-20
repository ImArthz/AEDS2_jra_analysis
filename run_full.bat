@echo off
echo Iniciando Coleta JRA 2002-2025 e JBIS Pedigree...
echo =================================================
cd /d "%~dp0src"
python run_pipeline.py --start-year 2002 --end-year 2025 --analyze
pause
