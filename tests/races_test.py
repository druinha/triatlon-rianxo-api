"""Proba de extremo a extremo do calendario (Fase 3) contra a API en marcha e unha BD de probas.
Uso:  python3 tests/races_test.py "<ligazón de invitación dun admin novo>"
"""
import sys
import uuid
from datetime import date, timedelta

import httpx

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


def day(n):
    return (date.today() + timedelta(days=n)).isoformat()


tag = uuid.uuid4().hex[:6]
admin = accept(sys.argv[1].split("#", 1)[1])
ana = accept(invite(admin, email=f"ana-{tag}@example.com", invited_name="Ana Souto"))
bea = accept(invite(admin, email=f"bea-{tag}@example.com", invited_name="Bea Lojo"))
nai = accept(invite(admin, email=f"nai-{tag}@example.com", invited_name="Carme Pérez", kind="guardian", minor_name="Uxía"))
coach = accept(invite(admin, email=f"coach-{tag}@example.com", invited_name="Ismael", is_athlete=False, grant_coach=True))
anon = client()
ana_id = ana.get("/auth/me").json()["athletes"][0]["id"]
bea_id = bea.get("/auth/me").json()["athletes"][0]["id"]
uxia_id = nai.get("/auth/me").json()["athletes"][0]["id"]

race = {"name": "Media Maratón de Vilagarcía", "race_date": day(20), "start_time": "10:30", "place": "Vilagarcía",
        "zone": "galicia", "sport": "running", "distances": " 21 km ,10 km,, ", "official_url": "https://example.com/mm"}

print("\n— Crear")
r = ana.post("/races/", json=race)
d = r.json()
check("create race", r.status_code == 201, r.text)
rid = d["id"]
check("creator auto-joined", [a["athlete_id"] for a in d["attendees"]] == [ana_id] and d["attendees"][0]["status"] == "going", d)
check("creator can edit", d["can_edit"] is True)
check("time and distances normalized", d["start_time"] == "10:30" and d["distances"] == "21 km, 10 km", d)
r = bea.post("/races/", json={**race, "name": "Trail do Trega", "race_date": day(27), "sport": "trail", "join": False,
                              "start_time": None, "distances": None, "official_url": None})
trail = r.json()
check("create without joining", r.status_code == 201 and trail["attendees"] == [], r.text)
r = coach.post("/races/", json={**race, "name": "Duatlón de Zuia", "race_date": day(90), "sport": "duathlon", "zone": "spain"})
zuia = r.json()
check("coach without profile creates, no attendance", r.status_code == 201 and zuia["attendees"] == [], r.text)
check("old date rejected", ana.post("/races/", json={**race, "race_date": day(-400)}).status_code == 422)
check("bad url rejected", ana.post("/races/", json={**race, "official_url": "non-é-url"}).status_code == 422)
check("bad time rejected", ana.post("/races/", json={**race, "start_time": "25:00"}).status_code == 422)
check("unknown sport rejected", ana.post("/races/", json={**race, "sport": "golf"}).status_code == 422)

print("\n— Duplicados")
names = [x["name"] for x in bea.get("/races/similar", params={"q": "maraton VILA"}).json()]
check("similar ignores case and accents", "Media Maratón de Vilagarcía" in names, names)
names = [x["name"] for x in bea.get("/races/similar", params={"q": "xx", "date": day(27)}).json()]
check("similar by same date", names == ["Trail do Trega"], names)
check("LIKE wildcards escaped", bea.get("/races/similar", params={"q": "%%%"}).json() == [])

print("\n— Vou / Quizais / Non vou")
r = bea.post(f"/races/{rid}/attendance", json={"athlete_id": bea_id, "status": "going", "distance": "10 km", "registered": True})
me = next(a for a in r.json()["attendees"] if a["athlete_id"] == bea_id)
check("bea going registered", r.status_code == 200 and me["registered"] is True and me["distance"] == "10 km", r.text)
r = bea.post(f"/races/{rid}/attendance", json={"athlete_id": bea_id, "status": "maybe", "registered": True})
me = next(a for a in r.json()["attendees"] if a["athlete_id"] == bea_id)
check("maybe clears registered", me["status"] == "maybe" and me["registered"] is False, me)
r = bea.post(f"/races/{rid}/attendance", json={"athlete_id": ana_id, "status": "none"})
check("cannot change someone else", r.status_code == 403 and r.json()["detail"] == "race_forbidden", r.text)
r = bea.post(f"/races/{rid}/attendance", json={"athlete_id": uxia_id, "status": "going"})
check("adult cannot touch minor", r.status_code == 403, r.text)
r = nai.post(f"/races/{rid}/attendance", json={"athlete_id": uxia_id, "status": "going"})
check("guardian sets minor going", r.status_code == 200, r.text)
check("attendance on missing race 404", bea.post("/races/99999999/attendance", json={"athlete_id": bea_id, "status": "going"}).status_code == 404)

