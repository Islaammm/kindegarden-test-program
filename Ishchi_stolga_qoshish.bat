@echo off
chcp 65001 >nul
setlocal
set "HERE=%~dp0"
set "TARGET=%HERE%ishga_tushirish.bat"
set "DESKTOP=%USERPROFILE%\Desktop"
set "ICON=%HERE%venv\Scripts\python.exe"

if not exist "%TARGET%" (
  echo Xato: ishga_tushirish.bat topilmadi. Bu faylni "savol-javob" papkasidan tashqariga chiqarmang.
  pause
  exit /b
)

powershell -NoProfile -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%DESKTOP%\Savol javob.lnk'); $s.TargetPath='%TARGET%'; $s.WorkingDirectory='%HERE%'; if (Test-Path '%ICON%') { $s.IconLocation='%ICON%' }; $s.Save()"

if exist "%DESKTOP%\Savol javob.lnk" (
  echo.
  echo Tayyor! Ishchi stolingizda "Savol javob" nomli belgicha paydo bo'ldi.
  echo Endi dasturni shu belgichani ikki marta bosib ochishingiz mumkin.
) else (
  echo.
  echo Belgicha yaratilmadi. Ishchi stolga o'zingiz qo'shib ko'ring:
  echo "ishga_tushirish.bat" ustida o'ng tugmani bosing -^> Send to -^> Desktop (create shortcut)
)
echo.
pause
