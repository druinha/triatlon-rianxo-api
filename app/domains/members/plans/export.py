"""Seguimento dun plan en Excel: quen fixo cada sesión, co esforzo, e os comentarios.

Folla «Seguimento»: unha fila por atleta e unha columna por sesión (✓ ou ✓ 7 co esforzo);
a columna «Feitas» é unha fórmula (CONTAR.SI), así se alguén edita a folla, recalcúlase.
Folla «Comentarios»: o que escribiu cada atleta.
"""
import io
from datetime import date, timedelta

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

TXT = {
    "gl": {
        "sheet": "Seguimento", "comments": "Comentarios", "athlete": "Atleta", "done": "Feitas",
        "of": "de", "day": "Día", "session": "Sesión", "rpe": "Esforzo (1-10)", "comment": "Comentario",
        "title": "Seguimento", "week": "semana", "legend": "✓ = feita · o número é o esforzo (1-10)",
        "scope": {"general": "Plan xeral", "group": "Grupo", "athlete": "Individual"},
        "days": ["Luns", "Martes", "Mércores", "Xoves", "Venres", "Sábado", "Domingo"],
        "sport": {"swim": "Natación", "bike": "Bici", "run": "Carreira", "gym": "Ximnasio", "race": "Competición",
                  "other": "Outro"},
    },
    "es": {
        "sheet": "Seguimiento", "comments": "Comentarios", "athlete": "Atleta", "done": "Hechas",
        "of": "de", "day": "Día", "session": "Sesión", "rpe": "Esfuerzo (1-10)", "comment": "Comentario",
        "title": "Seguimiento", "week": "semana", "legend": "✓ = hecha · el número es el esfuerzo (1-10)",
        "scope": {"general": "Plan general", "group": "Grupo", "athlete": "Individual"},
        "days": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
        "sport": {"swim": "Natación", "bike": "Bici", "run": "Carrera", "gym": "Gimnasio", "race": "Competición",
                  "other": "Otro"},
    },
}
FONT = "Arial"


def build(plan: dict, sessions: list[dict], rows: list[dict], lang: str) -> bytes:
    t = TXT.get(lang, TXT["gl"])
    week: date = plan["week_start"]
    # As de descanso non se marcan
    cols = [s for s in sessions if s["sport"] != "rest"]
    who = plan["group_name"] or plan["athlete_name"] or ""
    title = f'{t["title"]} · {t["scope"][plan["scope"]]}{f" · {who}" if who else ""} · ' \
            f'{t["week"]} {week:%d/%m} – {week + timedelta(days=6):%d/%m/%Y}'

    wb = Workbook()
    ws = wb.active
    ws.title = t["sheet"]
    bold = Font(name=FONT, bold=True)
    head_fill = PatternFill("solid", fgColor="0B0B0C")
    ws["A1"] = title
    ws["A1"].font = Font(name=FONT, bold=True, size=13)
    ws["A2"] = t["legend"]
    ws["A2"].font = Font(name=FONT, italic=True, size=9, color="555555")

    header = [t["athlete"]] + [
        f'{t["days"][s["day"]][:3]} · {t["sport"].get(s["sport"], s["sport"])}' + (f' · {s["title"]}' if s["title"] else "")
        for s in cols
    ] + [f'{t["done"]} ({t["of"]} {len(cols)})']
    ws.append([])
    ws.append(header)
    for c in ws[4]:
        c.font = Font(name=FONT, bold=True, color="FFFFFF")
        c.fill = head_fill
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    ws["A4"].alignment = Alignment(vertical="center")

    last_col = get_column_letter(len(cols) + 1)
    for i, r in enumerate(rows, start=5):
        done = {d["session_id"]: d for d in r["done"]}
        line = [r["full_name"]]
        for s in cols:
            d = done.get(s["id"])
            line.append(None if d is None else (f'✓ {d["rpe"]}' if d.get("rpe") else "✓"))
        line.append(f'=COUNTIF(B{i}:{last_col}{i},"✓*")' if cols else 0)
        ws.append(line)
        for c in ws[i]:
            c.font = Font(name=FONT)
            if c.column > 1:
                c.alignment = Alignment(horizontal="center")
        ws.cell(row=i, column=len(cols) + 2).font = bold

    ws.column_dimensions["A"].width = 26
    for j in range(2, len(cols) + 3):
        ws.column_dimensions[get_column_letter(j)].width = 14
    ws.row_dimensions[4].height = 46
    ws.freeze_panes = "B5"

    wc = wb.create_sheet(t["comments"])
    wc.append([t["athlete"], t["day"], t["session"], t["rpe"], t["comment"]])
    for c in wc[1]:
        c.font = Font(name=FONT, bold=True, color="FFFFFF")
        c.fill = head_fill
    by_id = {s["id"]: s for s in cols}
    for r in rows:
        for d in r["done"]:
            s = by_id.get(d["session_id"])
            if s and (d.get("rpe") or d.get("comment")):
                wc.append([r["full_name"], t["days"][s["day"]], t["sport"].get(s["sport"], s["sport"]),
                           d.get("rpe"), d.get("comment")])
    for row in wc.iter_rows(min_row=2):
        for c in row:
            c.font = Font(name=FONT)
    for col, w in zip("ABCDE", (26, 12, 16, 14, 60)):
        wc.column_dimensions[col].width = w

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
