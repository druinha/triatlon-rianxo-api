"""Proba de extremo a extremo dos plans de adestramento (Fase 4, parte 2) contra a API en marcha.
Uso:  python3 tests/plans_test.py "<ligazón de invitación dun admin novo>"
"""
import io
import sys
import uuid
from datetime import date, timedelta

import httpx
from openpyxl import Workbook

API = "http://localhost:8001/api"
ORIGIN = {"Origin": "http://localhost:4321"}
results = []


def check(name, cond, extra=""):
    results.append(bool(cond))
    print(("  OK  " if cond else "  FAIL") + f" {name} {extra if not cond else ''}")


def client():
    return httpx.Client(base_url=API, headers=ORIGIN)


def accept(token):
    c = client()
    r = c.post("/invitations/accept", json={"token": token, "password": "contrasinal-longo-1", "consent": True})
    assert r.status_code == 204, r.text
    return c


def invite(admin, **body):
    r = admin.post("/invitations/", json=body)
    assert r.status_code == 201, r.text
    return r.json()["link"].split("#", 1)[1]


tag = uuid.uuid4().hex[:6]
admin = accept(sys.argv[1].split("#", 1)[1])
ana = accept(invite(admin, email=f"ana-{tag}@example.com", invited_name="Ana Souto"))
bea = accept(invite(admin, email=f"bea-{tag}@example.com", invited_name="Bea Lojo"))
cris = accept(invite(admin, email=f"cris-{tag}@example.com", invited_name="Cris Vidal"))
nai = accept(invite(admin, email=f"nai-{tag}@example.com", invited_name="Carme Pérez", kind="guardian", minor_name="Uxía"))
coach = accept(invite(admin, email=f"coach-{tag}@example.com", invited_name="Ismael", is_athlete=False, grant_coach=True))
ana_id = ana.get("/auth/me").json()["athletes"][0]["id"]
bea_id = bea.get("/auth/me").json()["athletes"][0]["id"]
cris_id = cris.get("/auth/me").json()["athletes"][0]["id"]
uxia_id = nai.get("/auth/me").json()["athletes"][0]["id"]
for c in (ana, bea, cris, nai):
    c.post("/notifications/read")

# Unha semana futura só para esta proba (para non chocar con outras execucións)
base = date.today() - timedelta(days=date.today().weekday())
week = base + timedelta(weeks=20 + (int(tag, 16) % 100))
W = week.isoformat()
race_day = (week + timedelta(days=5)).isoformat()

print("\n— Permisos")
check("athlete can't list groups", ana.get("/plans/groups").status_code == 403)
check("athlete can't open editor", ana.get(f"/plans/editor?week={W}").status_code == 403)
check("not monday 422", coach.get(f"/plans/editor?week={(week + timedelta(days=1)).isoformat()}").status_code == 422)
r = coach.get(f"/plans/editor?week={W}")
check("empty editor", r.status_code == 200 and r.json() == {"plan": None, "sessions": []}, r.text)
r = ana.get(f"/plans/athlete/{ana_id}?week={W}")
check("no plan yet", r.status_code == 200 and r.json()["plan_id"] is None and r.json()["sessions"] == [], r.text)
check("other adult can't see", bea.get(f"/plans/athlete/{ana_id}?week={W}").status_code == 404)
check("adult can't see minor", ana.get(f"/plans/athlete/{uxia_id}?week={W}").status_code == 404)

print("\n— Plan xeral")
general = {"week_start": W, "scope": "general", "status": "draft", "sessions": [
    {"day": 0, "sport": "bike", "title": "Suave", "duration_min": 30, "content": "Cadencia alta"},
    {"day": 0, "sport": "gym", "content": "2x5-6 rep ao 70 %"},
    {"day": 1, "sport": "swim", "content": "8x100 Z4 / rec. 25″"},
    {"day": 4, "sport": "run", "content": "20′ Z1 a Z2"},
]}
check("athlete can't save", ana.post("/plans/", json=general).status_code == 403)
check("bad sport 422", coach.post("/plans/", json={**general, "sessions": [{"day": 0, "sport": "yoga"}]}).status_code == 422)
check("bad day 422", coach.post("/plans/", json={**general, "sessions": [{"day": 7, "sport": "run"}]}).status_code == 422)
r = coach.post("/plans/", json=general)
d = r.json()
check("draft saved", r.status_code == 200 and d["plan"]["status"] == "draft" and len(d["sessions"]) == 4, r.text)
check("unicode content kept", d["sessions"][2]["content"] == "8x100 Z4 / rec. 25″", d["sessions"][2])
check("positions per day", [(s["day"], s["position"]) for s in d["sessions"]] == [(0, 0), (0, 1), (1, 0), (4, 0)])
gen_id = d["plan"]["id"]
check("draft invisible to athlete", ana.get(f"/plans/athlete/{ana_id}?week={W}").json()["plan_id"] is None)
check("no notification for draft", ana.get("/notifications/").json()["unread"] == 0)

