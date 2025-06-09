@echo off

:: Install dependencies
python -m pip install -r dependencies-win.txt

setlocal
set "BASEDIR=%~dp0"
if "%BASEDIR:~-1%"=="\" set "BASEDIR=%BASEDIR:~0,-1%"
set "BATFILE=%BASEDIR%\flash-control.bat"
set "ICONFILE=%BASEDIR%\flash-control.ico"
set "SHORTCUT_NAME=Flash Control"
cscript //nologo "%BASEDIR%\create_shortcut.vbs" "%BATFILE%" "%ICONFILE%" "%SHORTCUT_NAME%"
endlocal

echo Shortcut created on your Desktop!

pause