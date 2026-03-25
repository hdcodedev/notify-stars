# Kilo Webhook Prompt Template

Paste this into the prompt template field when configuring your webhook at `app.kilo.ai/cloud/webhooks/new`.

## Prerequisites

In the **Agent Environment Profile**, add:
- `DISCORD_WEBHOOK_URL` — your Discord channel webhook URL (as a secret)

## Template

````markdown
## Context

You have received a GitHub stargazer tracking event. The incoming webhook payload is:

```json
{{bodyJson}}
```

## Task

1. Read the `new_stargazers` array from the payload above.

2. For each stargazer, review their profile data (bio, location, public_repos, followers, etc.) and write a one-line insight about who they are and what they likely work on.

3. Compose a Discord notification using the `DISCORD_WEBHOOK_URL` environment variable. POST to it with the following structure:

```json
{
  "username": "Star Tracker",
  "embeds": [{
    "title": "Star Update: {{bodyJson.repo}}",
    "url": "https://github.com/{{bodyJson.repo}}",
    "color": 16766720,
    "fields": [
      { "name": "Total Stars", "value": "{{bodyJson.summary.total_stars}}", "inline": true },
      { "name": "New Stars", "value": "+{{bodyJson.summary.new_count}}", "inline": true },
      { "name": "Net Change", "value": "+{{bodyJson.summary.net_change}}", "inline": true },
      { "name": "New Stargazers", "value": "<your formatted list here>" },
      { "name": "Profile Insights", "value": "<your one-line insights here>" }
    ],
    "footer": { "text": "notify-stars" }
  }]
}
```

## Rules

- Max 10 stargazers listed in the embed (Discord limits). If more, add "and X more" at the end.
- Keep insights to one sentence per user. Be specific — mention their tech stack, domain, or notable repos if visible.
- If a stargazer has no bio or minimal data, say "No public profile data" instead of guessing.
- Do NOT include any other output. Only POST the Discord webhook.
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
    "total_stars": 142,
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