sess = d["sessions"]
upd = {**general, "status": "published", "sessions": [
    {**{k: sess[0][k] for k in ("id", "day", "sport", "title", "duration_min", "content")}, "day": 2},  # movida ao mércores
    {k: sess[2][k] for k in ("id", "day", "sport", "title", "duration_min", "content")},
    {"day": 6, "sport": "run", "content": "10′ Z1 · 10′ Z2 · 10′ Z3"},
]}
r = coach.post("/plans/", json=upd)
d = r.json()
check("published", d["plan"]["status"] == "published" and d["plan"]["published_at"], d["plan"])
check("session moved keeps id", any(s["id"] == sess[0]["id"] and s["day"] == 2 for s in d["sessions"]), d["sessions"])
check("removed sessions gone", len(d["sessions"]) == 3 and not any(s["id"] == sess[1]["id"] for s in d["sessions"]))
swim_id = next(s["id"] for s in d["sessions"] if s["sport"] == "swim")
for who, c in (("ana", ana), ("bea", bea), ("guardian", nai)):
    n = c.get("/notifications/").json()
    check(f"{who} notified", n["unread"] == 1 and n["items"][0]["kind"] == "plan_published" and n["items"][0]["ref_id"] == gen_id, n)
coach.post("/plans/", json={**upd, "sessions": [{k: s[k] for k in ("id", "day", "sport", "title", "duration_min", "content")} for s in d["sessions"]]})
check("republish doesn't re-notify", ana.get("/notifications/").json()["unread"] == 1)

w = ana.get(f"/plans/athlete/{ana_id}?week={W}").json()
check("athlete sees general", w["plan_id"] == gen_id and w["scope"] == "general" and len(w["sessions"]) == 3, w)
check("athlete can mark", w["can_mark"] is True)
check("any day of week → same week", ana.get(f"/plans/athlete/{ana_id}?week={(week + timedelta(days=3)).isoformat()}").json()["plan_id"] == gen_id)
c = coach.get(f"/plans/athlete/{ana_id}?week={W}").json()
check("coach sees but can't mark", c["plan_id"] == gen_id and c["can_mark"] is False)

print("\n— Cambios nun plan publicado")
ana.post("/notifications/read")
cur = coach.get(f"/plans/editor?week={W}").json()["sessions"]
body = {**upd, "sessions": [{k: x[k] for k in ("id", "day", "sport", "title", "duration_min", "content")} for x in cur]}
coach.post("/plans/", json=body)
n = ana.get("/notifications/").json()
check("athlete told about change", n["unread"] == 1 and n["items"][0]["kind"] == "plan_updated"
      and n["items"][0]["week_start"] == W, n["items"][:1])
coach.post("/plans/", json=body)
check("no second unread change notice", ana.get("/notifications/").json()["unread"] == 1)
ana.post("/notifications/read")

