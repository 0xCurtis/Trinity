# Trinity - Content Automation Pipeline

Trinity is a content automation system that scrapes content from sources (Reddit, RedGifs) and posts it to destinations (Telegram, Twitter).

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Maker    │ ──► │  Middleware │ ──► │   Poster    │
│  (Source)   │     │ (Processing)│     │ (Destination)│
└─────────────┘     └─────────────┘     └─────────────┘
```

- **Makers**: Fetch content from external sources (Reddit, RedGifs)
- **Middlewares**: Process content between fetch and post (optional)
- **Posters**: Send content to destinations (Telegram, Twitter)

## Quick Start

### 1. Environment Setup

Copy the example environment file and fill in your secrets:

```bash
cp .env.example .env
```

Edit `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

**Note:** Telegram channel IDs can be kept raw in pipeline configs - only the bot token is secret.

### 2. Run the Pipeline

```bash
# Run manually
python runner.py

# Or use Docker
docker-compose up
```

## Configuration

### Pipeline Config (`pipelines/*.json`)

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

## Running with Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

The Docker container expects:
- `TELEGRAM_BOT_TOKEN` environment variable (set in docker-compose.yml or .env)

## API Endpoints (Health Check)

When using Flask-based health checks:

| Endpoint | Description |
|----------|-------------|
| `/health` | Basic health check |
| `/status` | Pipeline status and uptime |

## Development

### Running Tests

```bash
uv sync --dev
uv run pytest
```

### Code Quality

```bash
uv run ruff check .
uv run ruff check . --fix  # Auto-fix
```

## File Structure

```
Trinity/
├── runner.py              # Main entry point
├── src/
│   ├── config.py          # Configuration & env var resolution
│   ├── pipeline.py        # Core pipeline execution
│   ├── pipeline_store.py  # Pipeline management
│   ├── retry.py          # Retry decorator with backoff
│   ├── health.py         # Health check server
│   ├── logging_config.py # Logging setup
│   ├── maker/            # Content sources
│   │   ├── reddit_maker.py
│   │   ├── redgifs_maker.py
│   │   └── string_maker.py
│   ├── middleware/       # Processing middlewares
│   │   └── fake_delay.py
│   └── poster/          # Output destinations
│       ├── telegram_poster.py
│       ├── twitter_post.py
│       └── console_poster.py
├── pipelines/            # Pipeline configurations
│   ├── global.json      # Global settings
│   └── *.json          # Individual pipelines
├── tests/               # Test files
├── Dockerfile
└── docker-compose.yml
```