print("\n— Quen ve que")
d = bea.get(f"/races/{rid}").json()
ids = [a["athlete_id"] for a in d["attendees"]]
check("adult does not see minor in attendees", uxia_id not in ids and ana_id in ids, ids)
check("adult counts exclude minor", d["going_count"] == 1 and d["maybe_count"] == 1, d)
d = coach.get(f"/races/{rid}").json()
check("coach sees minor", uxia_id in [a["athlete_id"] for a in d["attendees"]] and d["going_count"] == 2, d)
d = nai.get(f"/races/{rid}").json()
mine = [a for a in d["attendees"] if a["is_mine"]]
check("guardian sees own kid as mine", [a["athlete_id"] for a in mine] == [uxia_id], mine)
lst = bea.get("/races/").json()
row = next(x for x in lst if x["id"] == rid)
check("list who hides minor", uxia_id not in [w["id"] for w in row["who"]] and row["going_count"] == 1, row)
check("list mine shows my status", row["mine"] == [{"athlete_id": bea_id, "status": "maybe"}], row["mine"])
check("list sorted by date", [x["id"] for x in lst if x["id"] in (rid, trail["id"], zuia["id"])] == [rid, trail["id"], zuia["id"]])
check("mine filter", [x["id"] for x in bea.get("/races/", params={"mine": True}).json()] == [rid])
check("coach mine empty", coach.get("/races/", params={"mine": True}).json() == [])
check("guardian mine via kid", rid in [x["id"] for x in nai.get("/races/", params={"mine": True}).json()])
check("unauthenticated 401", anon.get("/races/").status_code == 401)

print("\n— Web pública")
r = anon.get("/public/races")
pub = r.json()
check("public works without session", r.status_code == 200, r.text)
p = next((x for x in pub if x["id"] == rid), None)
check("public counts everyone incl. minor", p and p["going_count"] == 2, p)
check("public has no names", p and "who" not in p and "attendees" not in p, p)
check("public hides races nobody is going to", trail["id"] not in [x["id"] for x in pub] and zuia["id"] not in [x["id"] for x in pub])
check("public cache header", "max-age=300" in r.headers.get("cache-control", ""))

print("\n— Editar e borrar")
r = bea.post(f"/races/{rid}", json={**race, "place": "Outro sitio"})
check("non-creator cannot edit", r.status_code == 403, r.text)
r = ana.post(f"/races/{rid}", json={**race, "place": "Vilagarcía de Arousa"})
check("creator edits", r.status_code == 200 and r.json()["place"] == "Vilagarcía de Arousa", r.text)
r = admin.post(f"/races/{trail['id']}", json={**race, "name": "Trail do Trega", "race_date": day(28), "sport": "trail"})
check("admin edits anyone's race", r.status_code == 200 and r.json()["race_date"] == day(28), r.text)
check("csrf on race edit", httpx.post(f"{API}/races/{rid}", headers={"Origin": "https://evil.example"}, cookies=ana.cookies, json=race).status_code == 403)

print("\n— Carreiras no perfil")
past = ana.post("/races/", json={**race, "name": "Carreira pasada", "race_date": day(-10)}).json()
lst = bea.get(f"/races/athlete/{ana_id}").json()
check("ana upcoming first then past", [x["id"] for x in lst] == [rid, past["id"]], [x["name"] for x in lst])
check("past flagged", lst[1]["is_past"] is True and lst[0]["is_past"] is False)
check("viewer_status is bea's own", lst[0]["viewer_status"] == "maybe" and lst[1]["viewer_status"] is None, lst)
check("adult cannot list minor's races", bea.get(f"/races/athlete/{uxia_id}").json() == [])
check("guardian lists kid's races", [x["id"] for x in nai.get(f"/races/athlete/{uxia_id}").json()] == [rid])
bea.post(f"/races/{past['id']}/attendance", json={"athlete_id": bea_id, "status": "maybe"})
check("past maybe not in history", past["id"] not in [x["id"] for x in bea.get(f"/races/athlete/{bea_id}").json()])
check("past races not in calendar", past["id"] not in [x["id"] for x in bea.get("/races/").json()])
r = bea.post(f"/races/{rid}/attendance", json={"athlete_id": bea_id, "status": "none"})
check("none removes", bea_id not in [a["athlete_id"] for a in r.json()["attendees"]])

print("\n— Borrar")
check("non-creator cannot delete", bea.post(f"/races/{rid}/delete").status_code == 403)
check("creator deletes", ana.post(f"/races/{rid}/delete").status_code == 204)
check("deleted race 404", bea.get(f"/races/{rid}").status_code == 404)
check("deleted race gone from kid's list", nai.get(f"/races/athlete/{uxia_id}").json() == [])

print(f"\n{sum(results)}/{len(results)} OK")
sys.exit(0 if all(results) else 1)
