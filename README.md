# Triatlón Rianxo · API

FastAPI + MySQL con stored procedures, patrón routes → management → repository → queries → SP.

```
app/
  core/            config, BD, seguridade (Argon2id, tokens), auth (cookie de sesión), CSRF
  domains/accounts/
    auth/          login, logout, /me, restablecer contrasinal
    invitations/   invitacións (admin) e aceptalas (público)
    users/         listar contas, activar/desactivar, ligazón de contrasinal (admin)
  domains/members/
    athletes/      perfil do atleta (ver/editar, foto) e directorio de atletas
    races/         calendario: carreiras, vou/quizais, duplicados, lista pública (/api/public/races)
  cli.py           crear a primeira invitación de admin
db/                001–004: esquema e procedementos (cárganse en orde)
deploy/            servizo systemd e bloque de Caddy
tests/flow_test.py    contas e invitacións (45 comprobacións)
tests/profile_test.py perfil, permisos e fotos (54 comprobacións)
tests/races_test.py   calendario, visibilidade e web pública (51 comprobacións)
```

## Seguridade
- Contrasinais con **Argon2id**. Tokens (sesión, invitación, restablecer) aleatorios de 256 bits; na BD só o hash SHA-256.
- Cookie `tr_session`: HttpOnly, Secure, SameSite=Lax, 30 días.
- Invitacións: 7 días, un só uso, por persoa. O token vai despois do `#` na ligazón, así nunca chega a ningún servidor nin rexistro, e a vista previa de WhatsApp non a consome.
- Límite de intentos: 5 fallos por email ou 30 por IP en 15 minutos.
- CSRF: as peticións POST teñen que vir da propia web (`ALLOWED_ORIGINS`).
- Non se pode desactivar o último admin nin a propia conta.

## Contas e menores
- **users** = quen inicia sesión. **athletes** = perfil deportivo.
- Adulto: unha conta co seu propio perfil.
- Escola: a invitación vai ao pai/nai (`kind=guardian`) e crea o perfil do menor xestionado por esa conta.
  Se o pai xa ten conta (segundo fillo), confirma co seu contrasinal e engádese o novo perfil.

## Perfil do atleta e permisos
| Quen mira | Nome, foto, deportes | Nacemento, licenza, chip | Pode editar |
|---|---|---|---|
| O propio atleta, os seus titores, admins | ✓ | ✓ | ✓ |
| Adestradores | ✓ | ✓ | — |
| Outros membros (perfís de adultos) | ✓ | — | — |
| Outros membros (nenos da escola) | — | — | — |

Os permisos decídeos `Athlete_AccessLevel` na BD; a API nunca devolve os campos que non tocan.
Fotos: no disco (`MEDIA_DIR/athletes/`), comprimida no navegador (JPEG 2048 px), gardada como WebP 800×800 sen EXIF, nome aleatorio; sérveas a API só a membros con sesión.

## Calendario
- Calquera membro engade carreiras; editala ou borrala só quen a creou e os admins.
- «Non vou» = sen fila en `race_attendance`. Quen a crea queda apuntado se ten perfil propio.
- As listas de «quen vai» seguen os mesmos permisos ca o perfil: os nenos da escola só os ven familias, adestradores e admins.
- `/api/public/races` (sen sesión, caché 5 min): só carreiras con alguén que marcou «Vou», e só o número de atletas.

## Desenvolvemento local
```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # pon DATABASE_URL, COOKIE_SECURE=false, CORS_ORIGINS=http://localhost:4321, MEDIA_DIR=./media
mysql -u root -p triatlon_rianxo < db/001_schema.sql
mysql -u root -p triatlon_rianxo < db/002_procedures_accounts.sql
mysql -u root -p triatlon_rianxo < db/003_schema_profiles.sql
mysql -u root -p triatlon_rianxo < db/004_procedures_profiles.sql
mysql -u root -p triatlon_rianxo < db/005_schema_races.sql
mysql -u root -p triatlon_rianxo < db/006_procedures_races.sql
mysql -u root -p triatlon_rianxo < db/007_races_price.sql
mysql -u root -p triatlon_rianxo < db/008_athlete_names.sql
mysql -u root -p triatlon_rianxo < db/010_schema_tests.sql
mysql -u root -p triatlon_rianxo < db/011_procedures_tests.sql
mysql -u root -p triatlon_rianxo < db/012_schema_plans.sql
mysql -u root -p triatlon_rianxo < db/013_procedures_plans.sql
# Opcional: carreiras de nov. 2026 a out. 2027 no calendario
mysql -u root -p triatlon_rianxo < db/009_seed_races_2027.sql
uvicorn app.main:app --reload --port 8001
python -m app.cli invite --email ti@example.com --name "O teu nome" --admin --coach
```
Documentación interactiva: http://localhost:8001/api/docs

## Despregue no Hetzner
Ver `DEPLOY.md`.
