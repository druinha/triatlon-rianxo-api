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
  cli.py           crear a primeira invitación de admin
db/                001–004: esquema e procedementos (cárganse en orde)
deploy/            servizo systemd e bloque de Caddy
tests/flow_test.py    contas e invitacións (45 comprobacións)
tests/profile_test.py perfil, permisos e fotos (54 comprobacións)
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

## Desenvolvemento local
```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # pon DATABASE_URL, COOKIE_SECURE=false, CORS_ORIGINS=http://localhost:4321, MEDIA_DIR=./media
mysql -u root -p triatlon_rianxo < db/001_schema.sql
mysql -u root -p triatlon_rianxo < db/002_procedures_accounts.sql
mysql -u root -p triatlon_rianxo < db/003_schema_profiles.sql
mysql -u root -p triatlon_rianxo < db/004_procedures_profiles.sql
uvicorn app.main:app --reload --port 8001
python -m app.cli invite --email ti@example.com --name "O teu nome" --admin --coach
```
Documentación interactiva: http://localhost:8001/api/docs

## Despregue no Hetzner
Ver `DEPLOY.md`.
