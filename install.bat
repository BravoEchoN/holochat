@echo off

rem Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Installing Python...
    
    rem Download and install the latest version of Python (adjust URL as needed)
    curl -o python_installer.exe https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    
    rem Check if Python installation was successful
    python --version > nul 2>&1
    if %errorlevel% neq 0 (
        echo Python installation failed! Please install Python manually and rerun the script.
        pause
        exit /b %errorlevel%
    ) else (
        echo Python installed successfully!
    )
)

rem Install OpenAI package
echo Installing OpenAI package...
python -m pip install openai

rem Check if installation of OpenAI was successful
if %errorlevel% neq 0 (
    echo Installation of OpenAI package failed! Please check your Python and pip installation.
    pause
    exit /b %errorlevel%
)

rem Install Cryptography package
echo Installing cryptography package...
python -m pip install cryptography

rem Check if installation of Cryptography was successful
if %errorlevel% neq 0 (
    echo Installation of cryptography package failed! Please check your Python and pip installation.
    pause
    exit /b %errorlevel%
)

rem Install APSW package
echo Installing APSW package...
python -m pip install apsw

rem Check if installation of APSW was successful
if %errorlevel% neq 0 (
    echo Installation of APSW package failed! Please check your Python and pip installation.
    pause
    exit /b %errorlevel%
)

rem Install Gensim package
echo Installing Gensim package...
python -m pip install gensim

rem Check if installation of Gensim was successful
if %errorlevel% neq 0 (
    echo Installation of Gensim package failed! Please check your Python and pip installation.
    pause
    exit /b %errorlevel%
)

rem Run encrypts.py script
echo Running encrypts.py...
call python encrypts.py

rem Run holochat.py script
echo Running holochat.py...
call python holochat.py

pause
