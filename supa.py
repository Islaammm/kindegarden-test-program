"""Supabase bilan sinxronlash — ixtiyoriy funksiya.
Sozlamalarda URL/kalit kiritilmagan bo'lsa, hech narsa qilinmaydi va xato bermaydi.
"""
import json

import requests

TIMEOUT = 10


def configured(get_setting):
    return bool(get_setting("supabase_url")) and bool(get_setting("supabase_key"))


def _headers(key, prefer=None):
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if prefer:
        h["Prefer"] = prefer
    return h


def _base(url):
    return url.rstrip("/") + "/rest/v1"


def push_result(get_setting, result, filial):
    """`results()` lug'atini Supabase'ning `natijalar` jadvaliga yuboradi. (ok, xabar) qaytaradi."""
    url, key = get_setting("supabase_url"), get_setting("supabase_key")
    if not url or not key:
        return False, "Supabase sozlanmagan"
    p = result["p"]
    payload = {
        "filial": filial or "", "ism": p["ism"], "familya": p["familya"], "tugilgan": p["tugilgan"],
        "manzil": p["manzil"], "yonalish": p["yonalish"], "jami_ball": result["total"],
        "max_ball": result["max"], "ortacha_ball": result["overall"],
        "yechilgan": result["answered"], "savollar_soni": result["n_q"],
        "tafsilot": result["rows"],
        "hakamlar": [{"num": j["num"], "name": j["name"]} for j in result["judges"]],
    }
    try:
        r = requests.post(_base(url) + "/natijalar", headers=_headers(key),
                          data=json.dumps(payload), timeout=TIMEOUT)
        if r.status_code in (200, 201):
            return True, "Natija Supabase'ga yuborildi."
        return False, f"Supabase xato qaytardi ({r.status_code}): {r.text[:200]}"
    except requests.RequestException as e:
        return False, f"Ulanish xatosi: {e}"


def pull_savollar(get_setting, run, q):
    """Supabase'dagi yo'nalish+savollarni mahalliy bazaga qo'shadi (mavjudlarini takrorlamaydi).
    (ok, xabar, qoshilgan_soni) qaytaradi."""
    url, key = get_setting("supabase_url"), get_setting("supabase_key")
    if not url or not key:
        return False, "Supabase sozlanmagan", 0
    try:
        r = requests.get(_base(url) + "/yonalishlar", headers=_headers(key),
                         params={"select": "id,name"}, timeout=TIMEOUT)
        r.raise_for_status()
        added = 0
        for d in r.json():
            row = q("SELECT id FROM directions WHERE name=?", (d["name"],), one=True)
            did = row["id"] if row else run("INSERT INTO directions(name) VALUES(?)", (d["name"],)).lastrowid
            rq = requests.get(_base(url) + "/savollar", headers=_headers(key),
                              params={"yonalish_id": f"eq.{d['id']}", "select": "text,answer"}, timeout=TIMEOUT)
            rq.raise_for_status()
            existing = {x["text"] for x in q("SELECT text FROM questions WHERE direction_id=?", (did,))}
            for sq in rq.json():
                if sq["text"] not in existing:
                    run("INSERT INTO questions(direction_id, text, answer) VALUES(?,?,?)",
                        (did, sq["text"], sq.get("answer") or ""))
                    added += 1
        return True, "Savollar banki bilan sinxronlandi.", added
    except requests.RequestException as e:
        return False, f"Ulanish xatosi: {e}", 0


def push_savollar(get_setting, dirs_rows, questions_rows):
    """Mahalliy yo'nalish+savollarni Supabase'ga yuklaydi (mavjudlarini takrorlamaydi).
    (ok, xabar, qoshilgan_soni) qaytaradi."""
    url, key = get_setting("supabase_url"), get_setting("supabase_key")
    if not url or not key:
        return False, "Supabase sozlanmagan", 0
    try:
        r = requests.get(_base(url) + "/yonalishlar", headers=_headers(key),
                         params={"select": "id,name"}, timeout=TIMEOUT)
        r.raise_for_status()
        remote_by_name = {d["name"]: d["id"] for d in r.json()}
        added = 0
        for d in dirs_rows:
            rid = remote_by_name.get(d["name"])
            if rid is None:
                cr = requests.post(_base(url) + "/yonalishlar", headers=_headers(key, "return=representation"),
                                   data=json.dumps({"name": d["name"]}), timeout=TIMEOUT)
                cr.raise_for_status()
                rid = cr.json()[0]["id"]
                remote_by_name[d["name"]] = rid
            rq = requests.get(_base(url) + "/savollar", headers=_headers(key),
                              params={"yonalish_id": f"eq.{rid}", "select": "text"}, timeout=TIMEOUT)
            rq.raise_for_status()
            existing = {x["text"] for x in rq.json()}
            for x in questions_rows:
                if x["direction_id"] == d["id"] and x["text"] not in existing:
                    pr = requests.post(_base(url) + "/savollar", headers=_headers(key),
                                       data=json.dumps({"yonalish_id": rid, "text": x["text"],
                                                        "answer": x["answer"] or ""}), timeout=TIMEOUT)
                    pr.raise_for_status()
                    added += 1
        return True, "Mahalliy savollar Supabase'ga yuklandi.", added
    except requests.RequestException as e:
        return False, f"Ulanish xatosi: {e}", 0
