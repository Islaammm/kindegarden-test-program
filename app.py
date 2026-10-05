"""Savol javob — ishtirokchilarni hakamlar bilan savol-javob qilish va baholash dasturi.

Ishga tushirish:  python app.py
Admin paroli:     dastlab `admin` (Sozlamalar bo'limida o'zgartiriladi)
"""
import io
import json
import os
import random
import re
import secrets
import socket
import threading
import time
from datetime import datetime

from flask import (Flask, Response, abort, flash, g, jsonify, redirect,
                   render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from respath import base_dir, resource_dir

BASE = base_dir()
DB_PATH = os.path.join(BASE, "savol_javob_v3.db")
KEY_PATH = os.path.join(BASE, ".secret_key")
NATIJALAR_DIR = os.path.join(BASE, "natijalar")

# DATABASE_URL berilgan bo'lsa (masalan Supabase/Postgres — bulutga joylashtirilganda),
# shu bazadan foydalaniladi. Bo'lmasa, kompyuterdagi oddiy SQLite fayl ishlatiladi.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool
    # Hakamlar soni cheklanmagan (admin xohlagancha qo'sha oladi), shuning uchun
    # bazaga ulanish fondi ham shunga qarab yetarlicha keng qilib belgilangan —
    # ishtirokchi, admin va o'nlab hakam bir vaqtda, bir-biriga to'sqinlik
    # qilmasdan ishlashi uchun.
    PG_POOL = psycopg2.pool.ThreadedConnectionPool(2, 30, DATABASE_URL)
else:
    import sqlite3

app = Flask(__name__,
            template_folder=os.path.join(resource_dir(), "templates"),
            static_folder=os.path.join(resource_dir(), "static"))

# Kirish (session) kaliti: bulutda FLASK_SECRET_KEY muhit o'zgaruvchisidan olinadi
# (konteyner diski vaqtinchalik bo'lgani uchun — aks holda har deploy'da hamma
# kirishlar bekor bo'lib qolardi). Kompyuterda esa avvalgidek diskdagi fayldan.
_env_secret = os.environ.get("FLASK_SECRET_KEY", "").strip()
if _env_secret:
    app.secret_key = _env_secret
else:
    if not os.path.exists(KEY_PATH):
        with open(KEY_PATH, "w") as f:
            f.write(secrets.token_hex(32))
    app.secret_key = open(KEY_PATH).read().strip()

# Bulutda (Postgres) doim HTTPS orqali ishlaydi — cookie'ni shunga qarab himoyalaymiz.
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=USE_PG,
)

if USE_PG:
    # Railway/Render kabi hostinglar proksi orqali ishlaydi — haqiqiy mijoz IP
    # manzilini (tezlik cheklovi uchun) va https ekanini to'g'ri aniqlash uchun.
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


@app.context_processor
def _inject_use_pg():
    # Shablonlar "Supabase" sinxronlash menyusini ko'rsatish-yo'qligini shundan biladi:
    # dastur allaqachon Postgres'ning o'zida ishlayotgan bo'lsa, bu menyu keraksiz.
    return {"use_pg": USE_PG}

SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS directions(
  id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS questions(
  id INTEGER PRIMARY KEY, direction_id INTEGER, text TEXT NOT NULL, answer TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS judges(
  id INTEGER PRIMARY KEY AUTOINCREMENT, num INTEGER UNIQUE, ism TEXT, familya TEXT,
  tugilgan TEXT, code TEXT UNIQUE, last_seen REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS participants(
  id INTEGER PRIMARY KEY, code TEXT UNIQUE, created_at TEXT,
  direction_id INTEGER, yonalish TEXT, judges TEXT, n_questions INTEGER,
  ism TEXT, familya TEXT, tugilgan TEXT, manzil TEXT,
  registered INTEGER NOT NULL DEFAULT 0, max_score INTEGER DEFAULT 5, synced INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'waiting');
CREATE TABLE IF NOT EXISTS asked(
  id INTEGER PRIMARY KEY, participant_id INTEGER, ord INTEGER, text TEXT, answer TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'waiting');
CREATE TABLE IF NOT EXISTS scores(
  asked_id INTEGER, judge_id INTEGER, ball INTEGER,
  PRIMARY KEY(asked_id, judge_id));
"""

# Postgres (Supabase) uchun — SERIAL o'zi avtomatik raqamlaydi, sozlamalar
# ustunlari boshidanoq kiritilgan (eski bazani "migrate" qilish shart emas).
SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS directions(
  id SERIAL PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS questions(
  id SERIAL PRIMARY KEY, direction_id INTEGER, text TEXT NOT NULL, answer TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS judges(
  id SERIAL PRIMARY KEY, num INTEGER UNIQUE, ism TEXT, familya TEXT,
  tugilgan TEXT, code TEXT UNIQUE, last_seen DOUBLE PRECISION DEFAULT 0);
CREATE TABLE IF NOT EXISTS participants(
  id SERIAL PRIMARY KEY, code TEXT UNIQUE, created_at TEXT,
  direction_id INTEGER, yonalish TEXT, judges TEXT, n_questions INTEGER,
  ism TEXT, familya TEXT, tugilgan TEXT, manzil TEXT,
  registered INTEGER NOT NULL DEFAULT 0, max_score INTEGER DEFAULT 5, synced INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'waiting');
CREATE TABLE IF NOT EXISTS asked(
  id SERIAL PRIMARY KEY, participant_id INTEGER, ord INTEGER, text TEXT, answer TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'waiting');
CREATE TABLE IF NOT EXISTS scores(
  asked_id INTEGER, judge_id INTEGER, ball INTEGER,
  PRIMARY KEY(asked_id, judge_id));
"""
DEFAULTS = {"n_questions": "5", "q_order": "random", "max_score": "5"}
STATUS_UZ = {"issued": "Kod berildi", "waiting": "Navbatda", "open": "Javob bermoqda",
             "finished": "Yakunlandi", "closed": "Yopilgan"}


# ---------- baza ----------

def db():
    if "db" not in g:
        if USE_PG:
            g.db = PG_POOL.getconn()
        else:
            g.db = sqlite3.connect(DB_PATH, timeout=10)
            g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d is not None:
        if USE_PG:
            PG_POOL.putconn(d)
        else:
            d.close()


def _adapt(sql):
    """SQLite'ning ?-o'rin belgilarini Postgres kutgan %s ga o'giradi."""
    return sql.replace("?", "%s") if USE_PG else sql


def q(sql, args=(), one=False):
    conn = db()
    if USE_PG:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(_adapt(sql), args)
        rows = cur.fetchall()
        cur.close()
    else:
        rows = conn.execute(sql, args).fetchall()
    return (rows[0] if rows else None) if one else rows


def run(sql, args=()):
    conn = db()
    if USE_PG:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(_adapt(sql), args)
        conn.commit()
        return cur
    cur = conn.execute(sql, args)
    conn.commit()
    return cur


def insert_returning_id(sql, args=()):
    """INSERT ... RETURNING id turidagi so'rov — yangi yozuv id'sini ikkala
    bazada ham xavfsiz qaytaradi (commit'dan OLDIN o'qiladi)."""
    conn = db()
    if USE_PG:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(_adapt(sql), args)
        row = cur.fetchone()
        conn.commit()
        cur.close()
    else:
        cur = conn.execute(sql, args)
        row = cur.fetchone()
        conn.commit()
    return row["id"]


def get_setting(key):
    r = q("SELECT value FROM settings WHERE key=?", (key,), one=True)
    return r["value"] if r else DEFAULTS.get(key)


def set_setting(key, value):
    if USE_PG:
        run("""INSERT INTO settings(key, value) VALUES(?,?)
               ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value""", (key, str(value)))
    else:
        run("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (key, str(value)))


def new_code():
    while True:
        c = str(secrets.randbelow(900000) + 100000)
        if not q("SELECT 1 FROM judges WHERE code=?", (c,), one=True) and \
           not q("SELECT 1 FROM participants WHERE code=?", (c,), one=True):
            return c


def migrate(con):
    """Eski bazani yangi ustunlar bilan to'ldiradi (ma'lumotlar saqlanadi)."""
    def cols(tbl):
        return {r[1] for r in con.execute(f"PRAGMA table_info({tbl})")}
    if "answer" not in cols("questions"):
        con.execute("ALTER TABLE questions ADD COLUMN answer TEXT DEFAULT ''")
    if "answer" not in cols("asked"):
        con.execute("ALTER TABLE asked ADD COLUMN answer TEXT DEFAULT ''")
    if "max_score" not in cols("participants"):
        con.execute("ALTER TABLE participants ADD COLUMN max_score INTEGER DEFAULT 5")
    if "synced" not in cols("participants"):
        con.execute("ALTER TABLE participants ADD COLUMN synced INTEGER DEFAULT 0")


def max_setting():
    try:
        return max(1, min(10, int(get_setting("max_score"))))
    except (TypeError, ValueError):
        return 5


def init_db():
    if USE_PG:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(SCHEMA_PG)
        conn.commit()
        cur.execute("SELECT 1 FROM settings WHERE key='admin_password'")
        has_pw = cur.fetchone() is not None
        if not has_pw:
            pw = os.environ.get("ADMIN_PASSWORD", "admin")
            cur.execute("INSERT INTO settings VALUES('admin_password',%s)", (generate_password_hash(pw),))
            conn.commit()
        cur.close()
        conn.close()
        return
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.executescript(SCHEMA_SQLITE)
    migrate(con)
    con.commit()
    if not con.execute("SELECT 1 FROM settings WHERE key='admin_password'").fetchone():
        pw = os.environ.get("ADMIN_PASSWORD", "admin")
        con.execute("INSERT INTO settings VALUES('admin_password',?)", (generate_password_hash(pw),))
        con.commit()
    con.close()


# ---------- ishtirokchi va hisob-kitob ----------

def get_part(pid):
    return q("SELECT * FROM participants WHERE id=?", (pid,), one=True)


def cur_part():
    return q("SELECT * FROM participants WHERE status='open' ORDER BY id DESC LIMIT 1", one=True)


def snap(p):
    try:
        return json.loads(p["judges"] or "[]")
    except ValueError:
        return []


def full_name(p):
    return f"{p['ism'] or ''} {p['familya'] or ''}".strip()


def current_asked(pid):
    return q("SELECT * FROM asked WHERE participant_id=? AND status='current'", (pid,), one=True)


def update_finished(pid):
    left = q("SELECT COUNT(*) c FROM asked WHERE participant_id=? AND status!='done'",
             (pid,), one=True)["c"]
    p = get_part(pid)
    if p["status"] == "open" and left == 0:
        run("UPDATE participants SET status='finished' WHERE id=?", (pid,))
        threading.Thread(target=_finish_side_effects, args=(pid,), daemon=True).start()


def _finish_side_effects(pid):
    """PDF saqlash va Supabase'ga yuborish tarmoq/disk ishi bo'lgani uchun orqa fonda ishlaydi —
    hakam yoki ishtirokchining so'rovi shu sabab kutib turmaydi."""
    with app.app_context():
        save_local_files(pid)
        try_sync_result(pid)


def _safe_filename(s):
    return re.sub(r'[<>:"/\\|?*]', "", s).strip() or "ishtirokchi"


def save_local_files(pid):
    """Tugagan suhbat natijasini va umumiy reytingni diskka PDF qilib saqlaydi (qo'shimcha zaxira).
    Diskka yozib bo'lmasa ham (joy yoki ruxsat muammosi) dastur ishlashda davom etadi."""
    try:
        os.makedirs(NATIJALAR_DIR, exist_ok=True)
        from pdf import participant_pdf, rating_pdf
        r = results(pid)
        name = _safe_filename(f"{r['p']['ism']} {r['p']['familya']}")
        with open(os.path.join(NATIJALAR_DIR, f"{pid:04d}-{name}.pdf"), "wb") as f:
            f.write(participant_pdf(r))
        with open(os.path.join(NATIJALAR_DIR, "reyting.pdf"), "wb") as f:
            f.write(rating_pdf(all_results()))
    except Exception:
        pass


def try_sync_result(pid):
    """Supabase sozlangan bo'lsa, natijani yuborishga urinadi. Xato bo'lsa jim o'tkazib yuboradi
    (keyinroq admin panelidan qayta urinish mumkin)."""
    import supa
    if not supa.configured(get_setting):
        return
    try:
        ok, _ = supa.push_result(get_setting, results(pid), get_setting("filial_nomi"))
    except Exception:
        ok = False
    run("UPDATE participants SET synced=? WHERE id=?", (1 if ok else 0, pid))


def close_if_complete(asked_id):
    a = q("SELECT * FROM asked WHERE id=?", (asked_id,), one=True)
    if not a or a["status"] != "current":
        return
    p = get_part(a["participant_id"])
    exist = {r["id"] for r in q("SELECT id FROM judges")}
    need = {j["id"] for j in snap(p) if j["id"] in exist}
    have = {r["judge_id"] for r in q("SELECT judge_id FROM scores WHERE asked_id=?", (asked_id,))}
    if need and need <= have:
        run("UPDATE asked SET status='done' WHERE id=?", (asked_id,))
        update_finished(p["id"])


def recheck_open():
    p = cur_part()
    if p:
        c = current_asked(p["id"])
        if c:
            close_if_complete(c["id"])


def results(pid):
    p = get_part(pid)
    js = snap(p)
    mx = int(p["max_score"] or 5) if p["status"] in ("open", "finished", "closed") else max_setting()
    asked = q("SELECT * FROM asked WHERE participant_id=? ORDER BY ord", (pid,))
    rows = []
    jsum = [0] * len(js)
    jcnt = [0] * len(js)
    total = cnt = 0
    for a in asked:
        got = {r["judge_id"]: r["ball"] for r in
               q("SELECT judge_id, ball FROM scores WHERE asked_id=?", (a["id"],))}
        sc = [got.get(j["id"]) for j in js]
        vals = [v for v in sc if v is not None]
        for i, v in enumerate(sc):
            if v is not None:
                jsum[i] += v
                jcnt[i] += 1
                total += v
                cnt += 1
        rows.append({"ord": a["ord"], "text": a["text"], "answer": a["answer"] or "",
                     "status": a["status"], "scores": sc,
                     "sum": sum(vals), "avg": round(sum(vals) / len(vals), 2) if vals else None})
    return {"p": p, "judges": js, "rows": rows,
            "judge_sum": jsum,
            "judge_avg": [round(jsum[i] / jcnt[i], 2) if jcnt[i] else None for i in range(len(js))],
            "total": total, "mx": mx, "max": len(asked) * len(js) * mx,
            "overall": round(total / cnt, 2) if cnt else None,
            "answered": len([a for a in asked if a["status"] == "done"]), "n_q": len(asked)}


# ---------- kim kirgan ----------

def actor():
    if session.get("admin"):
        return {"role": "admin"}
    code = session.get("code")
    if code:
        j = q("SELECT * FROM judges WHERE code=?", (code,), one=True)
        if j:
            return {"role": "judge", "jid": j["id"], "num": j["num"],
                    "name": f"{j['ism']} {j['familya']}"}
    pid = session.get("pid")
    if pid:
        p = q("SELECT id FROM participants WHERE id=?", (pid,), one=True)
        if p:
            return {"role": "candidate", "pid": p["id"]}
    return None


def need(*roles):
    a = actor()
    if not a or a["role"] not in roles:
        if request.path.startswith("/api/"):
            abort(401)
        abort(redirect(url_for("index")))
    return a


def admin_only():
    if not session.get("admin"):
        abort(redirect(url_for("admin_login")))


_LOGIN_ATTEMPTS = {}
_LOGIN_LOCK = threading.Lock()


def too_many_attempts(bucket, max_attempts=10, window=300):
    """IP manziliga qarab oddiy tezlik cheklovi — kod/parolni qo'pol kuch bilan
    (brute-force) taxmin qilishni sekinlashtiradi. Internetga chiqarilgan sayt
    uchun muhim, chunki endi uni istalgan kishi urinib ko'ra oladi."""
    key = f"{bucket}:{request.remote_addr or 'noma-lum'}"
    now = time.time()
    with _LOGIN_LOCK:
        hits = [t for t in _LOGIN_ATTEMPTS.get(key, ()) if now - t < window]
        hits.append(now)
        _LOGIN_ATTEMPTS[key] = hits
        return len(hits) > max_attempts


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if too_many_attempts("kod"):
            flash("Juda ko'p urinish. Bir necha daqiqadan keyin qayta urinib ko'ring.")
            return redirect(url_for("index"))
        code = "".join(ch for ch in request.form.get("code", "") if ch.isdigit())
        if q("SELECT 1 FROM judges WHERE code=?", (code,), one=True):
            session.clear()
            session["code"] = code
            return redirect(url_for("judge"))
        flash("Kod noto'g'ri yoki eskirgan. Adminga murojaat qiling.")
        return redirect(url_for("index"))
    a = actor()
    if a:
        return redirect({"candidate": url_for("candidate"), "judge": url_for("judge"),
                         "admin": url_for("admin")}[a["role"]])
    return render_template("index.html")


@app.route("/chiqish")
def logout():
    a = actor()
    if a and a["role"] == "candidate":
        # Ishtirokchi savol-javobni tugatmasdan chiqsa, suhbat yopiladi
        run("UPDATE participants SET status='closed' WHERE id=? AND status IN ('open','waiting')",
            (a["pid"],))
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin/kirish", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if too_many_attempts("admin"):
            flash("Juda ko'p urinish. Bir necha daqiqadan keyin qayta urinib ko'ring.")
            return redirect(url_for("admin_login"))
        if check_password_hash(get_setting("admin_password"), request.form.get("password", "")):
            session.clear()
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Parol noto'g'ri.")
        return redirect(url_for("admin_login"))
    return render_template("admin_login.html")


# ---------- ishtirokchi ----------

EMPTY_VALS = {"ism": "", "familya": "", "tugilgan": "", "manzil": "", "direction": ""}


@app.route("/royxat", methods=["GET", "POST"])
def register():
    all_dirs = q("""SELECT d.id, d.name, (SELECT COUNT(*) FROM questions WHERE direction_id=d.id) AS n
                    FROM directions d ORDER BY d.name""")
    usable = [d for d in all_dirs if d["n"] > 0]
    if request.method == "POST":
        did = request.form.get("direction", type=int)
        d = q("SELECT * FROM directions WHERE id=?", (did,), one=True) if did else None
        f = {k: request.form.get(k, "").strip() for k in ("ism", "familya", "tugilgan", "manzil")}
        vals = {**f, "direction": str(did) if did else ""}
        missing = {k for k in ("ism", "familya", "tugilgan") if not f[k]}
        if not d:
            missing.add("direction")
        if missing:
            flash("Belgilangan maydonlarni to'ldiring.")
            return render_template("register.html", dirs=usable, has_any=bool(all_dirs),
                                   vals=vals, missing=missing)
        pool = [r["id"] for r in q("SELECT id FROM questions WHERE direction_id=? ORDER BY id", (did,))]
        if not pool:
            flash(f"\"{d['name']}\" yo'nalishida savol yo'q. Adminga murojaat qiling.")
            return render_template("register.html", dirs=usable, has_any=bool(all_dirs),
                                   vals=vals, missing=set())
        nq = max(1, min(50, int(get_setting("n_questions"))))
        k = min(nq, len(pool))
        ids = random.sample(pool, k) if get_setting("q_order") == "random" else pool[:k]
        pid = insert_returning_id(
            """INSERT INTO participants(created_at, direction_id, yonalish, judges, n_questions,
                     ism, familya, tugilgan, manzil, registered, status)
                     VALUES(?,?,?,?,?,?,?,?,?,1,'waiting') RETURNING id""",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), did, d["name"], "[]", k,
             f["ism"], f["familya"], f["tugilgan"], f["manzil"]))
        for i, qid in enumerate(ids, 1):
            row = q("SELECT text, answer FROM questions WHERE id=?", (qid,), one=True)
            run("INSERT INTO asked(participant_id, ord, text, answer) VALUES(?,?,?,?)",
                (pid, i, row["text"], row["answer"] or ""))
        session.clear()
        session["pid"] = pid
        return redirect(url_for("candidate"))
    return render_template("register.html", dirs=usable, has_any=bool(all_dirs),
                           vals=EMPTY_VALS, missing=set())


@app.route("/nomzod")
def candidate():
    a = need("candidate")
    return render_template("candidate.html", p=get_part(a["pid"]))


def start_participant(pid):
    """Xato bo'lsa matn qaytaradi, muvaffaqiyatda None."""
    p = get_part(pid)
    if not p or p["status"] != "waiting":
        return "Bu ishtirokchi hozir boshlay olmaydi."
    if cur_part():
        return "Hozir boshqa ishtirokchi javob bermoqda. Navbatingizni kuting."
    first = q("SELECT id FROM participants WHERE status='waiting' ORDER BY id LIMIT 1", one=True)
    if first["id"] != pid:
        return "Sizdan oldin navbatda ishtirokchilar bor."
    judges = q("SELECT * FROM judges ORDER BY num")
    if not judges:
        return "Hakamlar qo'shilmagan. Adminga murojaat qiling."
    has_q = q("SELECT 1 FROM asked WHERE participant_id=? LIMIT 1", (pid,), one=True)
    if not has_q:
        return "Bu ishtirokchiga savollar biriktirilmagan. Adminga murojaat qiling."
    snapshot = [{"id": j["id"], "num": j["num"], "name": f"{j['ism']} {j['familya']}"} for j in judges]
    run("UPDATE participants SET status='open', judges=?, max_score=? WHERE id=?",
        (json.dumps(snapshot), max_setting(), pid))
    return None


def pick_question(pid, asked_id):
    """Ishtirokchi xohlagan savolini tanlaydi. Xato bo'lsa matn qaytaradi."""
    p = get_part(pid)
    if not p or p["status"] != "open":
        return "Savol tanlash mumkin emas."
    if current_asked(pid):
        return "Avval joriy savol baholansin."
    ask = q("SELECT * FROM asked WHERE id=? AND participant_id=?", (asked_id, pid), one=True)
    if not ask or ask["status"] != "waiting":
        return "Bu savolni tanlab bo'lmaydi."
    run("UPDATE asked SET status='current' WHERE id=?", (ask["id"],))
    return None


@app.route("/api/boshlash", methods=["POST"])
def api_start():
    a = need("candidate")
    err = start_participant(a["pid"])
    if err:
        return jsonify(error=err), 400
    return jsonify(ok=True)


@app.route("/api/tanlash", methods=["POST"])
def api_pick():
    a = need("candidate")
    err = pick_question(a["pid"], (request.json or {}).get("id"))
    if err:
        return jsonify(error=err), 400
    return jsonify(ok=True)


# ---------- hakam ----------

@app.route("/hakam")
def judge():
    a = need("judge")
    return render_template("judge.html", num=a["num"], name=a["name"])


@app.route("/api/baho", methods=["POST"])
def api_score():
    a = need("judge")
    p = cur_part()
    if not p or a["jid"] not in [j["id"] for j in snap(p)]:
        return jsonify(error="Baholash mumkin emas."), 400
    data = request.json or {}
    try:
        ball = int(data.get("ball"))
    except (TypeError, ValueError):
        return jsonify(error="Baho noto'g'ri."), 400
    mx = int(p["max_score"] or 5)
    if not 1 <= ball <= mx:
        return jsonify(error=f"Baho 1 dan {mx} gacha bo'lishi kerak."), 400
    ask = q("SELECT * FROM asked WHERE id=? AND participant_id=?", (data.get("id"), p["id"]), one=True)
    if not ask or ask["status"] != "current":
        return jsonify(error="Bu savol hozir baholanmaydi."), 400
    if USE_PG:
        run("""INSERT INTO scores(asked_id, judge_id, ball) VALUES(?,?,?)
               ON CONFLICT(asked_id, judge_id) DO UPDATE SET ball=EXCLUDED.ball""",
            (ask["id"], a["jid"], ball))
    else:
        run("INSERT OR REPLACE INTO scores(asked_id, judge_id, ball) VALUES(?,?,?)",
            (ask["id"], a["jid"], ball))
    close_if_complete(ask["id"])
    return jsonify(ok=True)


# ---------- umumiy holat (polling) ----------

@app.route("/api/holat")
def api_state():
    a = need("candidate", "judge", "admin")
    p = get_part(a["pid"]) if a["role"] == "candidate" else cur_part()
    out = {"role": a["role"], "participant": None, "finished": False, "closed": False,
           "current": None, "n_judges": 0, "total": 0,
           "max_score": int(p["max_score"] or 5) if p and p["status"] in ("open", "finished", "closed") else max_setting()}
    jid = None
    if a["role"] == "judge":
        jid = a["jid"]
        run("UPDATE judges SET last_seen=? WHERE id=?", (time.time(), jid))
        out["me"] = {"num": a["num"], "name": a["name"]}
    if a["role"] != "candidate":
        nxt = q("SELECT ism, familya FROM participants WHERE status='waiting' ORDER BY id LIMIT 1", one=True)
        out["waiting"] = q("SELECT COUNT(*) c FROM participants WHERE status='waiting'", one=True)["c"]
        out["next"] = f"{nxt['ism']} {nxt['familya']}" if nxt else None
    if not p:
        last = q("SELECT id FROM participants WHERE status='finished' ORDER BY id DESC LIMIT 1", one=True)
        out["last"] = last["id"] if last else None
        return jsonify(out)
    st = p["status"]
    out.update(finished=st == "finished", closed=st == "closed",
               participant={"id": p["id"], "status": st, "ism": p["ism"], "familya": p["familya"],
                            "yonalish": p["yonalish"]})
    if a["role"] == "candidate":
        ahead = q("SELECT COUNT(*) c FROM participants WHERE status='waiting' AND id<?",
                  (p["id"],), one=True)["c"]
        busy = 1 if cur_part() else 0
        out.update(ahead=ahead + busy, can_start=st == "waiting" and ahead == 0 and not busy)
    js = snap(p)
    out["n_judges"] = len(js)
    asked = q("SELECT * FROM asked WHERE participant_id=? ORDER BY ord", (p["id"],))
    out["total"] = len(asked)
    cur = current_asked(p["id"])
    have = {}
    if cur:
        have = {r["judge_id"]: r["ball"] for r in
                q("SELECT judge_id, ball FROM scores WHERE asked_id=?", (cur["id"],))}
        out["current"] = {"id": cur["id"], "ord": cur["ord"], "text": cur["text"],
                          "scored": len([j for j in js if j["id"] in have]),
                          "mine": have.get(jid) if jid else None}
        if a["role"] != "candidate":
            out["current"]["answer"] = cur["answer"] or ""
        if a["role"] in ("judge", "admin"):
            # Hakamlar bir-birining bahosini emas, faqat kim allaqachon baho
            # qo'yganini ko'radi (qizil/yashil doiracha) — bahoga ta'sir qilmasin.
            out["current"]["panel"] = [{"num": j["num"], "scored": j["id"] in have} for j in js]
    if a["role"] in ("candidate", "admin"):
        show_all = a["role"] == "admin" or st != "waiting"
        out["questions"] = [{"id": r["id"], "ord": r["ord"], "status": r["status"],
                             "text": r["text"] if show_all else None}
                            for r in asked]
    if a["role"] == "admin":
        now = time.time()
        seen = {r["id"]: r["last_seen"] for r in q("SELECT id, last_seen FROM judges")}
        exist = set(seen)
        out["judges"] = [{"num": j["num"], "name": j["name"], "ball": have.get(j["id"]),
                          "removed": j["id"] not in exist,
                          "online": now - (seen.get(j["id"]) or 0) < 8} for j in js]
    if jid and st == "open":
        out["my"] = [{"ord": r["ord"], "ball": r["ball"]} for r in q(
            """SELECT a.ord, s.ball FROM asked a LEFT JOIN scores s
               ON s.asked_id=a.id AND s.judge_id=? WHERE a.participant_id=? ORDER BY a.ord""",
            (jid, p["id"]))]
    return jsonify(out)


# ---------- natijalar ----------

def can_see(pid):
    a = need("candidate", "judge", "admin")
    if a["role"] == "candidate" and a["pid"] != pid:
        abort(403)
    if not get_part(pid):
        abort(404)
    return a


@app.route("/natija")
def my_result():
    a = need("candidate")
    return redirect(url_for("result_page", pid=a["pid"]))


@app.route("/natija/<int:pid>")
def result_page(pid):
    a = can_see(pid)
    r = results(pid)
    return render_template("result.html", r=r, p=r["p"], a=a)


def _pdf_disposition(name):
    """Fayl nomida o'zbekcha harflar (o', g' va h.k.) ham to'g'ri chiqishi uchun —
    eski brauzerlar uchun oddiy, yangilari uchun to'liq UTF-8 nom birga beriladi."""
    from urllib.parse import quote
    ascii_name = name.encode("ascii", "ignore").decode("ascii").strip() or "natija"
    return f'attachment; filename="{ascii_name}.pdf"; filename*=UTF-8\'\'{quote(name)}.pdf'


@app.route("/natija/<int:pid>.pdf")
def result_pdf(pid):
    can_see(pid)
    from pdf import participant_pdf
    r = results(pid)
    data = participant_pdf(r)
    name = _safe_filename(f"{r['p']['ism']} {r['p']['familya']}".strip()) or f"natija-{pid}"
    return Response(data, mimetype="application/pdf",
                    headers={"Content-Disposition": _pdf_disposition(name)})


def all_results():
    out = []
    for p in q("SELECT * FROM participants WHERE registered=1 AND status NOT IN ('issued','waiting') ORDER BY id"):
        r = results(p["id"])
        out.append({"p": p, "r": r, "overall": r["overall"]})
    out.sort(key=lambda x: (x["overall"] is None, -(x["overall"] or 0)))
    return out


@app.route("/natijalar")
def results_list():
    a = need("judge", "admin")
    return render_template("results_list.html", items=all_results(), a=a)


@app.route("/natijalar.pdf")
def results_list_pdf():
    need("judge", "admin")
    from pdf import rating_pdf
    return Response(rating_pdf(all_results()), mimetype="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=reyting.pdf"})


# ---------- admin: boshqaruv ----------

def connect_link():
    """Boshqa kompyuterlar shu manzil orqali ulanadi. Lokal tarmoqda ishlaganda
    kompyuterning tarmoq manzilini, bulutda joylashganda esa haqiqiy (ochiq)
    manzilni ko'rsatadi."""
    host = request.host
    if not host.split(":")[0].startswith(("127.", "192.168.", "10.", "localhost")):
        scheme = request.headers.get("X-Forwarded-Proto", "https" if request.is_secure else "http")
        return f"{scheme}://{host}"
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except OSError:
        return None
    port = host.split(":")[1] if ":" in host else "80"
    return f"http://{ip}:{port}"


@app.route("/admin")
def admin():
    admin_only()
    return render_template("admin.html", link=connect_link())


@app.route("/admin/yakunlash", methods=["POST"])
def admin_force():
    admin_only()
    p = cur_part()
    if p:
        c = current_asked(p["id"])
        if c:
            run("UPDATE asked SET status='done' WHERE id=?", (c["id"],))
            update_finished(p["id"])
    return redirect(url_for("admin"))


# ---------- admin: yo'nalishlar ----------

@app.route("/admin/yonalishlar", methods=["GET", "POST"])
def admin_directions():
    admin_only()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Yo'nalish nomini kiriting.")
        elif q("SELECT 1 FROM directions WHERE name=?", (name,), one=True):
            flash(f"\"{name}\" yo'nalishi allaqachon bor.")
        else:
            run("INSERT INTO directions(name) VALUES(?)", (name,))
            flash(f"\"{name}\" yo'nalishi qo'shildi. Endi Savollar menyusida unga savol qo'shing.")
        return redirect(url_for("admin_directions"))
    items = q("""SELECT d.id, d.name, (SELECT COUNT(*) FROM questions WHERE direction_id=d.id) AS n
                 FROM directions d ORDER BY d.name""")
    return render_template("admin_directions.html", items=items)


@app.route("/admin/yonalishlar/<int:did>/ochirish", methods=["POST"])
def admin_direction_delete(did):
    admin_only()
    run("DELETE FROM questions WHERE direction_id=?", (did,))
    run("DELETE FROM directions WHERE id=?", (did,))
    flash("Yo'nalish va uning savollari o'chirildi.")
    return redirect(url_for("admin_directions"))


# ---------- admin: savollar ----------

@app.route("/admin/savollar", methods=["GET", "POST"])
def admin_questions():
    admin_only()
    dirs = q("SELECT * FROM directions ORDER BY name")
    if request.method == "POST":
        did = request.form.get("direction", type=int)
        text = request.form.get("question", "").strip()
        ans = request.form.get("answer", "").strip()
        qid = request.form.get("qid", type=int)
        if not did or not q("SELECT 1 FROM directions WHERE id=?", (did,), one=True):
            flash("Avval yo'nalishni tanlang.")
            return redirect(url_for("admin_questions"))
        if not text:
            flash("Savol matnini kiriting.")
            return redirect(url_for("admin_questions", d=did, edit=qid))
        if qid:
            run("UPDATE questions SET direction_id=?, text=?, answer=? WHERE id=?", (did, text, ans, qid))
            flash("Savol yangilandi.")
        else:
            run("INSERT INTO questions(direction_id, text, answer) VALUES(?,?,?)", (did, text, ans))
            flash("Savol va javob qo'shildi. Keyingisini yozishingiz mumkin.")
        return redirect(url_for("admin_questions", d=did))
    flt = request.args.get("d", type=int)
    edit = request.args.get("edit", type=int)
    eq = q("SELECT * FROM questions WHERE id=?", (edit,), one=True) if edit else None
    if eq:
        flt = eq["direction_id"]
    sql = """SELECT qu.id, qu.text, qu.answer, qu.direction_id, d.name AS dname FROM questions qu
             LEFT JOIN directions d ON d.id=qu.direction_id"""
    items = q(sql + (" WHERE qu.direction_id=? ORDER BY qu.id" if flt else " ORDER BY d.name, qu.id"),
              (flt,) if flt else ())
    return render_template("admin_questions.html", dirs=dirs, items=items, flt=flt, eq=eq,
                           order=get_setting("q_order"), nq=get_setting("n_questions"))


@app.route("/admin/savollar/tartib", methods=["POST"])
def admin_questions_order():
    admin_only()
    set_setting("q_order", "sequential" if request.form.get("order") == "sequential" else "random")
    flash("Savollar tartibi saqlandi. Keyingi berilgan kodlardan boshlab amal qiladi.")
    return redirect(url_for("admin_questions"))


@app.route("/admin/savollar/<int:qid>/ochirish", methods=["POST"])
def admin_question_delete(qid):
    admin_only()
    run("DELETE FROM questions WHERE id=?", (qid,))
    return redirect(request.referrer or url_for("admin_questions"))


# ---------- admin: ishtirokchilar ----------

@app.route("/admin/ishtirokchilar")
def admin_participants():
    admin_only()
    items = []
    for p in q("SELECT * FROM participants ORDER BY id DESC"):
        r = results(p["id"])
        items.append({"p": p, "r": r})
    return render_template("admin_participants.html", items=items, cur=cur_part(), status_uz=STATUS_UZ)


@app.route("/admin/ishtirokchilar/<int:pid>/panel")
def admin_participant_panel(pid):
    admin_only()
    p = get_part(pid) or abort(404)
    return render_template("_pdetail.html", p=p, r=results(pid), status_uz=STATUS_UZ)


@app.route("/admin/ishtirokchilar/<int:pid>/yopish", methods=["POST"])
def admin_participant_close(pid):
    admin_only()
    run("UPDATE participants SET status='closed' WHERE id=? AND status='open'", (pid,))
    return redirect(url_for("admin_participants"))


@app.route("/admin/ishtirokchilar/<int:pid>/ochirish", methods=["POST"])
def admin_participant_delete(pid):
    admin_only()
    run("DELETE FROM scores WHERE asked_id IN (SELECT id FROM asked WHERE participant_id=?)", (pid,))
    run("DELETE FROM asked WHERE participant_id=?", (pid,))
    run("DELETE FROM participants WHERE id=?", (pid,))
    return redirect(url_for("admin_participants"))


# ---------- admin: hakamlar ----------

@app.route("/admin/hakamlar", methods=["GET", "POST"])
def admin_judges():
    admin_only()
    if request.method == "POST":
        ism = request.form.get("ism", "").strip()
        fam = request.form.get("familya", "").strip()
        tug = request.form.get("tugilgan", "").strip()
        num = request.form.get("num", type=int)
        if not ism or not fam:
            flash("Hakamning ismi va familyasini kiriting.")
        elif not num or num < 1:
            flash("Hakam raqamini to'g'ri kiriting.")
        elif q("SELECT 1 FROM judges WHERE num=?", (num,), one=True):
            flash(f"Hakam {num} raqami band. Boshqa raqam tanlang.")
        else:
            run("INSERT INTO judges(num, ism, familya, tugilgan, code) VALUES(?,?,?,?,?)",
                (num, ism, fam, tug, new_code()))
            flash(f"Hakam {num} ({ism} {fam}) qo'shildi. Unga kod berildi.")
        return redirect(url_for("admin_judges"))
    now = time.time()
    rows = [{"j": r, "online": now - (r["last_seen"] or 0) < 8}
            for r in q("SELECT * FROM judges ORDER BY num")]
    nxt = 1
    used = {r["j"]["num"] for r in rows}
    while nxt in used:
        nxt += 1
    return render_template("admin_judges.html", rows=rows, next_num=nxt)


@app.route("/admin/hakamlar/<int:jid>/yangilash", methods=["POST"])
def admin_judge_renew(jid):
    admin_only()
    run("UPDATE judges SET code=?, last_seen=0 WHERE id=?", (new_code(), jid))
    flash("Hakam chiqarib yuborildi va unga yangi kod berildi.")
    return redirect(url_for("admin_judges"))


@app.route("/admin/hakamlar/<int:jid>/ochirish", methods=["POST"])
def admin_judge_delete(jid):
    admin_only()
    run("DELETE FROM judges WHERE id=?", (jid,))
    recheck_open()
    flash("Hakam o'chirildi.")
    return redirect(url_for("admin_judges"))


# ---------- admin: sozlamalar ----------

@app.route("/admin/sozlamalar", methods=["GET", "POST"])
def admin_settings():
    admin_only()
    if request.method == "POST":
        form = request.form.get("form")
        if form == "password":
            if not check_password_hash(get_setting("admin_password"), request.form.get("old", "")):
                flash("Joriy parol noto'g'ri.")
            elif len(request.form.get("new", "")) < 4:
                flash("Yangi parol kamida 4 belgidan iborat bo'lsin.")
            elif request.form.get("new") != request.form.get("new2"):
                flash("Yangi parollar bir xil emas.")
            else:
                set_setting("admin_password", generate_password_hash(request.form["new"]))
                flash("Parol o'zgartirildi.")
        elif form == "general":
            set_setting("n_questions", max(1, min(50, request.form.get("n_questions", type=int) or 5)))
            set_setting("max_score", max(1, min(10, request.form.get("max_score", type=int) or 5)))
            flash("Sozlamalar saqlandi. Ball tizimi hali boshlanmagan suhbatlardan boshlab amal qiladi.")
        elif form == "wipe":
            run("DELETE FROM scores")
            run("DELETE FROM asked")
            run("DELETE FROM participants")
            flash("Barcha ishtirokchilar va natijalar tozalandi.")
        return redirect(url_for("admin_settings"))
    return render_template("admin_settings.html", nq=get_setting("n_questions"), mx=max_setting())


@app.route("/admin/supabase", methods=["GET", "POST"])
def admin_supabase():
    admin_only()
    if USE_PG:
        # Dastur allaqachon Postgres'ning o'zida (DATABASE_URL orqali) ishlayapti —
        # alohida sinxronlash chalkashlik keltirib chiqaradi, shuning uchun yopiq.
        flash("Bu menyu kerak emas: dastur allaqachon to'g'ridan-to'g'ri Supabase'da ishlayapti.")
        return redirect(url_for("admin"))
    import supa
    if request.method == "POST":
        form = request.form.get("form")
        if form == "save":
            set_setting("supabase_url", request.form.get("url", "").strip())
            set_setting("supabase_key", request.form.get("key", "").strip())
            set_setting("filial_nomi", request.form.get("filial", "").strip())
            flash("Sozlamalar saqlandi.")
        elif form == "pull":
            ok, msg, n = supa.pull_savollar(get_setting, run, q)
            flash(f"{msg} {n} ta yangi yozuv qo'shildi." if ok else msg)
        elif form == "push":
            ok, msg, n = supa.push_savollar(get_setting, q("SELECT * FROM directions"),
                                            q("SELECT * FROM questions"))
            flash(f"{msg} {n} ta yangi savol yuklandi." if ok else msg)
        elif form == "retry":
            pid = request.form.get("pid", type=int)
            if pid:
                try_sync_result(pid)
        elif form == "retry_all":
            for r in q("SELECT id FROM participants WHERE synced=0 AND status IN ('finished','closed')"):
                try_sync_result(r["id"])
            flash("Barchasi qayta yuborildi.")
        return redirect(url_for("admin_supabase"))
    pending = q("""SELECT * FROM participants WHERE synced=0 AND status IN ('finished','closed')
                  ORDER BY id DESC""")
    return render_template("admin_supabase.html",
                           url=get_setting("supabase_url") or "", key=get_setting("supabase_key") or "",
                           filial=get_setting("filial_nomi") or "",
                           configured=supa.configured(get_setting), pending=pending, status_uz=STATUS_UZ)


init_db()

if __name__ == "__main__":
    import socket
    import threading
    import webbrowser
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except OSError:
        ip = "127.0.0.1"
    port = int(os.environ.get("PORT", 8000))
    print(f"\n  Savol javob ishga tushdi.\n  Shu kompyuterda:   http://127.0.0.1:{port}\n"
          f"  Boshqalar uchun:   http://{ip}:{port}\n  Admin:             /admin\n")
    if not os.environ.get("NO_BROWSER"):
        def open_browser():
            try:
                webbrowser.open(f"http://127.0.0.1:{port}")
            except Exception:
                pass  # server sifatida ishlaganda brauzer bo'lmasligi mumkin, muammo emas
        threading.Timer(1.2, open_browser).start()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
