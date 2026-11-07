"""Proba de extremo a extremo dos tests, zonas e avisos (Fase 4, parte 1) contra a API en marcha.
Uso:  python3 tests/athlete_tests_test.py "<ligazón de invitación dun admin novo>"
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


def run_data(totals, hrs=(167, 167, 169, 167, 171, 171)):
    return {"hr_warmup": 106, "hr_start": 106,
            "splits": [{"m": 500 * (i + 1), "total_s": t, "hr": h} for i, (t, h) in enumerate(zip(totals, hrs))]}


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
coach.post("/notifications/read")

print("\n— Acceso")
check("anon 401", anon.get(f"/tests/athlete/{ana_id}").status_code == 401)
r = ana.get(f"/tests/athlete/{ana_id}")
d = r.json()
check("own empty", r.status_code == 200 and d["tests"] == [] and d["zones"] == [] and d["due_days"] == 180, r.text)
check("athlete can't review", d["can_review"] is False)
check("other adult forbidden", bea.get(f"/tests/athlete/{ana_id}").status_code == 403)
check("adult can't see minor", ana.get(f"/tests/athlete/{uxia_id}").status_code == 403)
check("guardian sees minor", nai.get(f"/tests/athlete/{uxia_id}").status_code == 200)
r = coach.get(f"/tests/athlete/{ana_id}")
check("coach sees + can review", r.status_code == 200 and r.json()["can_review"] is True, r.text)
check("missing athlete 404", ana.get("/tests/athlete/999999").status_code in (403, 404))
check("athlete no inbox", ana.get("/tests/inbox").status_code == 403)

print("\n— Validación")
bad = [
    {"kind": "run_3000", "test_date": day(0), "data": run_data([118, 236, 353, 473, 592])},
    {"kind": "run_3000", "test_date": day(0), "data": run_data([118, 236, 353, 350, 592, 709])},
    {"kind": "run_3000", "test_date": day(1), "data": run_data([118, 236, 353, 473, 592, 709])},
    {"kind": "swim_200", "test_date": day(0), "data": {"total_s": 30}},
    {"kind": "bike_ftp20", "test_date": day(0), "data": {"avg_watts": 2000}},
    {"kind": "nope", "test_date": day(0), "data": {}},
]
for i, b in enumerate(bad):
    check(f"invalid {i} → 422", ana.post(f"/tests/athlete/{ana_id}", json=b).status_code == 422)
check("other adult can't create", bea.post(f"/tests/athlete/{ana_id}",
      json={"kind": "swim_200", "test_date": day(0), "data": {"total_s": 182}}).status_code == 403)

print("\n— Carreira 3000")
r = ana.post(f"/tests/athlete/{ana_id}", json={"kind": "run_3000", "test_date": day(-200), "data": run_data([120, 240, 363, 490, 620, 750])})
check("old run test", r.status_code == 201, r.text)
first_run = r.json()["id"]
r = ana.post(f"/tests/athlete/{ana_id}", json={"kind": "run_3000", "test_date": day(-1), "data": run_data([118, 236, 353, 473, 592, 709])})
t = r.json()
check("run test created", r.status_code == 201 and t["status"] == "submitted", r.text)
check("results", t["result_seconds"] == 709 and t["avg_hr"] == 169, t)
check("prev = older test", t["prev"] and t["prev"]["id"] == first_run and t["prev"]["result_seconds"] == 750, t.get("prev"))
z = t["zones"]["provisional"]
check("provisional zones as Isma's table",
      z == {"r1000": 235, "r500": 108, "r400": 88, "r200": 43, "uan": 261, "uae": 294, "easy": 336, "vo2max": None}, z)
check("provisional from this test", t["zones"]["provisional_test_id"] == t["id"] and t["zones"]["confirmed"] is None)
run_id = t["id"]
check("other adult can't read test", bea.get(f"/tests/{run_id}").status_code == 404)
check("athlete can't review", ana.post(f"/tests/{run_id}/review", json={"comment": "x"}).status_code == 403)

print("\n— Avisos ao adestrador")
n = coach.get("/notifications/").json()
check("coach notified twice", n["unread"] == 2 and n["items"][0]["kind"] == "test_submitted"
      and n["items"][0]["ref_id"] == run_id and n["items"][0]["athlete_name"] == "Ana Souto", n)
check("athlete not notified of own", ana.get("/notifications/").json()["unread"] == 0)
inbox = coach.get("/tests/inbox").json()
check("inbox has both, oldest first", [i["id"] for i in inbox if i["athlete_id"] == ana_id] == [first_run, run_id], inbox)

print("\n— Revisión")
zones = dict(z, vo2max=57, uan=262)
check("bad zones 422", coach.post(f"/tests/{run_id}/review", json={"zones": {"r1000": 235}}).status_code == 422)
r = coach.post(f"/tests/{run_id}/review", json={"comment": "Moi ben a regularidade", "zones": zones})
t = r.json()
check("reviewed", r.status_code == 200 and t["status"] == "reviewed" and t["coach_comment"] == "Moi ben a regularidade", r.text)
check("zones confirmed", t["zones"]["confirmed"] == zones and t["zones"]["provisional"] is None, t["zones"])
check("reviewer name", t["reviewed_by_name"] == "Ismael", t.get("reviewed_by_name"))
n = ana.get("/notifications/").json()
check("athlete notified", n["unread"] == 1 and n["items"][0]["kind"] == "test_reviewed" and n["items"][0]["sport"] == "run", n)
coach.post(f"/tests/{run_id}/review", json={"comment": "Moi ben", "zones": zones})
check("re-review doesn't re-notify", ana.get("/notifications/").json()["unread"] == 1)
check("mark read", ana.post("/notifications/read").status_code == 204 and ana.get("/notifications/").json()["unread"] == 0)
check("athlete can't delete reviewed", ana.post(f"/tests/{run_id}/delete").status_code == 403)
r = coach.post(f"/tests/{first_run}/review", json={"comment": None, "zones": None})
check("review keeping zones", r.status_code == 200 and r.json()["zones"]["confirmed"] == zones)

print("\n— Natación e bici")
r = ana.post(f"/tests/athlete/{ana_id}", json={"kind": "swim_200", "test_date": day(0), "data": {"total_s": 182, "hr": 160}})
t = r.json()
check("swim zones", r.status_code == 201 and t["zones"]["provisional"] ==
      {"z1": 104, "z2": 99, "z3": 96, "z4": 94, "z5": 91, "z6": [87, 89], "s50": 38, "s25": 17}, t)
r = ana.post(f"/tests/athlete/{ana_id}", json={"kind": "bike_ftp20", "test_date": day(0), "data": {"avg_watts": 263}})
t = r.json()
check("bike ftp zones", r.status_code == 201 and t["zones"]["provisional"]["ftp"] == 250
      and t["zones"]["provisional"]["z4"] == [228, 262], t)
bike_ftp = t["id"]
r = ana.post(f"/tests/athlete/{ana_id}", json={"kind": "bike_climb", "test_date": day(0), "data": {"climb": "Curota", "total_s": 1500}})
t = r.json()
check("climb no zones change", r.status_code == 201 and t["result_seconds"] == 1500
      and t["zones"]["provisional_test_id"] == bike_ftp, t)
check("climb can't confirm zones", coach.post(f"/tests/{t['id']}/review", json={"zones": {"ftp": 1}}).status_code == 422)
check("athlete deletes own submitted", ana.post(f"/tests/{t['id']}/delete").status_code == 204)
check("deleted gone", ana.get(f"/tests/{t['id']}").status_code == 404)
r = ana.post(f"/tests/athlete/{ana_id}", json={"kind": "bike_hr20", "test_date": day(0), "data": {"avg_hr": 170}})
check("bike hr replaces provisional", r.json()["zones"]["provisional_kind"] == "bike_hr20"
      and r.json()["zones"]["provisional"]["lthr"] == 162, r.json()["zones"])
d = ana.get(f"/tests/athlete/{ana_id}").json()
check("list 5 tests", len(d["tests"]) == 5 and d["tests"][0]["test_date"] >= d["tests"][-1]["test_date"], len(d["tests"]))
check("zones per sport ordered", [x["sport"] for x in d["zones"]] == ["swim", "bike", "run"], d["zones"])

print("\n— Zonas a man e menores")
check("athlete can't set zones", ana.post(f"/tests/athlete/{ana_id}/zones", json={"kind": "swim_200", "values": {}}).status_code == 403)
check("coach bad zones 422", coach.post(f"/tests/athlete/{ana_id}/zones", json={"kind": "swim_200", "values": {"z1": 1}}).status_code == 422)
sw = {"z1": 105, "z2": 100, "z3": 97, "z4": 95, "z5": 92, "z6": [88, 90], "s50": 39, "s25": 18}
r = coach.post(f"/tests/athlete/{ana_id}/zones", json={"kind": "swim_200", "values": sw})
swim = next(x for x in r.json() if x["sport"] == "swim")
check("coach sets swim zones", r.status_code == 200 and swim["confirmed"] == sw and swim["provisional"] is not None, swim)
r = nai.post(f"/tests/athlete/{uxia_id}", json={"kind": "swim_200", "test_date": day(0), "data": {"total_s": 240}})
check("guardian adds minor test", r.status_code == 201, r.text)
minor_test = r.json()["id"]
check("adult can't read minor test", ana.get(f"/tests/{minor_test}").status_code == 404)
coach.post(f"/tests/{minor_test}/review", json={"comment": "Ben", "zones": None})
check("guardian notified", any(i["kind"] == "test_reviewed" for i in nai.get("/notifications/").json()["items"]))

print("\n— Lembranzas")
due = coach.get("/tests/due").json()
mine = {(x["athlete_id"], x["sport"]) for x in due}
check("bea due swim+run, not bike", (bea_id, "swim") in mine and (bea_id, "run") in mine and (bea_id, "bike") not in mine)
check("ana not due", not any(a == ana_id for a, _ in mine), [x for x in due if x["athlete_id"] == ana_id])
check("athlete can't list due", ana.get("/tests/due").status_code == 403)
check("remind", coach.post("/tests/remind", json={"athlete_id": bea_id, "sport": "swim"}).status_code == 204)
coach.post("/tests/remind", json={"athlete_id": bea_id, "sport": "swim"})
n = bea.get("/notifications/").json()
check("bea reminded once", n["unread"] == 1 and n["items"][0]["kind"] == "test_reminder" and n["items"][0]["sport"] == "swim", n)
due = coach.get("/tests/due").json()
check("reminded_at shown", next(x for x in due if x["athlete_id"] == bea_id and x["sport"] == "swim")["reminded_at"])
check("remind missing athlete 404", coach.post("/tests/remind", json={"athlete_id": 999999, "sport": "swim"}).status_code == 404)

print(f"\n{sum(results)}/{len(results)} OK")
sys.exit(0 if all(results) else 1)
