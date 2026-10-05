#!/bin/sh
cd "$(dirname "$0")"
echo 'Bu admin parolini "admin" ga qaytaradi. Boshqa hech narsaga tegmaydi.'
printf "Davom etasizmi? (h/y): "
read javob
case "$javob" in
  h|H|y|Y) ;;
  *) echo "Bekor qilindi."; exit 0 ;;
esac
if [ ! -d venv ]; then
  echo "Xato: avval dasturni kamida bir marta ./ishga_tushirish.sh bilan ishga tushiring."
  exit 1
fi
. venv/bin/activate
python3 -c "import sqlite3; c=sqlite3.connect('savol_javob_v3.db'); c.execute(\"DELETE FROM settings WHERE key='admin_password'\"); c.commit(); print('Parol tiklandi.')"
echo "Endi dasturni ./ishga_tushirish.sh bilan qayta ishga tushiring va /admin ga parol \"admin\" bilan kiring."
