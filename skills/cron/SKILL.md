---
name: cron
description: Manage Gateway cron jobs for scheduled tasks and reminders. Create, update, list, and remove recurring or one-time jobs.
metadata: {"clawdbot":{"emoji":"⏰","builtin":true}}
---

# Cron Job Management

The `cron` tool manages scheduled tasks in the Clawdbot Gateway. Use it to create recurring reminders, periodic status checks, or one-time scheduled messages.

## Core Concepts

### Session Targets

Cron jobs run in one of two contexts:

1. **main** - Sends events to the main agent session (like a user message)
2. **isolated** - Runs in a separate session, optionally posting results back to main

### Payload Types

The payload determines what happens when the job runs:

#### For Main Session (`sessionTarget: "main"`)
```json
{
  "kind": "systemEvent",
  "text": "Your reminder or task description"
}
```

#### For Isolated Session (`sessionTarget: "isolated"`)
```json
{
  "kind": "agentTurn",
  "message": "Task for the agent to perform",
  "model": "optional-model-override",
  "thinking": "low|medium|high",
  "deliver": true,
  "channel": "last"
}
```

### Schedule Types

Three ways to schedule jobs:

1. **Cron expression** - Unix-style cron syntax
   ```json
   { "kind": "cron", "expr": "0 9 * * *", "tz": "Asia/Shanghai" }
   ```

2. **Interval** - Repeat every N milliseconds
   ```json
   { "kind": "every", "everyMs": 3600000 }
   ```

3. **One-time** - Run once at a specific timestamp
   ```json
   { "kind": "at", "atMs": 1739347200000 }
   ```

## Common Patterns

### Daily Reminder (Main Session)

```json
{
  "action": "add",
  "job": {
    "name": "Morning Weather Check",
    "enabled": true,
    "schedule": {
      "kind": "cron",
      "expr": "0 9 * * *",
      "tz": "Asia/Shanghai"
    },
    "sessionTarget": "main",
    "wakeMode": "next-heartbeat",
    "payload": {
      "kind": "systemEvent",
      "text": "Check today's weather forecast for Hangzhou"
    }
  }
}
```

### Hourly Status Report (Isolated Session)

```json
{
  "action": "add",
  "job": {
    "name": "System Status Check",
    "enabled": true,
    "schedule": {
      "kind": "every",
      "everyMs": 3600000
    },
    "sessionTarget": "isolated",
    "wakeMode": "now",
    "payload": {
      "kind": "agentTurn",
      "message": "Check system status and report any issues",
      "deliver": true,
      "channel": "last"
    }
  }
}
```

### One-Time Reminder

```json
{
  "action": "add",
  "job": {
    "name": "Meeting Reminder",
    "enabled": true,
    "deleteAfterRun": true,
    "schedule": {
      "kind": "at",
      "atMs": 1739347200000
    },
    "sessionTarget": "main",
    "wakeMode": "now",
    "payload": {
      "kind": "systemEvent",
      "text": "Team meeting starts in 5 minutes"
    }
  }
}
```

### Weekly Report with Context

```json
{
  "action": "add",
  "contextMessages": 5,
  "job": {
    "name": "Weekly Summary",
    "enabled": true,
    "schedule": {
      "kind": "cron",
      "expr": "0 18 * * 5",
      "tz": "Asia/Shanghai"
    },
    "sessionTarget": "main",
    "wakeMode": "next-heartbeat",
    "payload": {
      "kind": "systemEvent",
      "text": "Generate a summary of this week's conversations"
    }
  }
}
```

## Tool Actions

### status
Get cron service status and job counts.

```json
{ "action": "status" }
```

### list
List all cron jobs (optionally include disabled ones).

```json
{
  "action": "list",
  "includeDisabled": true
}
```

### add
Create a new cron job.

```json
{
  "action": "add",
  "job": { /* job spec */ },
  "contextMessages": 5  // Optional: include recent chat context (0-10)
}
```

### update
Modify an existing job.

```json
{
  "action": "update",
  "jobId": "job-id-here",
  "patch": {
    "enabled": false,
    "schedule": { "kind": "cron", "expr": "0 10 * * *" }
  }
}
```

### remove
Delete a job.

```json
{
  "action": "remove",
  "jobId": "job-id-here"
}
```

### run
Manually trigger a job (ignores schedule).

```json
{
  "action": "run",
  "jobId": "job-id-here",
  "runMode": "force"  // "force" (default) = run immediately, "due" = only run if due
}
```

### runs
Get execution history for a job.

```json
{
  "action": "runs",
  "jobId": "job-id-here",
  "limit": 10
}
```

### wake
Send a wake event to the main session (not a cron job).

```json
{
  "action": "wake",
  "text": "Check for new messages",
  "mode": "next-heartbeat"  // or "now"
}
```

## Cron Expression Examples

```
0 9 * * *        # Daily at 9:00 AM
0 */2 * * *      # Every 2 hours
30 8 * * 1-5     # Weekdays at 8:30 AM
0 0 1 * *        # First day of each month at midnight
0 12 * * 0       # Sundays at noon
*/15 * * * *     # Every 15 minutes
```

## Common Mistakes to Avoid

### ❌ Wrong: Mixing schedule and payload properties
```json
{
  "payload": {
    "kind": "agentTurn",
    "atMs": 123456789,      // This belongs in schedule!
    "command": "do something"  // No such property
  }
}
```

### ✅ Correct: Separate schedule and payload
```json
{
  "schedule": {
    "kind": "at",
    "atMs": 1739347200000
  },
  "payload": {
    "kind": "agentTurn",
    "message": "do something"
  }
}
```

### ❌ Wrong: Using "text" for isolated sessions
```json
{
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "text": "task description"  // Should be "message"
  }
}
```

### ✅ Correct: Use "message" for agentTurn
```json
{
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "task description"
  }
}
```

### ❌ Wrong: Mismatched sessionTarget and payload kind
```json
{
  "sessionTarget": "main",
  "payload": {
    "kind": "agentTurn",  // Main requires systemEvent!
    "message": "..."
  }
}
```

### ✅ Correct: Match sessionTarget with payload kind
```json
{
  "sessionTarget": "main",
  "payload": {
    "kind": "systemEvent",
    "text": "..."
  }
}
```

## Tips

1. **Use contextMessages** - When creating reminders in main session, set `contextMessages: 3-5` to include recent conversation context
2. **Timezone matters** - Always specify `tz` for cron expressions to avoid confusion
3. **Test with "run"** - Use the `run` action to test jobs immediately without waiting for the schedule
4. **One-time jobs** - Set `deleteAfterRun: true` for one-time reminders to auto-cleanup
5. **Isolated for heavy tasks** - Use isolated sessions for long-running or resource-intensive tasks
6. **Wake mode** - Use `"now"` for urgent tasks, `"next-heartbeat"` for normal priority

## Troubleshooting

### Job not running
- Check `enabled: true`
- Verify cron expression with online tools
- Check timezone setting
- Use `action: "runs"` to see execution history

### Validation errors
- Ensure `sessionTarget` matches `payload.kind`:
  - `main` → `systemEvent`
  - `isolated` → `agentTurn`
- Check for typos in property names
- Don't mix schedule properties into payload

### Jobs running but no output
- For isolated jobs, set `deliver: true` to see results
- Check `channel` setting (use `"last"` for most recent channel)
- Verify the agent has permissions for the target channel

## Related

- CLI: `clawdbot cron list|add|update|remove|run`
- Config: `~/.clawdbot/cron.json`
- Logs: Check gateway logs for execution details
