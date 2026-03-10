# VPS Setup Guide for Trinity Bot

This guide helps an AI agent set up the Trinity bot on a VPS with cron jobs for the bot and Nginx for the dashboard.

## Prerequisites

- VPS with Ubuntu/Debian
- Root or sudo access
- Domain name (optional, for SSL)
- Bot tokens already configured in environment

---

## Step 1: Upload Files

```bash
# Create directory
sudo mkdir -p /opt/trinity
cd /opt/trinity

# Upload the trinity/ folder contents
# (bot/, dashboard/, docs/)
```

---

## Step 2: Setup Bot Dependencies

```bash
cd /opt/trinity/bot

# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync
```

---

## Step 3: Setup Dashboard Dependencies

```bash
cd /opt/trinity/dashboard

# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies  
uv sync
```

---

## Step 4: Configure Cron for Bot

```bash
# Open crontab
crontab -e

# Add this line (runs every 1 minutes)
*/1 * * * * cd /opt/trinity/bot && /root/.local/bin/uv run python runner.py >> /var/log/trinity.log 2>&1
```

To verify:
```bash
# Check if cron is running
systemctl status cron

# View logs
tail -f /var/log/trinity.log
```

---

## Step 5: Setup Dashboard Service

Create `/etc/systemd/system/trinity-dashboard.service`:

```ini
[Unit]
Description=Trinity Dashboard
After=network.target

[Service]
Type=notify
WorkingDirectory=/opt/trinity/dashboard
ExecStart=/root/.local/bin/uv run gunicorn -w 4 -b 127.0.0.1:8080 app:app
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

Then:
```bash
load
sudo systemctlsudo systemctl daemon-re enable trinity-dashboard
sudo systemctl start trinity-dashboard
sudo systemctl status trinity-dashboard
```

---

## Step 6: Setup Nginx with Basic Auth

### 6.1 Install Required Packages

```bash
sudo apt update
sudo apt install apache2-utils nginx certbot python3-certbot-nginx
```

### 6.2 Create Password File

```bash
sudo htpasswd -c /etc/nginx/.htpasswd admin
# Enter password when prompted
```

### 6.3 Create Nginx Config

Create `/etc/nginx/sites-available/trinity`:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Basic Auth
        auth_basic "Trinity Dashboard";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

### 6.4 Enable and Restart

```bash
sudo ln -s /etc/nginx/sites-available/trinity /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Step 7: (Optional) HTTPS with Let's Encrypt

```bash
sudo certbot --nginx -d your-domain.com
# Follow prompts
# Choose "Secure" to redirect HTTP to HTTPS
```

---

## Verification Commands

| Check | Command |
|-------|---------|
| Bot running | `tail -f /var/log/trinity.log` |
| Dashboard status | `systemctl status trinity-dashboard` |
| Dashboard logs | `journalctl -u trinity-dashboard -f` |
| Nginx status | `sudo systemctl status nginx` |
| Dashboard via curl | `curl -u admin:password http://127.0.0.1:8080/api/health` |

---

## Troubleshooting

### Dashboard not starting
```bash
# Check for port conflicts
sudo lsof -i :8080

# Check logs
journalctl -u trinity-dashboard -n 50
```

### Nginx 502 error
```bash
# Ensure dashboard is running
systemctl status trinity-dashboard

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Bot not running via cron
```bash
# Check cron logs
grep CRON /var/log/syslog

# Test runner manually
cd /opt/trinity/bot && /root/.local/bin/uv run python runner.py
```
