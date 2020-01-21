import pytest

from delatore.outputs.telegram import BotRunner


@pytest.fixture
def bot(service, stop_event):
    return BotRunner(service, stop_event)
