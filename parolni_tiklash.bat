@echo off
chcp 65001 >nul
echo Bu admin parolini "admin" ga qaytaradi. Boshqa hech narsaga (ishtirokchilar, hakamlar, savollar, natijalar) tegmaydi.
echo.
set /p javob="Davom etasizmi? (h/y): "
if /I not "%javob%"=="h" (echo Bekor qilindi. & pause & exit /b)
if not exist venv (
  echo Xato: avval dasturni kamida bir marta ishga_tushirish.bat bilan ishga tushiring.
  pause
  exit /b
)
call venv\Scripts\activate
python -c "import sqlite3; c=sqlite3.connect('savol_javob_v3.db'); c.execute(\"DELETE FROM settings WHERE key='admin_password'\"); c.commit(); print('Parol tiklandi.')"
echo.
echo Endi dasturni ishga_tushirish.bat bilan qayta ishga tushiring va /admin ga parol \"admin\" bilan kiring.
pause
