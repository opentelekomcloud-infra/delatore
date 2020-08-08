import pytest

from delatore.outputs import AlertaRunner, BotRunner


@pytest.fixture
def bot(service, stop_event):
    return BotRunner(service, stop_event)


@pytest.fixture
def alerta(service, stop_event):
    return AlertaRunner(msg_service=service, stop_event=stop_event, send_heartbeats=False)