print("\n— Feito")
r = ana.post(f"/plans/sessions/{swim_id}/done", json={"athlete_id": ana_id, "rpe": 7, "comment": "Custou"})
check("mark done", r.status_code == 204, r.text)
s = next(x for x in ana.get(f"/plans/athlete/{ana_id}?week={W}").json()["sessions"] if x["id"] == swim_id)
check("done stored", s["done"] and s["rpe"] == 7 and s["comment"] == "Custou", s)
check("bad rpe 422", ana.post(f"/plans/sessions/{swim_id}/done", json={"athlete_id": ana_id, "rpe": 11}).status_code == 422)
check("other adult can't mark for ana", bea.post(f"/plans/sessions/{swim_id}/done", json={"athlete_id": ana_id}).status_code == 403)
check("coach can't mark", coach.post(f"/plans/sessions/{swim_id}/done", json={"athlete_id": ana_id}).status_code == 403)
check("guardian marks minor", nai.post(f"/plans/sessions/{swim_id}/done", json={"athlete_id": uxia_id}).status_code == 204)
check("missing session 404", ana.post("/plans/sessions/999999/done", json={"athlete_id": ana_id}).status_code == 404)
# Editar o plan non borra o feito das sesións que seguen
cur = coach.get(f"/plans/editor?week={W}").json()["sessions"]
coach.post("/plans/", json={**upd, "sessions": [{k: x[k] for k in ("id", "day", "sport", "title", "duration_min", "content")} | ({"content": "8x100 Z4 / rec. 20″"} if x["id"] == swim_id else {}) for x in cur]})
s = next(x for x in ana.get(f"/plans/athlete/{ana_id}?week={W}").json()["sessions"] if x["id"] == swim_id)
check("edit keeps done", s["done"] and s["content"] == "8x100 Z4 / rec. 20″", s)

print("\n— Grupo dunha carreira")
r = ana.post("/races/", json={"name": f"Dúatlon proba {tag}", "race_date": race_day, "place": "Zuia", "zone": "spain", "sport": "duathlon"})
race_id = r.json()["id"]
bea.post(f"/races/{race_id}/attendance", json={"athlete_id": bea_id, "status": "going"})
check("athlete can't create group", ana.post("/plans/groups", json={"race_id": race_id}).status_code == 403)
check("group needs name or race", coach.post("/plans/groups", json={}).status_code == 422)
r = coach.post("/plans/groups", json={"race_id": race_id})
g = r.json()
check("group from race", r.status_code == 201 and g["name"] == f"Dúatlon proba {tag}" and g["member_count"] == 2, r.text)
check("same race → same group", coach.post("/plans/groups", json={"race_id": race_id}).json()["id"] == g["id"])
gid = g["id"]
mem = {m["athlete_id"]: m for m in coach.get(f"/plans/groups/{gid}/members").json()}
check("members from race", mem[ana_id]["in_group"] and mem[ana_id]["from_race"] and mem[bea_id]["in_group"] and not mem[cris_id]["in_group"])
coach.post(f"/plans/groups/{gid}/members", json={"athlete_id": cris_id, "mode": "add"})
r = coach.post(f"/plans/groups/{gid}/members", json={"athlete_id": bea_id, "mode": "exclude"})
mem = {m["athlete_id"]: m for m in r.json()}
check("add + exclude", mem[cris_id]["in_group"] and mem[cris_id]["mode"] == "add" and not mem[bea_id]["in_group"]
      and mem[bea_id]["from_race"], [mem[cris_id], mem[bea_id]])
r = coach.post("/plans/", json={"week_start": W, "scope": "group", "group_id": gid, "status": "published", "sessions": [
    {"day": 5, "sport": "race", "title": "Dúatlon", "content": "15 + 70 + 7"}, {"day": 4, "sport": "rest"}]})
grp_plan = r.json()["plan"]["id"]
check("group plan published", r.status_code == 200, r.text)
w = ana.get(f"/plans/athlete/{ana_id}?week={W}").json()
check("ana gets group plan", w["plan_id"] == grp_plan and w["scope"] == "group" and w["group_name"] == g["name"], w)
check("race week shown", [x["id"] for x in w["races"]] == [race_id], w["races"])
check("ana can't mark general anymore", ana.post(f"/plans/sessions/{swim_id}/done", json={"athlete_id": ana_id}).status_code == 403)
check("cris (manual) gets group", cris.get(f"/plans/athlete/{cris_id}?week={W}").json()["plan_id"] == grp_plan)
check("bea (excluded) gets general", bea.get(f"/plans/athlete/{bea_id}?week={W}").json()["plan_id"] == gen_id)
check("cris notified of group", any(n["kind"] == "plan_published" and n["ref_id"] == grp_plan for n in cris.get("/notifications/").json()["items"]))
coach.post(f"/plans/groups/{gid}/members", json={"athlete_id": bea_id, "mode": "none"})
check("back to automatic", bea.get(f"/plans/athlete/{bea_id}?week={W}").json()["plan_id"] == grp_plan)

