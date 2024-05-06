@echo off

:: Set the name of your project

:: Create a new Python virtual environment in the venv folder
python -m venv venv

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Install required libraries (replace with your own list of libraries)
pip install winshell pyside6 pywin32 psutil pyinstaller

:: Deactivate the virtual environment
deactivate

pause
:: End of script