"""Savol javob — kompyuterda o'rnatilgan dastur sifatida ochish.

Bu skript Flask serverni orqa fonda ishga tushiradi va uni alohida dastur
oynasida ko'rsatadi (brauzer manzil satri, yorliqlari ko'rinmaydi).

Boshqa kompyuterlar (hakamlar, ishtirokchi) hamon o'z brauzerida manzilni
ochib ulanadi — ko'p kompyuterda ishlashi uchun bu zarur. Faqat shu
kompyuterning o'zida ochiladigan oyna endi oddiy dastur kabi ko'rinadi.

Agar "pywebview" o'rnatilmagan yoki bu kompyuterda ishlamasa (masalan juda
eski Windows), dastur avtomatik oddiy brauzer rejimiga o'tadi — hech narsa
buzilmaydi, faqat brauzer tabida ochiladi.
"""
import os
import socket
import threading
import time

PORT = int(os.environ.get("PORT", 8000))


def _wait_ready(port, tries=50):
    for _ in range(tries):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def _local_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "127.0.0.1"


def run_server():
    from app import app as flask_app
    flask_app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True, use_reloader=False)


def main():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    _wait_ready(PORT)
    print(f"\n  Savol javob ishga tushdi.\n"
          f"  Shu kompyuterda:   http://127.0.0.1:{PORT}\n"
          f"  Boshqalar uchun:   http://{_local_ip()}:{PORT}\n  Admin:  /admin\n")

    try:
        import webview
    except ImportError:
        print('  Eslatma: "pywebview" topilmadi, shuning uchun oddiy brauzerda ochiladi.\n'
              "  Dastur kabi oynada ochish uchun: pip install pywebview\n")
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{PORT}")
        print("  Dasturni to'xtatish uchun shu oynani yoping yoki Ctrl+C bosing.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return

    try:
        webview.create_window("Savol javob", f"http://127.0.0.1:{PORT}",
                              width=1180, height=800, min_size=(820, 560))
        webview.start()
    except Exception as e:
        print(f"  Dastur oynasini ochib bo'lmadi ({e}). Brauzerda ochiladi.\n")
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{PORT}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
