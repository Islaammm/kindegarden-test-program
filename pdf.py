"""PDF natijalar (reportlab)."""
import io
import os
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from respath import resource_dir

FONTS = os.path.join(resource_dir(), "static", "fonts")
try:
    pdfmetrics.registerFont(TTFont("DV", os.path.join(FONTS, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DV-B", os.path.join(FONTS, "DejaVuSans-Bold.ttf")))
    F, FB = "DV", "DV-B"
except Exception:  # shrift topilmasa
    F, FB = "Helvetica", "Helvetica-Bold"

ACC = colors.HexColor("#0E5A62")
TINT = colors.HexColor("#DCEBEA")
LINE = colors.HexColor("#B9B09C")
INK = colors.HexColor("#16202A")
MUT = colors.HexColor("#56616C")


def st(name, size=10, bold=False, color=INK, align=0, leading=None):
    return ParagraphStyle(name, fontName=FB if bold else F, fontSize=size, textColor=color,
                          alignment=align, leading=leading or size * 1.3)


S_TITLE = st("t", 20, True, INK, leading=24)
S_SUB = st("s", 9, True, ACC)
S_CELL = st("c", 9.5)
S_CELLB = st("cb", 9.5, True)
S_CELLC = st("cc", 10, False, INK, 1)
S_CELLCB = st("ccb", 10, True, INK, 1)
S_HEAD = st("h", 8.5, True, INK, 1, 10.5)
S_LABEL = st("l", 9, False, MUT)
S_BIG = st("b", 15, True, ACC, 1, 18)
S_SMALL = st("sm", 8, False, MUT, 1)


def P(text, style):
    return Paragraph(escape(str(text if text is not None else "")).replace("\n", "<br/>"), style)


def fmt(v, nd=2):
    return "-" if v is None else f"{v:.{nd}f}"


def status_uz(s):
    return {"issued": "Kod berildi", "waiting": "Navbatda", "open": "Javob bermoqda",
            "finished": "Yakunlandi", "closed": "Yopilgan"}.get(s, s)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(F, 8)
    canvas.setFillColor(MUT)
    w, _ = doc.pagesize
    canvas.drawString(doc.leftMargin, 10 * mm, "Savol javob")
    canvas.drawRightString(w - doc.rightMargin, 10 * mm,
                           f"{datetime.now().strftime('%Y-%m-%d %H:%M')}  ·  {doc.page}-bet")
    canvas.restoreState()


def _doc(buf, landscape_mode):
    size = landscape(A4) if landscape_mode else A4
    return SimpleDocTemplate(buf, pagesize=size, leftMargin=15 * mm, rightMargin=15 * mm,
                             topMargin=14 * mm, bottomMargin=18 * mm, title="Savol javob natija")


def participant_pdf(r):
    p, js = r["p"], r["judges"]
    buf = io.BytesIO()
    doc = _doc(buf, len(js) > 4)
    width = doc.pagesize[0] - doc.leftMargin - doc.rightMargin
    story = [P("SAVOL JAVOB", S_SUB), P("Natija bayonnomasi", S_TITLE), Spacer(1, 5 * mm)]

    name = f"{p['ism'] or ''} {p['familya'] or ''}".strip() or "-"
    info = [
        ("F.I.Sh.", name), ("Tug'ilgan sana", p["tugilgan"] or "-"),
        ("Yo'nalish", p["yonalish"] or "-"), ("Manzil", p["manzil"] or "-"),
        ("Holat", status_uz(p["status"])), ("Sana", p["created_at"] or "-"),
    ]
    rows = []
    for i in range(0, len(info), 2):
        a, b = info[i], info[i + 1]
        rows.append([P(a[0], S_LABEL), P(a[1], S_CELLB), P(b[0], S_LABEL), P(b[1], S_CELLB)])
    t = Table(rows, colWidths=[width * .16, width * .34, width * .16, width * .34])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("LINEBELOW", (0, 0), (-1, -1), .4, colors.HexColor("#E4DFD2"))]))
    story += [t, Spacer(1, 6 * mm)]

    box = [[P("Yechilgan savollar", S_SMALL), P(f"Jami ball (har savol {r['mx']} ball)", S_SMALL),
            P("O'rtacha ball", S_SMALL)],
           [P(f"{r['answered']} / {r['n_q']}", S_BIG), P(f"{r['total']} / {r['max']}", S_BIG),
            P(f"{fmt(r['overall'])} / {r['mx']}", S_BIG)]]
    bt = Table(box, colWidths=[width / 3] * 3)
    bt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TINT), ("BOX", (0, 0), (-1, -1), .6, ACC),
                            ("LINEAFTER", (0, 0), (1, -1), .6, colors.white),
                            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story += [bt, Spacer(1, 7 * mm)]

    nj = len(js)
    w_no, w_sum, w_avg = 9 * mm, 15 * mm, 18 * mm
    w_j = min(26 * mm, max(17 * mm, (width - w_no - w_sum - w_avg - 60 * mm) / max(nj, 1)))
    w_q = width - w_no - w_sum - w_avg - w_j * nj
    head = [P("№", S_HEAD), P("Savol", st("hq", 8.5, True, INK, 0, 10.5))]
    for j in js:
        head.append(P(f"Hakam {j['num']}\n{j['name']}", S_HEAD))
    head += [P("Jami", S_HEAD), P("O'rtacha", S_HEAD)]
    data = [head]
    for row in r["rows"]:
        line = [P(row["ord"], S_CELLC), P(row["text"], S_CELL)]
        line += [P("-" if v is None else v, S_CELLC) for v in row["scores"]]
        line += [P(row["sum"], S_CELLC), P(fmt(row["avg"]), S_CELLCB)]
        data.append(line)
    data.append([P("", S_CELLC), P("Hakam bo'yicha jami ball", S_CELLB)]
                + [P(v, S_CELLCB) for v in r["judge_sum"]] + [P(r["total"], S_CELLCB), P("", S_CELLC)])
    data.append([P("", S_CELLC), P("Hakam bo'yicha o'rtacha", S_CELLB)]
                + [P(fmt(v), S_CELLCB) for v in r["judge_avg"]] + [P("", S_CELLC), P(fmt(r["overall"]), S_CELLCB)])
    tb = Table(data, colWidths=[w_no, w_q] + [w_j] * nj + [w_sum, w_avg], repeatRows=1)
    n = len(data)
    tb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TINT), ("LINEBELOW", (0, 0), (-1, 0), 1.2, ACC),
        ("GRID", (0, 0), (-1, n - 3), .4, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, n - 2), (-1, n - 1), TINT), ("BOX", (0, n - 2), (-1, n - 1), .6, ACC),
        ("LINEABOVE", (0, n - 2), (-1, n - 2), 1.2, ACC),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tb)
    if not js:
        story += [Spacer(1, 4 * mm), P("Suhbat hali boshlanmagan.", S_CELL)]
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


