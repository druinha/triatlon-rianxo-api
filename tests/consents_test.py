"""Proba de extremo a extremo dos consentimentos (adestramento e imaxe) contra a API en marcha.
Uso:  python3 tests/consents_test.py "<ligazón de invitación dun admin novo>"
"""
import sys
import uuid
from datetime import date

import httpx

API = "http://localhost:8001/api"
ORIGIN = {"Origin": "http://localhost:4321"}
results = []


def check(name, cond, extra=""):
    results.append(bool(cond))
    print(("  OK  " if cond else "  FAIL") + f" {name} {extra if not cond else ''}")


def accept(token):
    c = httpx.Client(base_url=API, headers=ORIGIN)
    r = c.post("/invitations/accept", json={"token": token, "password": "contrasinal-longo-1", "consent": True})
    assert r.status_code == 204, r.text
    return c


def invite(admin, **body):
    r = admin.post("/invitations/", json=body)
    assert r.status_code == 201, r.text
    return r.json()["link"].split("#", 1)[1]


ALL = {"training": True, "img_web": True, "img_social": True, "img_whatsapp": True, "img_print": True}
tag = uuid.uuid4().hex[:6]
admin = accept(sys.argv[1].split("#", 1)[1])
ana = accept(invite(admin, email=f"ana-{tag}@example.com", invited_name="Ana Souto"))
nai = accept(invite(admin, email=f"nai-{tag}@example.com", invited_name="Carme Pérez", kind="guardian", minor_name="Uxía"))
coach = accept(invite(admin, email=f"coach-{tag}@example.com", invited_name="Ismael", is_athlete=False, grant_coach=True))
ana_id = ana.get("/auth/me").json()["athletes"][0]["id"]
uxia_id = nai.get("/auth/me").json()["athletes"][0]["id"]

print("\n— Pendentes ao entrar")
me = ana.get("/auth/me").json()
check("new account has pending", me["consents_pending"] is True and me["athletes"][0]["consent_pending"] is True, me)
check("training false by default", me["athletes"][0]["training"] is False, me)
check("coach without athlete: nothing pending", coach.get("/auth/me").json()["consents_pending"] is False)
mine = ana.get("/consents/mine").json()
check("mine lists own", [m["athlete_id"] for m in mine] == [ana_id] and mine[0]["pending"], mine)

print("\n— Permisos")
check("adult can't set other's", ana.post(f"/consents/{uxia_id}", json=ALL).status_code == 403)
check("coach can't set", coach.post(f"/consents/{ana_id}", json=ALL).status_code == 403)
check("admin can't set", admin.post(f"/consents/{ana_id}", json=ALL).status_code == 403)
check("athlete can't list staff", ana.get("/consents/staff").status_code == 403)
check("missing field 422", ana.post(f"/consents/{ana_id}", json={"training": True}).status_code == 422)

print("\n— Sen consentimento de adestramento")
test = {"kind": "run_3000", "test_date": date.today().isoformat(),
        "data": {"hr_warmup": 106, "hr_start": 106,
                 "splits": [{"m": 500 * (i + 1), "total_s": t, "hr": 167} for i, t in enumerate([118, 236, 353, 473, 592, 709])]}}
r = ana.post(f"/tests/athlete/{ana_id}", json=test)
check("test blocked", r.status_code == 403 and r.json()["detail"] == "training_consent_required", r.text)

print("\n— Gardar")
r = ana.post(f"/consents/{ana_id}", json=ALL)
check("athlete sets own", r.status_code == 200 and r.json()["row"]["training"] is True and not r.json()["row"]["pending"], r.text)
me = ana.get("/auth/me").json()
check("no longer pending", me["consents_pending"] is False and me["athletes"][0]["training"] is True, me)
r = nai.post(f"/consents/{uxia_id}", json={**ALL, "img_social": False, "img_whatsapp": False})
check("guardian sets minor's", r.status_code == 200 and r.json()["row"]["img_social"] is False, r.text)
r = ana.post(f"/tests/athlete/{ana_id}", json=test)
check("test allowed now", r.status_code == 201, r.text)

print("\n— Lista de staff")
rows = {x["athlete_id"]: x for x in coach.get("/consents/staff").json()}
check("coach sees uxía no social", rows[uxia_id]["img_social"] is False and rows[uxia_id]["img_web"] is True, rows.get(uxia_id))
check("admin sees list", admin.get("/consents/staff").status_code == 200)

print("\n— Retirar")
r = ana.post(f"/consents/{ana_id}", json={**ALL, "training": False})
check("withdraw wipes", r.status_code == 200 and r.json()["wiped"] is True, r.text)
t = ana.get(f"/tests/athlete/{ana_id}").json()
check("tests gone", t["tests"] == [], t)
r = ana.post(f"/consents/{ana_id}", json={**ALL, "training": False})
check("second withdraw no wipe", r.json()["wiped"] is False, r.text)

print(f"\n{sum(results)}/{len(results)} OK")
sys.exit(0 if all(results) else 1)
