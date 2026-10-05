"""PyInstaller bilan yagona .exe qilib yig'ilganda ham, oddiy Python skripti
sifatida ishlaganda ham to'g'ri papkalarni topish uchun yordamchi."""
import os
import sys


def base_dir():
    """Ma'lumotlar (baza, natijalar, sozlamalar) saqlanadigan papka — doim
    .exe yoki app.py fayli turgan joy, hech qachon vaqtinchalik papka emas."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_dir():
    """Dastur bilan birga keladigan fayllar (shablonlar, shriftlar) papkasi.
    .exe ichida bular PyInstaller tomonidan vaqtinchalik papkaga ochiladi."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", base_dir())
    return os.path.dirname(os.path.abspath(__file__))
