@echo off
chcp 65001 >nul
setlocal

echo   Bu skript "Savol javob.exe" nomli, Python kerak bo'lmaydigan doimiy
echo   dastur yasaydi. Bir necha daqiqa vaqt oladi.
echo.

set "PY="
python --version 2>&1 | findstr /b /r "Python [0-9]" >nul
if not errorlevel 1 set "PY=python"
if not defined PY (
  py --version 2>&1 | findstr /b /r "Python [0-9]" >nul
  if not errorlevel 1 set "PY=py"
)
if not defined PY (
  echo Python topilmadi. Avval ishga_tushirish.bat ni ishga tushirib, Python
  echo to'g'ri ishlayotganiga ishonch hosil qiling, keyin shu faylni qayta
  echo ishga tushiring.
  pause
  exit /b
)

if exist venv (
  if not exist venv\Scripts\activate.bat rmdir /s /q venv
)
if not exist venv (%PY% -m venv venv)
call venv\Scripts\activate
pip install -r requirements.txt pyinstaller -q

echo.
echo   .exe fayl yig'ilmoqda...
echo.

pyinstaller --noconfirm --onefile --name "Savol javob" ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  --hidden-import webview.platforms.edgechromium ^
  --hidden-import webview.platforms.winforms ^
  --hidden-import webview.platforms.mshtml ^
  dastur.py

if exist "dist\Savol javob.exe" (
  copy /y "dist\Savol javob.exe" "Savol javob.exe" >nul
  echo.
  echo ==================================================================
  echo   Tayyor! "Savol javob.exe" shu papkada paydo bo'ldi.
  echo   Endi shu bitta faylni istalgan Windows kompyuterga nusxalab,
  echo   ikki marta bosib ishlatishingiz mumkin - u yerda Python
  echo   o'rnatilgan bo'lishi shart emas.
  echo ==================================================================
) else (
  echo.
  echo Xatolik yuz berdi, .exe yaratilmadi. Yuqoridagi xabarlarni menga
  echo yuboring - shunga qarab tuzataman.
)
echo.
pause
