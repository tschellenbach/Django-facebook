

@echo off
set VIRTUAL_ENV=c:\workspace\django_facebook\docs\docs_env

if not defined PROMPT (
    set PROMPT=$P$G
)

if defined _OLD_VIRTUAL_PROMPT (
    set PROMPT=%_OLD_VIRTUAL_PROMPT%
)

if defined _OLD_VIRTUAL_PYTHONHOME (
     set PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%
)

set _OLD_VIRTUAL_PROMPT=%PROMPT%
set PROMPT=(docs_env) %PROMPT%

if defined PYTHONHOME (
     set _OLD_VIRTUAL_PYTHONHOME=%PYTHONHOME%
     set PYTHONHOME=
)

if defined _OLD_VIRTUAL_PATH set PATH=%_OLD_VIRTUAL_PATH%; goto SKIPPATH

set _OLD_VIRTUAL_PATH=%PATH%


REM custom venv settings
set PYTHONPATH=%\VIRTUAL_ENV%;%\VIRTUAL_ENV%\conf;%\VIRTUAL_ENV%\apps
set DJANGO_SETTINGS_MODULE=settings

ftype Python.File=%VIRTUAL_ENV%\Scripts\python.exe %1 %*

:SKIPPATH
set PATH=%VIRTUAL_ENV%\Scripts;%PATH%
:END
