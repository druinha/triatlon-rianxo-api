"""Ler un plan semanal dun Excel (.xlsx) ou dun Word (.docx) cunha táboa de 7 días.

O formato é o que xa usa o adestrador: unha fila de cabeceira cos días (LUNES… DOMINGO, ou en
galego LUNS… DOMINGO) e debaixo, en cada columna, o adestramento dese día. Dentro dunha cela,
cada sesión empeza por unha liña co deporte ("Bici", "Natación Mar", "Carrera", "Gym"…);
as liñas cun "+" só tamén separan sesións. Tamén vale cos días na primeira columna.

Non garda nada: devolve as sesións para que o adestrador as revise no editor.
"""
import io
import re
import unicodedata

from fastapi import HTTPException


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


DAYS = {
    "lunes": 0, "luns": 0, "lun": 0,
    "martes": 1, "mar": 1,
    "miercoles": 2, "mercores": 2, "mie": 2, "mer": 2,
    "jueves": 3, "xoves": 3, "jue": 3, "xov": 3,
    "viernes": 4, "venres": 4, "vie": 4, "ven": 4,
    "sabado": 5, "sab": 5,
    "domingo": 6, "dom": 6,
}

# Só palabras que case sempre abren unha sesión. "Rodaje", "fuerza", "core"… quedan fóra:
# adoitan ir dentro do adestramento ("Rodaje 1h30 Z1", "Natación · Fuerza").
SPORTS = [
    (r"natacion|nado|swim|augas abertas|aguas abiertas", "swim"),
    (r"bici(?:cleta)?|ciclismo|rodillo|rodillos|btt|mtb", "bike"),
    (r"carrera|carreira|correr|running", "run"),
    (r"gym|gimnasio|ximnasio", "gym"),
    (r"descanso", "rest"),
    (r"competicion|proba|prueba", "race"),
]
_SPORT_RE = re.compile(r"^(?P<sport>" + "|".join(p for p, _ in SPORTS) + r")\b[\s:.\-]*(?P<rest>.*)$", re.IGNORECASE)
# Unha duración ao final do título: "suave 1h 30´" → ("suave", 90)
_TAIL_DUR_RE = re.compile(r"^(.*?)\s*((?:\d{1,2}\s*h(?:oras?)?\s*)?(?:\d{1,3}\s*(?:min|['´′’]))|\d{1,2}\s*h(?:oras?)?)$", re.IGNORECASE)
_DUR_RE = re.compile(r"^(?:(\d{1,2})\s*h(?:oras?)?\s*)?(?:(\d{1,3})\s*(?:min|['´′’]))?$", re.IGNORECASE)


def _day_of(text: str) -> int | None:
    t = _norm(text).rstrip(".:")
    return DAYS.get(t)


def _sport_of(word: str) -> str:
    w = _norm(word)
    for pattern, sport in SPORTS:
        if re.fullmatch(pattern, w):
            return sport
    return "other"


def _duration(text: str) -> int | None:
    m = _DUR_RE.match(_norm(text).replace(" ", ""))
    if not m or not (m.group(1) or m.group(2)):
        return None
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)


