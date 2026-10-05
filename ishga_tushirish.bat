@echo off
chcp 65001 >nul
setlocal

rem "python" ba'zi Windows kompyuterlarda Microsoft Store bilan bog'langan soxta
rem yorliqqa ulanib qoladi. Shuning uchun haqiqiy Python borligini --version
rem chiqishiga qarab tekshiramiz, shunchaki mavjudligiga emas.
set "PY="
python --version 2>&1 | findstr /b /r "Python [0-9]" >nul
if not errorlevel 1 set "PY=python"
if not defined PY (
  py --version 2>&1 | findstr /b /r "Python [0-9]" >nul
  if not errorlevel 1 set "PY=py"
)

if not defined PY (
  echo Python topilmadi yoki noto'g'ri ishlayapti.
  echo.
  echo Bu ko'pincha Windows'ning "python" buyrug'ini Microsoft Store bilan
  echo bog'lab qo'yishi sababli bo'ladi. Tuzatish uchun:
  echo   1^) Windows qidiruvidan "App execution aliases" ^(yoki "Ilova ijro
  echo      etish taxalluslari"^) ni oching.
  echo   2^) "python.exe" va "python3.exe" qatoridagi tugmachalarni O'CHIRING.
  echo   3^) Shu faylni qayta ishga tushiring.
  echo.
  echo Agar bu yordam bermasa, python.org saytidan Python'ni rasman
  echo o'rnating ^("Add python.exe to PATH" katagini belgilab^).
  pause
  exit /b
)

rem Oldingi muvaffaqiyatsiz urinishdan chala/buzilgan venv qolgan bo'lsa, qayta yaratamiz.
if exist venv (
  if not exist venv\Scripts\activate.bat (
    rmdir /s /q venv
  )
)
if not exist venv (%PY% -m venv venv)
call venv\Scripts\activate
pip install -r requirements.txt -q
rem Admin parolini o'zgartiring:
set ADMIN_PASSWORD=admin
python dastur.py
pause
