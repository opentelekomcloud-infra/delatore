Delatore
========

| |Build Status|
| |Zuul|
| |codecov|
| |PyPI version|
| |GitHub|

Monitor and report status of customer service monitoring scenarios

Bot commands
------------

Telegram bot accepts following commands:

``/status``
~~~~~~~~~~~

Bot reply to the message with last status(-es) retrieved from given
source

Status has following syntax:

``/status <source> [detailed_source] [history_depth]``

If some argument contains spaces, it should be surrounded by quotes,
either ``'...'`` or ``"..."``

AWX Source
^^^^^^^^^^

Status command for AWX source has following syntax:

``/status awx [template_name] [history_depth]``

Examples:

-  ``/status awx`` — return last job status for all *scenarios*
-  ``/status awx 'Buld test host'`` — return last job status for AWX
   template which called 'Buld test host'
-  ``/status awx 'Scenario 1.5' 3`` — return status of last 3 jobs for
   AWX template which called ``Scenario 1.5``

.. |Build Status| image:: https://travis-ci.org/opentelekomcloud-infra/delatore.svg?branch=master
   :target: https://travis-ci.org/opentelekomcloud-infra/delatore
.. |codecov| image:: https://codecov.io/gh/opentelekomcloud-infra/delatore/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/opentelekomcloud-infra/delatore
.. |PyPI version| image:: https://img.shields.io/pypi/v/delatore.svg
   :target: https://pypi.org/project/delatore/
.. |GitHub| image:: https://img.shields.io/github/license/opentelekomcloud-infra/delatore
.. |Zuul| image:: https://zuul-ci.org/gated.svg
