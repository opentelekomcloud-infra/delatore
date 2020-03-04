*Delatore Bot help*

Delatore monitors and reports status of Customer Service Monitoring

Delatore works in two modes:  passive mode automatically reporting status changes to  `OTC CSM notifications` channel,
and active mode responding to `/status` command

*Status command:*

Status command retrieves status of given source

`/status` command has following syntax:
`/status <source> [template_name]`

Implemented sources:
1\. `awx` — get last job state for AWX templates

Examples:
`/status awx` — return last job status for all __scenarios__
`/status awx "Scenario 1.5"` — return last status for Scenario 1\.5
