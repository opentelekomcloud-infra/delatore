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
