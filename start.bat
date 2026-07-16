@echo off
cd /d D:\AI projects\links\Mimo-projects\xsmb-analysis
call .venv\Scripts\activate.bat

echo ============================
echo XSMN Update Tool
echo ============================
echo 1. Cap nhat binh thuong
echo 2. Cap nhat tu ngay cu the
echo 3. Xoa du lieu cu va cap nhat lai
echo ============================
set /p choice="Chon (1/2/3): "

if "%choice%"=="1" (
    python src/update_xsmn.py
) else if "%choice%"=="2" (
    set /p fromdate="Nhap ngay (YYYY-MM-DD): "
    python src/update_xsmn.py --from-date %fromdate%
) else if "%choice%"=="3" (
    python src/update_xsmn.py --refetch --from-date 2025-01-01
) else (
    echo Lua chon khong hop le
)

if %errorlevel% equ 0 (
    echo.
    echo Open readme.html in browser
    start readme.html
)
pause
