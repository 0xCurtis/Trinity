# Trinity - Content Automation Pipeline

Trinity is a content automation system that scrapes content from sources (Reddit, RedGifs) and posts it to destinations (Telegram, Twitter).

## Project Structure

```
trinity/
├── bot/                    # Main automation bot
│   ├── src/               # Source code
│   ├── pipelines/         # Pipeline configs
│   ├── tests/             # Tests
│   ├── logs/              # Bot logs
│   ├── history/           # Post history
│   ├── .last_run/         # Last run timestamps
│   └── runner.py          # Entry point
│
├── dashboard/             # Web dashboard
│   ├── app.py            # Flask app
│   ├── static/           # JS, CSS
│   └── templates/        # HTML
│
└── docs/                  # Documentation
```

## Local Development

### Bot
```bash
cd bot
uv sync
uv run python runner.py
```

### Dashboard
```bash
cd dashboard
uv sync
uv run gunicorn -w 4 -b 127.0.0.1:8080 app:app
# Or for dev: uv run python app.py
```

### Tests
```bash
cd bot
uv run pytest
```

---

## VPS Production Deployment

### 1. Upload Files

```bash
# On VPS
sudo mkdir -p /opt/trinity
cd /opt/trinity
# Upload bot/ and dashboard/ folders
```

### 2. Bot - Cron Job

```bash
# Add to crontab (crontab -e)
*/15 * * * * cd /opt/trinity/bot && /opt/trinity/bot/.venv/bin/python runner.py >> /var/log/trinity.log 2>&1
```

### 3. Dashboard - Systemd Service

Create `/etc/systemd/system/trinity-dashboard.service`:
```ini
[Unit]
Description=Trinity Dashboard

[Service]
Type=notify
WorkingDirectory=/opt/trinity/dashboard
ExecStart=/opt/trinity/dashboard/.venv/bin/gunicorn -w 4 -b 127.0.0.1:8080 app:app
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable trinity-dashboard
sudo systemctl start trinity-dashboard
```

### 4. Nginx with Password Protection

**Install htpasswd tool:**
```bash
sudo apt install apache2-utils
```

**Create password:**
```bash
sudo htpasswd -c /etc/nginx/.htpasswd admin
```

**Nginx config** (`/etc/nginx/sites-available/trinity`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        
        # Password protect
        auth_basic "Trinity Dashboard";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

**Enable:**
```bash
sudo ln -s /etc/nginx/sites-available/trinity /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Optional: HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Configuration

### Pipeline Config (`bot/pipelines/*.json`)

Each pipeline is defined by a JSON file:

### Config Reference

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique pipeline name |
| `description` | string | Human-readable description |
| `enabled` | boolean | Whether pipeline runs |
| `unique_posts` | boolean | Track history to avoid duplicates |
| `run_every_minutes` | integer | Minimum interval between runs |
| `source.task` | string | Python path to maker function |
| `source.*` | object | Maker-specific configuration |
| `middleware` | array | List of middleware task paths |
| `post.task` | string | Python path to poster function |
| `auth.*` | object | Authentication credentials |
| `telegram.chat_id` | string | Telegram channel ID (not secret) |

### Global Config (`pipelines/global.json`)

Controls notification settings:

```json
{
  "notifications": {
    "telegram": {
      "enabled": true,
      "token": "${TELEGRAM_BOT_TOKEN}",
      "chat_id": "-1003838413629"
    }
  }
}
```

## Adding New Modules

### Creating a New Maker (Source)

1. Create a new file in `src/maker/`:

```python
# src/maker/my_maker.py
from src.pipeline import MyPipeline
from src.retry import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=2.0)
def my_maker(pipeline: MyPipeline = None, args: dict = None) -> dict:
    # Fetch content from external source
    # args contains config from pipeline.json "source" section
    
    # Add media to pipeline
    pipeline.add_media("video", "/path/to/video.mp4")
    
    # Set post text
    args["string"] = "My post text"
    
    # Add to history for deduplication
    args.setdefault("_add_to_history", []).append("unique_content_id")
    
    return args
```

2. Reference it in your pipeline config:

```json
{
  "source": {
    "task": "src.maker.my_maker.my_maker",
    "my_maker": {
      "setting": "value"
    }
  }
}
```

### Creating a New Poster (Destination)

1. Create a new file in `src/poster/`:

```python
# src/poster/my_poster.py
from src.pipeline import MyPipeline
from src.retry import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=2.0)
def my_poster(pipeline: MyPipeline = None, args: dict = None):
    # Access config
    destination = args["my_poster"]["destination"]
    
    # Access auth
    api_key = args["auth"]["my_service"]["api_key"]
    
    # Access media and text
    media = args.get("media", [])
    text = args.get("string", "")
    
    # Post to external service
    # ...
    
    return args
```

2. Reference it in your pipeline config:

```json
{
  "post": {
    "task": "src.poster.my_poster.my_poster"
  },
  "auth": {
    "my_service": {
      "api_key": "${API_KEY}"
    }
  },
  "my_poster": {
    "destination": "value"
  }
}
```

### Creating Middleware

Middleware runs between the maker and poster:

```python
# src/middleware/my_middleware.py
from src.pipeline import MyPipeline

def my_middleware(pipeline: MyPipeline = None, args: dict = None) -> dict:
    # Process/transform content
    args["string"] = args["string"].upper()  # Example: uppercase text
    return args
```

Add to pipeline:

```json
{
  "middleware": ["src.middleware.my_middleware.my_middleware"]
}
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot API token |
| `TWITTER_API_KEY` | No | Twitter API key (for Twitter poster) |
| `TWITTER_API_KEY_SECRET` | No | Twitter API secret |
| `TWITTER_ACCESS_TOKEN` | No | Twitter access token |
| `TWITTER_ACCESS_TOKEN_SECRET` | No | Twitter access token secret |

## Using Secrets in Config

Use `${ENV_VAR_NAME}` syntax to reference environment variables:

```json
{
  "auth": {
    "telegram": {
      "token": "${TELEGRAM_BOT_TOKEN}"
    }
  }
}
```

This will be resolved at runtime. If the environment variable is not set, the pipeline will fail to load with an error.

## API Endpoints (Health Check)

| Endpoint | Description |
|----------|-------------|
| `/health` | Basic health check |
| `/status` | Pipeline status and uptime |

## Code Quality

```bash
cd bot
uv run ruff check .
uv run ruff check . --fix  # Auto-fix
```
