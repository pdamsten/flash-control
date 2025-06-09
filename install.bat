@echo off
set SCRIPT_NAME=voting_gui.py
set SHORTCUT_NAME=KKS Äänestys
set ICON_PATH=voting.ico

:: Install dependencies
::python -m pip install -r dependencies-win.txt

setlocal
set "BASEDIR=%~dp0"
if "%BASEDIR:~-1%"=="\" set "BASEDIR=%BASEDIR:~0,-1%"
set "BATFILE=%BASEDIR%\voting_gui.bat"
set "ICONFILE=%BASEDIR%\voting.ico"
set "SHORTCUT_NAME=Aanestyksen hallinta"
cscript //nologo "%BASEDIR%\create_shortcut.vbs" "%BATFILE%" "%ICONFILE%" "%SHORTCUT_NAME%"
endlocal

echo Shortcut created on your Desktop!

pause