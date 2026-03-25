# Kilo Webhook Prompt Template

Paste this into the prompt template field when configuring your webhook at `app.kilo.ai/cloud/webhooks/new`.

## Prerequisites

In the **Agent Environment Profile**, add:
- `DISCORD_WEBHOOK_URL` — your Discord channel webhook URL (as a secret)

## Template

````markdown
You received a GitHub stargazer webhook. Your ONLY job is to send a Discord notification.

## Step 1: Read the payload

The incoming data is:

```json
{{bodyJson}}
```

## Step 2: Analyze stargazers

For each user in `new_stargazers`, write ONE sentence about who they are based on their bio, repos, location, and followers.

## Step 3: Send to Discord

Run this EXACT command, replacing the placeholders with real values:

```
curl -s -X POST "$DISCORD_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Star Tracker",
    "embeds": [{
      "title": "Star Update: {{bodyJson.repo}}",
      "url": "https://github.com/{{bodyJson.repo}}",
      "color": 16766720,
      "fields": [
        {"name": "Total Stars", "value": "{{bodyJson.summary.total_stars}}", "inline": true},
        {"name": "New Stars", "value": "+{{bodyJson.summary.new_count}}", "inline": true},
        {"name": "Net Change", "value": "+{{bodyJson.summary.net_change}}", "inline": true},
        {"name": "New Stargazers", "value": "YOUR FORMATTED LIST HERE"},
        {"name": "Profile Insights", "value": "YOUR ONE-LINE INSIGHTS HERE"}
      ],
      "footer": {"text": "notify-stars"}
    }]
  }'
```

Replace:
- `YOUR FORMATTED LIST HERE` with each stargazer as a markdown link: `[username](profile_url)`, separated by ` | `
- `YOUR ONE-LINE INSIGHTS HERE` with your analysis, one line per user

## Rules

- Run the curl command. Do NOT just describe what you would do.
- Max 10 stargazers in the list. If more, add "and X more" at the end.
- If a stargazer has no bio, say "No public profile data" instead of guessing.
- If the event is `test_stargazers`, prefix the title with "[TEST] ".
- Your task is complete after running curl. Do nothing else.
````

## Available Variables

These variables are resolved by Kilo when the webhook fires:

| Variable | Description |
|----------|-------------|
| `{{body}}` | Raw request body |
| `{{bodyJson}}` | Parsed JSON body (pretty-printed) |
| `{{headers}}` | Request headers |
| `{{method}}` | HTTP method (GET, POST, etc.) |
| `{{path}}` | Request path after trigger ID |
| `{{query}}` | Query string parameters |
| `{{sourceIp}}` | Client IP address |
| `{{timestamp}}` | Request timestamp |

## Example Payload

The webhook receives a payload like this from `track_stars.py`:

```json
{
  "event": "new_stargazers",
  "repo": "HDCharts/charts",
  "timestamp": "2026-03-25T09:00:00Z",
  "summary": {
    "new_count": 3,
    "total_stars": 425,
    "net_change": 3
  },
  "new_stargazers": [
    {
      "username": "octocat",
      "starred_at": "2026-03-25T08:30:00Z",
      "profile_url": "https://github.com/octocat",
      "avatar_url": "https://avatars.githubusercontent.com/u/583231?v=4",
      "name": "The Octocat",
      "bio": "GitHub mascot",
      "company": "@github",
      "location": "San Francisco",
      "public_repos": 8,
      "followers": 10000,
      "following": 9
    }
  ]
}
```