def rating_pdf(items):
    buf = io.BytesIO()
    doc = _doc(buf, False)
    width = doc.pagesize[0] - doc.leftMargin - doc.rightMargin
    story = [P("SAVOL JAVOB", S_SUB), P("Ishtirokchilar reytingi", S_TITLE), Spacer(1, 6 * mm)]
    head = [P(h, S_HEAD) for h in ("O'rin", "Ishtirokchi", "Yo'nalish", "Yechilgan", "Jami ball", "O'rtacha")]
    data = [head]
    for i, x in enumerate(items, 1):
        p, r = x["p"], x["r"]
        data.append([P(i, S_CELLC), P(f"{p['ism']} {p['familya']}", S_CELLB), P(p["yonalish"], S_CELL),
                     P(f"{r['answered']} / {r['n_q']}", S_CELLC), P(f"{r['total']} / {r['max']}", S_CELLC),
                     P(fmt(r["overall"]), S_CELLCB)])
    if not items:
        data.append([P("", S_CELL), P("Hali natija yo'q.", S_CELL)] + [P("", S_CELL)] * 4)
    tb = Table(data, colWidths=[width * .09, width * .27, width * .24, width * .13, width * .14, width * .13], repeatRows=1)
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), TINT), ("LINEBELOW", (0, 0), (-1, 0), 1.2, ACC),
                            ("GRID", (0, 0), (-1, -1), .4, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(tb)
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
