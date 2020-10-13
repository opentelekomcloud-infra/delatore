import atexit
import logging

from apubsub import Service

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
CLG = logging.StreamHandler()
CLG.setLevel(logging.DEBUG)
LOGGER.addHandler(CLG)

SERVICE = Service()
SERVICE.start()
atexit.register(SERVICE.stop)
