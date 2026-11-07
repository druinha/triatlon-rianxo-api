"""Proba de extremo a extremo do perfil do atleta (Fase 2) contra a API en marcha e unha BD de probas.
Uso:  python3 tests/profile_test.py "<ligazón de invitación dun admin novo>" [MEDIA_DIR]
O admin crea o resto de contas. MEDIA_DIR serve para comprobar que os ficheiros se borran do disco.
"""
import io
import sys
import uuid
from pathlib import Path

import httpx
from PIL import Image

API = "http://localhost:8001/api"
ORIGIN = {"Origin": "http://localhost:4321"}
MEDIA = Path(sys.argv[2]) / "athletes" if len(sys.argv) > 2 else None
results = []


def check(name, cond, extra=""):
    results.append(bool(cond))
    print(("  OK  " if cond else "  FAIL") + f" {name} {extra if not cond else ''}")


def client():
    return httpx.Client(base_url=API, headers=ORIGIN)


def accept(token, password="contrasinal-longo-1"):
    c = client()
    r = c.post("/invitations/accept", json={"token": token, "password": password, "consent": True})
    assert r.status_code == 204, r.text
    return c


def invite(admin, **body):
    r = admin.post("/invitations/", json=body)
    assert r.status_code == 201, r.text
    return r.json()["link"].split("#", 1)[1]


def jpeg(w=1200, h=1600, color=(200, 30, 120), exif_gps=True, rotate=False):
    img = Image.new("RGB", (w, h), color)
    exif = Image.Exif()
    if exif_gps:
        exif[0x8825] = {2: (42.0, 39.0, 0.0), 4: (8.0, 49.0, 0.0)}  # GPSInfo
    if rotate:
        exif[0x0112] = 6  # Orientation: rotar 90°
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


def upload(c, athlete_id, data, name="foto.jpg", ctype="image/jpeg"):
    return c.post(f"/athletes/{athlete_id}/photo", files={"photo": (name, data, ctype)})


tag = uuid.uuid4().hex[:6]
admin = accept(sys.argv[1].split("#", 1)[1])
me_admin = admin.get("/auth/me").json()

# Contas: dous atletas adultos, unha nai cun menor e un adestrador que non compite
ana = accept(invite(admin, email=f"ana-{tag}@example.com", invited_name="Ana Souto"))
bea = accept(invite(admin, email=f"bea-{tag}@example.com", invited_name="Bea Lojo"))
nai = accept(invite(admin, email=f"nai-{tag}@example.com", invited_name="Carme Pérez", kind="guardian", minor_name="Uxía"))
coach = accept(invite(admin, email=f"coach-{tag}@example.com", invited_name="Ismael", is_athlete=False, grant_coach=True))
anon = client()

ana_id = ana.get("/auth/me").json()["athletes"][0]["id"]
bea_id = bea.get("/auth/me").json()["athletes"][0]["id"]
uxia_id = nai.get("/auth/me").json()["athletes"][0]["id"]

print("\n— Ver e editar o propio perfil")
p = ana.get(f"/athletes/{ana_id}").json()
check("own profile manage", p["access"] == "manage" and p["can_edit"] is True, p)
body = {"first_name": "  Ana ", "last_name": " Souto   Vidal", "birth_date": "1990-05-12", "license_number": "GAL-1234",
        "chip_code": "ab12cd", "sports": ["triathlon", "running", "running"]}
