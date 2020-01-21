# Delatore
[![Build Status](https://travis-ci.org/opentelekomcloud-infra/delatore.svg?branch=master)](https://travis-ci.org/opentelekomcloud-infra/delatore)
[![codecov](https://codecov.io/gh/opentelekomcloud-infra/delatore/branch/master/graph/badge.svg)](https://codecov.io/gh/opentelekomcloud-infra/delatore)
[![PyPI version](https://img.shields.io/pypi/v/delatore.svg)](https://pypi.org/project/delatore/)
![GitHub](https://img.shields.io/github/license/opentelekomcloud-infra/delatore)

Monitor and report status of customer service monitoring scenarios

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
