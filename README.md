# Google Sheet History Service

First phase implementation for:
- Configuring Google Sheet access from a web page
- Reading operation history from Google APIs
- Displaying history in a simple web page
- Deploying on a Google Cloud VM with IP allowlist

## 1) Install

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```

Copy env template:

```bash
copy .env.example .env
```

## 2) Required GCP setup

- Enable APIs:
  - Drive Activity API
  - Sheets API (if using audit sheet source)
  - Secret Manager API
- Create a service account and grant:
  - Secret Manager Secret Version Adder
  - Secret Manager Secret Accessor
  - Drive activity read access to target file
- Share target Google Sheet with that service account email.

## 3) Run locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:
- `http://localhost:8000/settings`
- Upload service account JSON, set `sheet_id` and `worksheet_name`
- Click `Validate current config`
- Open `http://localhost:8000/history`

## 4) API endpoints

- `GET /health`
- `GET /settings` (html)
- `POST /settings` (multipart form)
- `POST /settings/validate`
- `GET /api/history?limit=50`
- `GET /history` (html)

## 5) Deploy on GCP VM (recommended: systemd + nginx)

### 5.1 Create VM

```bash
gcloud compute instances create sheet-history-vm \
  --zone=asia-east1-b \
  --machine-type=e2-small \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --tags=http-server
```

Open firewall:

```bash
gcloud compute firewall-rules create allow-http-80 \
  --allow=tcp:80 \
  --target-tags=http-server
```

### 5.2 SSH to VM and install runtime

```bash
gcloud compute ssh sheet-history-vm --zone=asia-east1-b
```

Inside VM:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git
sudo mkdir -p /opt/data-source-parser-service
sudo chown $USER:$USER /opt/data-source-parser-service
```

### 5.3 Deploy app code

```bash
cd /opt/data-source-parser-service
git clone <your-repo-url> .
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- `GCP_PROJECT_ID=...`
- `ALLOWED_IPS=<your_office_or_home_ip>/32,127.0.0.1/32`

### 5.4 Configure systemd

Use template file in repo: `deploy/sheet-history.service`

```bash
sudo cp deploy/sheet-history.service /etc/systemd/system/sheet-history.service
sudo systemctl daemon-reload
sudo systemctl enable sheet-history
sudo systemctl start sheet-history
sudo systemctl status sheet-history
```

### 5.5 Configure nginx reverse proxy

Use template file in repo: `deploy/nginx-sheet-history.conf`

```bash
sudo cp deploy/nginx-sheet-history.conf /etc/nginx/sites-available/sheet-history
sudo ln -sf /etc/nginx/sites-available/sheet-history /etc/nginx/sites-enabled/sheet-history
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

Now open `http://<VM_EXTERNAL_IP>/settings`.

### 5.6 Optional: HTTPS (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d <your-domain>
```

## 6) Docker deployment (optional)

```bash
docker build -t sheet-history-service .
docker run -d --name sheet-history \
  -p 8000:8000 \
  --env-file .env \
  sheet-history-service
```

## Security notes

- Credential JSON is uploaded from UI, then stored in Google Secret Manager.
- Non-secret settings (`sheet_id`, `worksheet_name`, `google_api_key`) are stored in `config/runtime_settings.json`.
- IP access control is enforced by `ALLOWED_IPS`.
