# Kilo Webhook Prompt Template

Paste this into the prompt template field when configuring your webhook at `app.kilo.ai/cloud/webhooks/new`.

## Prerequisites

In the **Agent Environment Profile**, add:
- `DISCORD_WEBHOOK_URL` — your Discord channel webhook URL (as a secret)

## Template

````markdown
You received a webhook with new GitHub stargazers. Send a Discord notification.

## Data

```json
{{bodyJson}}
```

## Steps

1. For each user in `new_stargazers`, write one sentence about who they are based on their bio, repos, location, and followers.

2. Run this curl command, replacing YOUR VALUES:

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
        {"name": "New Stargazers", "value": "LIST OF USERS AS MARKDOWN LINKS"},
        {"name": "Profile Insights", "value": "ONE LINE PER USER"}
      ],
      "footer": {"text": "notify-stars"}
    }]
  }'
```

## Rules

- Run the curl command. Do NOT just describe what you would do.
- Max 10 stargazers. If more, add "and X more".
- No bio? Say "No public profile data".
- Task is complete after running curl.
````
