"""Proba de extremo a extremo contra a API en marcha (localhost:8001) e unha BD de probas.
Uso:  python3 tests/flow_test.py "<ligazón de invitación do admin>"
"""
import sys

import httpx

API = "http://localhost:8001/api"
ORIGIN = {"Origin": "http://localhost:4321"}
results = []


def check(name, cond, extra=""):
    results.append(cond)
    print(("  OK  " if cond else "  FAIL") + f" {name} {extra if not cond else ''}")


def client():
    return httpx.Client(base_url=API, headers=ORIGIN)


admin_token = sys.argv[1].split("#", 1)[1]

# 1. Admin acepta a súa invitación
a = client()
r = a.post("/invitations/check", json={"token": admin_token})
check("check admin invitation", r.status_code == 200 and r.json()["email_registered"] is False, r.text)
r = a.post("/invitations/accept", json={"token": admin_token, "password": "curto", "consent": True})
check("password too short rejected", r.status_code == 422 and r.json()["detail"] == "password_too_short", r.text)
r = a.post("/invitations/accept", json={"token": admin_token, "password": "contrasinal-longo-1", "consent": False})
check("consent required", r.status_code == 422 and r.json()["detail"] == "consent_required", r.text)
r = a.post("/invitations/accept", json={"token": admin_token, "password": "contrasinal-longo-1", "consent": True, "lang": "gl"})
check("admin accepts invitation", r.status_code == 204, r.text)
check("session cookie set", "tr_session" in a.cookies)
me = a.get("/auth/me").json()
check("me has admin+coach+athlete", set(me["roles"]) == {"admin", "coach", "athlete"}, me)
check("me has own athlete profile", len(me["athletes"]) == 1 and me["athletes"][0]["is_minor"] is False, me)
r = a.post("/invitations/accept", json={"token": admin_token, "password": "contrasinal-longo-1", "consent": True})
check("invitation cannot be reused", r.status_code == 410 and r.json()["detail"] == "invitation_used", r.text)

# 2. CSRF
r = httpx.post(f"{API}/invitations/", headers={"Origin": "https://evil.example"}, cookies=a.cookies, json={})
check("bad origin blocked", r.status_code == 403 and r.json()["detail"] == "bad_origin", r.text)

# 3. Admin invita a un atleta adulto
r = a.post("/invitations/", json={"email": "Atleta@Example.com", "invited_name": "Yago Lijó", "lang": "es"})
check("create athlete invitation", r.status_code == 201 and "/es/miembros/invitacion/#" in r.json()["link"], r.text)
athlete_token = r.json()["link"].split("#", 1)[1]
check("email normalized lowercase", r.json()["email"] == "atleta@example.com", r.text)

# 4. Non admin non pode crear invitacións
b = client()
r = b.post("/invitations/accept", json={"token": athlete_token, "password": "outro-contrasinal", "consent": True, "lang": "es"})
check("athlete accepts", r.status_code == 204, r.text)
me_b = b.get("/auth/me").json()
check("athlete roles", me_b["roles"] == ["athlete"] and me_b["lang"] == "es", me_b)
r = b.post("/invitations/", json={"email": "x@example.com", "invited_name": "X"})
check("athlete cannot create invitations", r.status_code == 403, r.text)
r = b.get("/users/")
check("athlete cannot list users", r.status_code == 403, r.text)

# 5. Titor con dous fillos (segunda invitación usa a conta existente)
r = a.post("/invitations/", json={"email": "nai@example.com", "invited_name": "María Pérez", "kind": "guardian", "minor_name": "Lucía"})
check("create guardian invitation", r.status_code == 201, r.text)
g1 = r.json()["link"].split("#", 1)[1]
r = a.post("/invitations/", json={"email": "nai@example.com", "invited_name": "María Pérez", "kind": "guardian"})
check("guardian requires minor_name", r.status_code == 422, r.text)
c = client()
r = c.post("/invitations/accept", json={"token": g1, "password": "nai-contrasinal", "consent": True})
check("guardian accepts", r.status_code == 204, r.text)
r = a.post("/invitations/", json={"email": "nai@example.com", "invited_name": "María Pérez", "kind": "guardian", "minor_name": "Martín"})
g2 = r.json()["link"].split("#", 1)[1]
d = client()
info = d.post("/invitations/check", json={"token": g2}).json()
check("second invite shows email_registered", info["email_registered"] is True, info)
r = d.post("/invitations/accept", json={"token": g2, "password": "mal"})
check("existing user wrong password", r.status_code == 401, r.text)
r = d.post("/invitations/accept", json={"token": g2, "password": "nai-contrasinal"})
check("existing user accepts 2nd child", r.status_code == 204, r.text)
me_d = d.get("/auth/me").json()
names = sorted(x["full_name"] for x in me_d["athletes"])
check("guardian manages 2 minors", names == ["Lucía", "Martín"] and all(x["is_minor"] for x in me_d["athletes"]), me_d)
check("guardian role only", me_d["roles"] == ["guardian"], me_d)

