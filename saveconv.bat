@echo off
rem Double-click: opens the converter window.
rem Drag save files onto this file: converts them to .mcd next to each source.
python "%~dp0saveconv.py" %*
if not "%~1"=="" pause