r = ana.post(f"/athletes/{ana_id}", json=body)
p = r.json()
check("update own profile", r.status_code == 200, r.text)
check("name normalized", p["full_name"] == "Ana Souto Vidal" and p["first_name"] == "Ana" and p["last_name"] == "Souto Vidal", p)
check("chip uppercased", p["chip_code"] == "AB12CD", p)
check("sports deduped", p["sports"] == ["triathlon", "running"], p)
check("birth date saved", p["birth_date"] == "1990-05-12", p)
r = ana.post(f"/athletes/{ana_id}", json={**body, "birth_date": "2999-01-01"})
check("future birth date rejected", r.status_code == 422, r.text)
r = ana.post(f"/athletes/{ana_id}", json={**body, "sports": ["golf"]})
check("unknown sport rejected", r.status_code == 422, r.text)
r = ana.post(f"/athletes/{ana_id}", json={**body, "chip_code": "<script>"})
check("weird chip rejected", r.status_code == 422, r.text)
r = ana.post(f"/athletes/{ana_id}", json={**body, "license_number": "", "chip_code": ""})
check("empty codes become null", r.json()["license_number"] is None and r.json()["chip_code"] is None, r.text)
r = ana.post(f"/athletes/{ana_id}", json={**body, "first_name": "  "})
check("first name required", r.status_code == 422, r.text)
r = ana.post(f"/athletes/{ana_id}", json={**body, "last_name": None})
check("last name optional", r.status_code == 200 and r.json()["full_name"] == "Ana" and r.json()["last_name"] is None, r.text)
r = ana.post(f"/athletes/{ana_id}", json={**body, "nickname": " A   Choupa "})
p = r.json()
check("nickname becomes display name", p["full_name"] == "A Choupa" and p["nickname"] == "A Choupa" and p["first_name"] == "Ana", p)
names = [a["full_name"] for a in bea.get("/athletes/").json()]
check("directory shows nickname", "A Choupa" in names, names)
pb = bea.get(f"/athletes/{ana_id}").json()
check("others see nickname, not real name", pb["full_name"] == "A Choupa" and pb["first_name"] is None and pb["last_name"] is None, pb)
r = ana.post(f"/athletes/{ana_id}", json={**body, "nickname": ""})
check("clearing nickname restores real name", r.json()["full_name"] == "Ana Souto Vidal" and r.json()["nickname"] is None, r.text)
ana.post(f"/athletes/{ana_id}", json=body)

print("\n— Visibilidade")
p = bea.get(f"/athletes/{ana_id}").json()
check("other athlete sees basic", p["access"] == "basic" and p["can_edit"] is False, p)
check("basic hides sensitive", p["birth_date"] is None and p["license_number"] is None and p["chip_code"] is None, p)
check("basic shows name and sports", p["full_name"] == "Ana Souto Vidal" and p["sports"] == ["triathlon", "running"], p)
check("basic hides guardians", p["guardians"] == [], p)
r = bea.post(f"/athletes/{ana_id}", json=body)
check("other athlete cannot edit", r.status_code == 403 and r.json()["detail"] == "profile_forbidden", r.text)
r = bea.get(f"/athletes/{uxia_id}")
check("adult cannot see minor", r.status_code == 404, r.text)
r = bea.post(f"/athletes/{uxia_id}", json=body)
check("adult cannot edit minor (404)", r.status_code == 404, r.text)
ids = {a["id"] for a in bea.get("/athletes/").json()}
check("directory has adults", {ana_id, bea_id} <= ids, ids)
check("directory hides minors from athletes", uxia_id not in ids, ids)
check("unauthenticated 401", anon.get(f"/athletes/{ana_id}").status_code == 401)
check("unknown athlete 404", bea.get("/athletes/99999999").status_code == 404)

print("\n— Titores e adestradores")
p = nai.get(f"/athletes/{uxia_id}").json()
check("guardian manages minor", p["access"] == "manage" and p["is_minor"] is True, p)
check("guardian listed", p["guardians"] == ["Carme Pérez"], p)
r = nai.post(f"/athletes/{uxia_id}", json={"first_name": "Uxía", "last_name": "Pérez", "birth_date": "2015-03-01",
                                           "license_number": "", "chip_code": "", "sports": ["triathlon", "swimming"]})
check("guardian edits minor", r.status_code == 200 and r.json()["full_name"] == "Uxía Pérez", r.text)
p = nai.get(f"/athletes/{bea_id}").json()
check("invited profile name split on the fly", p["full_name"] == "Bea Lojo" and p["first_name"] is None, p)
p = admin.get(f"/athletes/{bea_id}").json()
check("staff sees split name of invited profile", p["first_name"] == "Bea" and p["last_name"] == "Lojo", p)
check("guardian sees basic of adults", nai.get(f"/athletes/{ana_id}").json()["access"] == "basic")
p = coach.get(f"/athletes/{uxia_id}").json()
check("coach sees minor full", p["access"] == "staff" and p["birth_date"] == "2015-03-01" and p["can_edit"] is False, p)
p = coach.get(f"/athletes/{ana_id}").json()
check("coach sees adult chip", p["chip_code"] == "AB12CD", p)
check("coach cannot edit", coach.post(f"/athletes/{ana_id}", json=body).status_code == 403)
ids = {a["id"] for a in coach.get("/athletes/").json()}
check("coach directory includes minors", uxia_id in ids, ids)
r = admin.post(f"/athletes/{ana_id}", json={**body, "license_number": "GAL-9999"})
check("admin edits anyone", r.status_code == 200 and r.json()["license_number"] == "GAL-9999", r.text)

