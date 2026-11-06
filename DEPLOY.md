# Despregue da API no Hetzner (servidor de FuelUp-Tri)

Todo isto faise **unha vez**. Os comandos con `sudo` executalos co usuario `deploy` (`ssh hetzner`).

## 0. Snapshot
Antes de nada: Hetzner → servidor → Snapshots → Create. Se algo sae mal, volves atrás nun clic.

## 1. Base de datos
Comproba se xa tes MySQL (FuelUp-Tri seguramente o usa):
```bash
mysql --version
```
Se non está: `sudo apt update && sudo apt install -y mysql-server`.

Crea a base de datos e un usuario **só para o clube** (cambia o contrasinal):
```bash
sudo mysql -e "
CREATE DATABASE triatlon_rianxo CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'triatlon'@'localhost' IDENTIFIED BY 'UN_CONTRASINAL_LONGO';
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE ON triatlon_rianxo.* TO 'triatlon'@'localhost';
FLUSH PRIVILEGES;"
```
Este usuario non pode tocar as táboas de FuelUp-Tri nin modificar o esquema.

## 2. Subir o código (desde o teu PC, na carpeta triatlon-rianxo-api)
```powershell
ssh hetzner "sudo mkdir -p /opt/triatlon-api && sudo chown deploy:deploy /opt/triatlon-api"
scp -r app db deploy requirements.txt .env.example hetzner:/opt/triatlon-api/
```

## 3. Cargar o esquema (no servidor)
```bash
cd /opt/triatlon-api
sudo mysql triatlon_rianxo < db/001_schema.sql
sudo mysql triatlon_rianxo < db/002_procedures_accounts.sql
```

## 4. Python e configuración
```bash
sudo apt install -y python3-venv
cd /opt/triatlon-api
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env        # DATABASE_URL co contrasinal do paso 1; deixa COOKIE_SECURE=true e sen CORS_ORIGINS
chmod 600 .env
```

## 5. Servizo
```bash
sudo cp deploy/triatlon-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now triatlon-api
systemctl status triatlon-api --no-pager | head -5      # active (running)
curl -s localhost:8001/api/health                         # {"ok":true}
```

## 6. Caddy
Substitúe o bloque `triatlon.pdcgsolutions.com` de `/etc/caddy/Caddyfile` polo de `deploy/Caddyfile.triatlon`:
```bash
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak
sudo nano /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile && sudo systemctl reload caddy
curl -s https://triatlon.pdcgsolutions.com/api/health     # {"ok":true}
```

## 7. Primeiro admin
```bash
cd /opt/triatlon-api
venv/bin/python -m app.cli invite --email TEU@EMAIL --name "O teu nome" --admin --coach
```
Abre a ligazón que sae, crea o contrasinal e xa podes convidar a Ismael e ao resto desde **Membros → Administración**.

## Actualizacións posteriores
```powershell
scp -r app hetzner:/opt/triatlon-api/
ssh hetzner "sudo systemctl restart triatlon-api"
```
Se cambian os ficheiros de `db/`, súbeos e volve cargalos (os `.sql` pódense executar varias veces).

## Copias de seguridade
```bash
# Engade ao crontab do deploy (crontab -e): copia diaria ás 4:30
30 4 * * * mysqldump --single-transaction --routines triatlon_rianxo | gzip > /home/deploy/backups/triatlon-$(date +\%F).sql.gz
```
(crea antes `mkdir -p /home/deploy/backups` e un `~/.my.cnf` co usuario de MySQL)