def split_sessions(text: str) -> list[dict]:
    """Texto dunha cela → sesións [{sport, title, duration_min, content}]"""
    sessions: list[dict] = []
    cur: dict | None = None
    for raw in text.replace("\r", "\n").split("\n"):
        line = raw.strip()
        if not line:
            if cur and cur["lines"] and cur["lines"][-1] != "":
                cur["lines"].append("")
            continue
        if line == "+":
            cur = None
            continue
        m = _SPORT_RE.match(_norm(line))
        if m:
            # O resto da liña: un título ("Mar", "Cabra") ou xa a duración ("30´", "2h 30´")
            rest = line[len(line) - len(m.group("rest")):].strip() if m.group("rest") else ""
            cur = {"sport": _sport_of(m.group("sport")), "title": None, "duration_min": None, "lines": []}
            dur = _duration(rest) if rest else None
            if dur:
                cur["duration_min"] = dur
                cur["lines"].append(rest)
            elif rest:
                tail = _TAIL_DUR_RE.match(rest)
                if tail and tail.group(1) and _duration(tail.group(2)):
                    cur["title"] = tail.group(1)[:120]
                    cur["duration_min"] = _duration(tail.group(2))
                else:
                    cur["title"] = rest[:120]
            sessions.append(cur)
            continue
        if cur is None:
            cur = {"sport": "other", "title": None, "duration_min": None, "lines": []}
            sessions.append(cur)
        if not cur["lines"]:
            # Unha palabra curta xusto debaixo do deporte é o título ("Natación / Grupo")
            if cur["title"] is None and cur["sport"] != "other" and re.fullmatch(r"[^\W\d_]+(?: [^\W\d_]+){0,2}", line):
                cur["title"] = line[:120]
                continue
            if cur["duration_min"] is None:
                cur["duration_min"] = _duration(line)
        cur["lines"].append(line)
    out = []
    for s in sessions:
        content = "\n".join(s["lines"]).strip()
        if not content and not s["title"] and s["sport"] == "other":
            continue
        out.append({"sport": s["sport"], "title": s["title"], "duration_min": s["duration_min"],
                    "content": content[:4000] or None})
    return out


def _cell(v) -> str:
    return "" if v is None else str(v).strip()


def rows_to_week(rows: list[list[str]], preamble: list[str]) -> dict:
    days: list[list[str]] = [[] for _ in range(7)]
    found = False
    # 1) Días nunha fila de cabeceira
    for i, row in enumerate(rows):
        cols = {j: _day_of(c) for j, c in enumerate(row) if c and _day_of(c) is not None}
        if len(cols) >= 4:
            found = True
            preamble = preamble + [c for r in rows[:i] for c in r if c]
            for r in rows[i + 1:]:
                for j, d in cols.items():
                    if j < len(r) and r[j]:
                        days[d].append(r[j])
            break
    # 2) Días na primeira columna
    if not found:
        hits = [(i, _day_of(r[0])) for i, r in enumerate(rows) if r and r[0] and _day_of(r[0]) is not None]
        if len(hits) >= 4:
            found = True
            for i, d in hits:
                days[d].extend(c for c in rows[i][1:] if c)
    if not found:
        raise HTTPException(status_code=422, detail="import_no_days")
    week = [[s for text in cells for s in split_sessions(text)] for cells in days]
    title = next((p for p in preamble if p and _day_of(p) is None), None)
    return {"title": title[:120] if title else None, "days": week}


def parse_xlsx(data: bytes) -> dict:
    from openpyxl import load_workbook
    try:
        wb = load_workbook(io.BytesIO(data), data_only=True, read_only=True)
    except Exception:
        raise HTTPException(status_code=422, detail="import_unreadable")
    ws = wb.active
    rows = [[_cell(v) for v in row] for row in ws.iter_rows(values_only=True)]
    return rows_to_week([r for r in rows if any(r)], [])


def parse_docx(data: bytes) -> dict:
    from docx import Document
    try:
        doc = Document(io.BytesIO(data))
    except Exception:
        raise HTTPException(status_code=422, detail="import_unreadable")
    if not doc.tables:
        raise HTTPException(status_code=422, detail="import_no_days")
    table = max(doc.tables, key=lambda t: len(t.rows) * len(t.columns))
    rows = []
    for row in table.rows:
        seen: set[int] = set()
        cells = []
        for c in row.cells:
            # As celas combinadas repítense en python-docx
            cells.append("" if id(c._tc) in seen else c.text.strip())
            seen.add(id(c._tc))
        rows.append(cells)
    preamble = [p.text.strip() for p in doc.paragraphs if p.text.strip()][:3]
    return rows_to_week(rows, preamble)


def parse_file(filename: str, data: bytes) -> dict:
    name = filename.lower()
    if name.endswith(".xlsx") or data[:2] == b"PK" and b"xl/" in data[:2000]:
        return parse_xlsx(data)
    if name.endswith(".docx") or data[:2] == b"PK" and b"word/" in data[:2000]:
        return parse_docx(data)
    raise HTTPException(status_code=422, detail="import_format")