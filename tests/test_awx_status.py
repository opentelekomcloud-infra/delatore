from delatore.awx_status import AwxApiClient
from delatore.awx_status import TemplateStatus
import os
import time
from typing import Union, Dict, NamedTuple, List
import requests


def test_get_data():
    client = AwxApiClient()
    message = client.create_message_status(template = "Scenario 1.5")
    print(message)
    print(5)

