# Triatlón Rianxo · API

FastAPI + MySQL con stored procedures, patrón routes → management → repository → queries → SP.

```
app/
  core/            config, BD, seguridade (Argon2id, tokens), auth (cookie de sesión), CSRF
  domains/accounts/
    auth/          login, logout, /me, restablecer contrasinal
    invitations/   invitacións (admin) e aceptalas (público)
    users/         listar contas, activar/desactivar, ligazón de contrasinal (admin)
  cli.py           crear a primeira invitación de admin
db/                001_schema.sql, 002_procedures_accounts.sql
deploy/            servizo systemd e bloque de Caddy
tests/flow_test.py proba de extremo a extremo (45 comprobacións)
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

## Desenvolvemento local
```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # pon DATABASE_URL, COOKIE_SECURE=false, CORS_ORIGINS=http://localhost:4321
mysql -u root -p triatlon_rianxo < db/001_schema.sql
mysql -u root -p triatlon_rianxo < db/002_procedures_accounts.sql
uvicorn app.main:app --reload --port 8001
python -m app.cli invite --email ti@example.com --name "O teu nome" --admin --coach
```
Documentación interactiva: http://localhost:8001/api/docs

## Despregue no Hetzner
Ver `DEPLOY.md`.
