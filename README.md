# Delatore
Monitor and report status of customer service monitoring scenarios

## State
Given project is just a concept

## Architecture

### Gather events (CSM)
1. AWX (web hooks)
1. Test scripts (direct http API calls)
1. Telegraf (http output)

### Process reports (server)
1. Unify input (telegraf reports in fixed format)
1. Running on `test_host`, created by [kapellmeister](https://github.com/opentelekomcloud-infra/csm-kapellmeister)
1. Running in dedicated container
1. No storage

### Report (Telegram)
1. Configured telegram chanel
1. Direct messages to configured users
1. Control target user/channel by severity map

## Bot commands

Telegram bot accepts following commands:

### `/status`
Bot reply to the message with last status(-es) retrieved from given source

Status has following syntax:

`/status <source> [detailed_source] [history_depth]`

If some argument contains spaces, it should be surrounded by quotes, either `'...'` or `"..."`

#### AWX Source

Status command for AWX source has following syntax:

`/status awx [template_name] [history_depth]`

Examples:
 - `/status awx` — return last job status for all _scenarios_
 - `/status awx 'Buld test host'` — return last job status for AWX template which called 'Buld test host'
 - `/status awx 'Scenario 1.5' 3` — return status of last 3 jobs for AWX template which called  `Scenario 1.5`