print("\n— Individual")
r = coach.post("/plans/", json={"week_start": W, "scope": "athlete", "athlete_id": ana_id, "status": "published",
                                 "sessions": [{"day": 0, "sport": "run", "content": "Só para Ana"}]})
ind = r.json()["plan"]["id"]
check("individual wins", ana.get(f"/plans/athlete/{ana_id}?week={W}").json()["plan_id"] == ind)
check("athlete scope needs athlete", coach.post("/plans/", json={"week_start": W, "scope": "athlete", "sessions": []}).status_code == 422)
lst = coach.get(f"/plans/week?week={W}").json()
check("week list", [p["scope"] for p in lst] == ["general", "group", "athlete"] and lst[2]["athlete_name"] == "Ana Souto", lst)

print("\n— Seguimento")
prog = {p["athlete_id"]: p for p in coach.get(f"/plans/{gen_id}/progress").json()}
check("general recipients", uxia_id in prog and ana_id not in prog and bea_id not in prog, list(prog))
check("uxía done shown", [x["session_id"] for x in prog[uxia_id]["done"]] == [swim_id], prog[uxia_id])
check("athlete can't see progress", ana.get(f"/plans/{gen_id}/progress").status_code == 403)
r = coach.get(f"/plans/{gen_id}/progress.xlsx?lang=gl")
check("export xlsx", r.status_code == 200 and r.content[:2] == b"PK"
      and "seguimento-" in r.headers.get("content-disposition", ""), r.status_code)
from openpyxl import load_workbook
wbx = load_workbook(io.BytesIO(r.content))
ws = wbx["Seguimento"]
names = [ws.cell(row=i, column=1).value for i in range(5, ws.max_row + 1)]
check("export rows", "Uxía" in names and ws.cell(row=4, column=1).value == "Atleta", names)
check("export formula", str(ws.cell(row=5, column=ws.max_column).value).startswith("=COUNTIF("))
check("export comments sheet", wbx["Comentarios"].max_row >= 1)
check("export es", "seguimiento-" in coach.get(f"/plans/{gen_id}/progress.xlsx?lang=es").headers.get("content-disposition", ""))
check("athlete can't export", ana.get(f"/plans/{gen_id}/progress.xlsx").status_code == 403)

print("\n— Importar")
wb = Workbook()
ws = wb.active
ws.append(["Semana do 3 ao 9"])
ws.append(["LUNS", "MARTES", "MÉRCORES", "XOVES", "VENRES", "SÁBADO", "DOMINGO"])
ws.append(["Bici 30´\nsuave\n+\nGym\n2x5", "Natación\n8x100 Z4", None, "Descanso", "Carrera\n20´Z1", "Natación Mar\n2x10´Z1", "Bici Cabra\nRodar 3h"])
buf = io.BytesIO()
wb.save(buf)
r = coach.post("/plans/import", files={"file": ("plan.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
d = r.json()
check("import xlsx", r.status_code == 200 and d["title"] == "Semana do 3 ao 9", r.text)
check("import sessions", [[s["sport"] for s in day] for day in d["days"]] ==
      [["bike", "gym"], ["swim"], [], ["rest"], ["run"], ["swim"], ["bike"]], d["days"])
check("import title/duration", d["days"][0][0]["duration_min"] == 30 and d["days"][5][0]["title"] == "Mar", d["days"][0][0])
check("import bad file", coach.post("/plans/import", files={"file": ("x.txt", b"hola", "text/plain")}).status_code == 422)
check("athlete can't import", ana.post("/plans/import", files={"file": ("plan.xlsx", buf.getvalue(), "x")}).status_code == 403)

print("\n— Borrar")
check("delete group plan", coach.post(f"/plans/{grp_plan}/delete").status_code == 204)
check("ana keeps individual", ana.get(f"/plans/athlete/{ana_id}?week={W}").json()["plan_id"] == ind)
check("delete group", coach.post(f"/plans/groups/{gid}/delete").status_code == 204)
check("cris back to general", cris.get(f"/plans/athlete/{cris_id}?week={W}").json()["plan_id"] == gen_id)
for pid in (ind, gen_id):
    coach.post(f"/plans/{pid}/delete")
check("week empty", coach.get(f"/plans/week?week={W}").json() == [])

print(f"\n{sum(results)}/{len(results)} OK")
sys.exit(0 if all(results) else 1)
