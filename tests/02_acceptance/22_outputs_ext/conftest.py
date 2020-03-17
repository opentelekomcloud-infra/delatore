import pytest

from delatore.outputs import AlertaRunner, BotRunner


@pytest.fixture
def bot(service, stop_event):
    return BotRunner(service, stop_event)


@pytest.fixture
def alerta(service, stop_event):
    return AlertaRunner(service, stop_event)
