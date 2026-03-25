# notify-stars

GitHub stars tracker that runs daily via GitHub Actions. Detects new stargazers and sends them to a Kilo webhook for AI analysis + Discord notification.

## How it works

- GitHub Action runs daily at 06:00 UTC
- Fetches current stargazers for the tracked repo
- Compares against stored state to find new ones
- Sends new stargazers (with profile enrichment) to a webhook

## Configuration

| Env Variable | Description |
|---|---|
| `TRACKED_REPO` | Repo to track (default: `HDCharts/charts`) |
| `KILO_WEBHOOK_URL` | Webhook URL to POST new stargazers |
| `KILO_WEBHOOK_SECRET` | Secret value for the `x-notify-stars-key` header |

## Run locally

```bash
python scripts/track_stars.py        # Normal mode
python scripts/track_stars.py --test  # Test mode (forces webhook with recent stargazers)
```

## Data

Stargazer data is stored in `data/stargazers.json`.