print("\n— Fotos")
r = upload(ana, ana_id, jpeg(rotate=True))
p = r.json()
check("upload photo", r.status_code == 200 and p["photo_file"] and p["photo_file"].endswith(".webp"), r.text)
first = p["photo_file"]
r = bea.get(f"/athletes/{ana_id}/photo")
check("other athlete can view adult photo", r.status_code == 200 and r.headers["content-type"] == "image/webp", r.status_code)
img = Image.open(io.BytesIO(r.content))
check("photo is 800 square webp", img.format == "WEBP" and img.size == (800, 800), (img.format, img.size))
check("photo has no EXIF", not img.getexif(), dict(img.getexif()))
check("photo cache header", "immutable" in r.headers.get("cache-control", ""), r.headers)
check("anon cannot view photo", anon.get(f"/athletes/{ana_id}/photo").status_code == 401)
if MEDIA:
    check("file on disk", (MEDIA / first).is_file())
r = upload(ana, ana_id, jpeg(color=(10, 10, 10)))
second = r.json()["photo_file"]
check("replace photo gives new name", r.status_code == 200 and second != first, r.text)
if MEDIA:
    check("old file deleted", not (MEDIA / first).exists() and (MEDIA / second).is_file())
    before = set(MEDIA.iterdir())
r = upload(bea, ana_id, jpeg())
check("cannot upload to other's profile", r.status_code == 403, r.text)
if MEDIA:
    check("no orphan file after 403", set(MEDIA.iterdir()) == before)
check("ana photo unchanged", ana.get(f"/athletes/{ana_id}").json()["photo_file"] == second)
r = upload(ana, ana_id, b"isto non e unha imaxe", "x.jpg")
check("garbage rejected", r.status_code == 422 and r.json()["detail"] == "image_invalid", r.text)
gif = io.BytesIO(); Image.new("RGB", (200, 200)).save(gif, format="GIF")
r = upload(ana, ana_id, gif.getvalue(), "x.gif", "image/gif")
check("gif rejected", r.status_code == 415, r.text)
r = upload(ana, ana_id, b"0" * (26 * 1024 * 1024))
check("too large rejected", r.status_code == 413 and r.json()["detail"] == "image_too_large", r.text)
png = io.BytesIO(); Image.new("RGBA", (300, 200), (0, 0, 0, 0)).save(png, format="PNG")
r = upload(nai, uxia_id, png.getvalue(), "u.png", "image/png")
check("guardian uploads transparent png", r.status_code == 200, r.text)
check("adult cannot view minor photo", bea.get(f"/athletes/{uxia_id}/photo").status_code == 404)
check("coach can view minor photo", coach.get(f"/athletes/{uxia_id}/photo").status_code == 200)
me = nai.get("/auth/me").json()
check("/me includes photo_file", me["athletes"][0]["photo_file"] == r.json()["photo_file"], me)
r = ana.post(f"/athletes/{ana_id}/photo/delete")
check("delete photo", r.status_code == 200 and r.json()["photo_file"] is None, r.text)
check("deleted photo 404", bea.get(f"/athletes/{ana_id}/photo").status_code == 404)
if MEDIA:
    check("deleted file removed from disk", not (MEDIA / second).exists())
r = httpx.post(f"{API}/athletes/{ana_id}/photo/delete", headers={"Origin": "https://evil.example"}, cookies=ana.cookies)
check("csrf blocked on photo delete", r.status_code == 403, r.text)

print("\n— Contas desactivadas")
users = admin.get("/users/").json()
bea_user = next(u for u in users if u["email"] == f"bea-{tag}@example.com")
admin.post(f"/users/{bea_user['id']}/active", json={"active": False})
# A conta desactivada non entra, pero o seu perfil segue aí: só o oculta se se desactiva o perfil
check("deactivated user logged out", bea.get("/athletes/").status_code == 401)
admin.post(f"/users/{bea_user['id']}/active", json={"active": True})

print(f"\n{sum(results)}/{len(results)} OK")
sys.exit(0 if all(results) else 1)