# 6. Login, logout e límite de intentos
e = client()
r = e.post("/auth/login", json={"email": "atleta@example.com", "password": "outro-contrasinal"})
check("login ok", r.status_code == 204 and "tr_session" in e.cookies, r.text)
r = e.post("/auth/logout")
check("logout", r.status_code == 204, r.text)
check("me after logout 401", e.get("/auth/me").status_code == 401)
for i in range(5):
    e.post("/auth/login", json={"email": "atleta@example.com", "password": f"mal-{i}"})
r = e.post("/auth/login", json={"email": "atleta@example.com", "password": "outro-contrasinal"})
check("rate limit after 5 failures", r.status_code == 429, r.text)
r = e.post("/auth/login", json={"email": "non-existe@example.com", "password": "x"})
check("unknown email generic 401", r.status_code == 401 and r.json()["detail"] == "invalid_credentials", r.text)

# 7. Restablecer contrasinal (ligazón do admin)
users = a.get("/users/").json()
yago = next(u for u in users if u["email"] == "atleta@example.com")
maria = next(u for u in users if u["email"] == "nai@example.com")
check("users list minors", sorted(maria["minors"]) == ["Lucía", "Martín"], maria)
r = a.post(f"/users/{yago['id']}/reset-link", json={"lang": "gl"})
check("reset link created", r.status_code == 200 and "/membros/restablecer/#" in r.json()["link"], r.text)
rt = r.json()["link"].split("#", 1)[1]
f = client()
check("reset check", f.post("/auth/reset/check", json={"token": rt}).status_code == 200)
r = f.post("/auth/reset/complete", json={"token": rt, "password": "contrasinal-novo-9"})
check("reset complete logs in", r.status_code == 204 and f.get("/auth/me").status_code == 200, r.text)
check("old session of athlete closed", b.get("/auth/me").status_code == 401)
r = f.post("/auth/reset/complete", json={"token": rt, "password": "outro-mais"})
check("reset token single use", r.status_code == 410, r.text)

# 8. Desactivar conta
admin_id = me["user_id"]
r = a.post(f"/users/{admin_id}/active", json={"active": False})
check("cannot deactivate self", r.status_code == 400, r.text)
r = a.post(f"/users/{yago['id']}/active", json={"active": False})
check("deactivate athlete", r.status_code == 204, r.text)
check("deactivated session killed", f.get("/auth/me").status_code == 401)
g = client()
r = g.post("/auth/login", json={"email": "atleta@example.com", "password": "contrasinal-novo-9"})
check("deactivated cannot login", r.status_code == 403 and r.json()["detail"] == "account_disabled", r.text)
a.post(f"/users/{yago['id']}/active", json={"active": True})

# 9. Revogar e renovar
r = a.post("/invitations/", json={"email": "revogar@example.com", "invited_name": "Proba"})
inv = r.json()
r = a.post(f"/invitations/{inv['id']}/revoke")
check("revoke", r.status_code == 200 and r.json()["status"] == "revoked", r.text)
old = inv["link"].split("#", 1)[1]
check("revoked token rejected", client().post("/invitations/check", json={"token": old}).status_code == 410)
r = a.post(f"/invitations/{inv['id']}/renew", json={"lang": "gl"})
check("renew gives new link", r.status_code == 200 and r.json()["link"] != inv["link"], r.text)
new = r.json()["link"].split("#", 1)[1]
check("old token dead after renew", client().post("/invitations/check", json={"token": old}).status_code == 404)
check("new token valid", client().post("/invitations/check", json={"token": new}).status_code == 200)
used_id = next(i["id"] for i in a.get("/invitations/").json() if i["email"] == "atleta@example.com")
check("cannot renew used invitation", a.post(f"/invitations/{used_id}/renew", json={}).status_code == 409)
statuses = {i["email"]: i["status"] for i in a.get("/invitations/").json()}
check("list statuses", statuses["ismael@example.com"] == "used" and statuses["revogar@example.com"] == "pending", statuses)

print(f"\n{sum(results)}/{len(results)} OK")
sys.exit(0 if all(results) else 1)
