@echo off
echo Запуск тестов в %date% %time%
echo.

REM
python -m pytest test_main.py --cov=main -v

REM
if %errorlevel% equ 0 (
    echo Все тесты прошли успешно!
) else (
    echo Обнаружены failed тесты!
)

echo.
pause